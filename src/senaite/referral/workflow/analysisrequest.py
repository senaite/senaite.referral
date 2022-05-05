# -*- coding: utf-8 -*-

import json

from senaite.referral import check_installed
from senaite.referral import logger
from senaite.referral.remotesession import RemoteSession
from senaite.referral.utils import get_field_value
from senaite.referral.utils import get_lab_code
from senaite.referral.utils import is_valid_url
from senaite.referral.workflow import revoke_analyses_permissions
from senaite.referral.workflow import ship_sample

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.utils import format_supsub
from bika.lims.utils.analysis import format_uncertainty
from bika.lims.workflow import doActionFor


@check_installed(None)
def AfterTransitionEventHandler(sample, event): # noqa lowercase
    """Actions to be done just after a transition for a sample takes place
    """
    if not event.transition:
        return

    if event.transition.id == "no_sampling_workflow":
        after_no_sampling_workflow(sample)

    if event.transition.id == "ship":
        after_ship(sample)

    if event.transition.id == "verify":
        after_verify(sample)


def after_no_sampling_workflow(sample):
    """Automatically receive and ship samples for which an outbound shipment
    has been specified on creation (Add sample form)
    """
    shipment = get_field_value(sample, "OutboundShipment")
    if not shipment:
        return

    # Transition the sample to received + shipped status
    doActionFor(sample, "receive")
    ship_sample(sample, shipment)


def after_ship(sample):
    """Automatically revoke edit permissions for analyses from this sample
    """
    revoke_analyses_permissions(sample)


def after_verify(sample):
    """Notify the referring laboratory about this sample
    """
    shipment = get_field_value(sample, "InboundShipment")
    if not shipment:
        return

    # Notify the referring laboratory
    lab = shipment.getReferringLaboratory()
    url = lab and lab.getUrl() or ""
    if not is_valid_url(url):
        return

    username = lab.getUsername()
    password = lab.getPassword()
    if not all([username, password]):
        return

    notifier = SampleNotifier(url)
    if not notifier.auth(username, password):
        # Unable to authenticate
        msg = "Cannot authenticate with '{}': {}".format(username, url)
        logger.error(msg)
        return msg

    # Send sample information via post
    notifier.send(sample)


class SampleNotifier(RemoteSession):

    def send(self, sample, timeout=5):
        payload = {
            "consumer": "senaite.referral.outbound_sample",
            "lab_code": get_lab_code(),
            "sample": self.get_sample_info(sample),
        }
        response = self.post(sample, "push", payload, timeout)
        return response

    def get_sample_info(self, sample):
        # Extract the shipment the sample belongs to
        shipment = get_field_value(sample, "InboundShipment")

        # We are only interested in analyses results. Referring laboratory does
        # not care about the information set at sample level
        valid = ["verified", "published"]
        analyses = sample.getAnalyses(full_objects=True)
        analyses = filter(lambda a: api.get_review_status(a) in valid, analyses)
        analyses = [self.get_analysis_info(analysis) for analysis in analyses]
        return {
            "id": api.get_id(sample),
            "referring_id": sample.getClientSampleID(),
            "shipment_id": shipment.get_shipment_id(),
            "analyses": analyses,
        }

    def get_analysis_info(self, analysis):
        result_date = analysis.getResultCaptureDate()
        verification_date = analysis.getDateVerified()
        return {
            "keyword": analysis.getKeyword(),
            "result": analysis.getResult(),
            "result_options": analysis.getResultOptions(),
            "interim_fields": analysis.getInterimFields(),
            "formatted_result": self.get_formatted_result(analysis) or "NA",
            "result_date": result_date.strftime("%Y-%m-%d"),
            "verification_date": verification_date.strftime("%Y-%m-%d"),
        }

    def get_formatted_result(self, analysis):
        """Returns the result of the analysis formatted as to be stored in
        the referring laboratory
        """
        # Result
        result = analysis.getFormattedResult()

        # Uncertainty
        uncertainty = format_uncertainty(analysis, analysis.getResult())
        uncertainty = uncertainty and "[+-{}]".format(uncertainty) or ""

        # Unit
        unit = analysis.getUnit()
        unit = unit and format_supsub(unit) or ""

        # Return the whole thing joined as an string
        values = filter(None, [result, unit, uncertainty])
        return " ".join(values)
