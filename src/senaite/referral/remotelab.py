# -*- coding: utf-8 -*-

import json

from datetime import datetime
from requests.auth import HTTPBasicAuth
from senaite.core.supermodel import SuperModel
from senaite.referral import logger
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.remotesession import RemoteSession
from senaite.referral.utils import get_lab_code
from senaite.referral.utils import is_valid_url

from bika.lims.utils import format_supsub
from bika.lims.utils.analysis import format_uncertainty
from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from remotesession import RemoteSession


def get_remote_connection(laboratory):
    """Returns a RemoteLab object for the laboratory passed-in if a remote
    connection is supported. Returns None otherwise
    """
    if not IExternalLaboratory.providedBy(laboratory):
        return None

    url = laboratory.getUrl()
    if not is_valid_url(url):
        return None

    username = laboratory.getUsername()
    password = laboratory.getPassword()
    if not all([username, password]):
        return None

    return RemoteLab(laboratory)


def get_object_info(obj):
    """Returns a dict representation of the object passed-in, suitable for
    being injected into a POST payload
    """
    if not api.is_object(obj):
        n_obj = api.get_object(obj, default=None)
        if not n_obj:
            raise ValueError("Type not supported: {}".format(repr(obj)))
        return get_object_info(n_obj)

    # Basic information
    basic_info = {
        "id": api.get_id(obj),
        "uid": api.get_uid(obj),
        "portal_type": api.get_portal_type(obj),
    }

    # Find out if there is a specific adapter converter
    # adapter = queryAdapter(obj, IReferralObjectInfo)
    # if adapter:
    #     return adapter.to_dict()

    # Rely on supermodel
    sm = SuperModel(obj)
    info = sm.to_dict()
    basic_info.update(info)
    return basic_info


class RemoteLab(object):

    _session = None

    def __init__(self, external_laboratory):
        self.laboratory = external_laboratory

    @property
    def laboratory_url(self):
        return self.laboratory.getUrl()

    @property
    def session(self):
        if self._session is None:
            username = self.laboratory.getUsername()
            password = self.laboratory.getPassword()
            auth = HTTPBasicAuth(username, password)
            self._session = RemoteSession(self.laboratory_url, auth)
        return self._session

    def do_action(self, obj, action, timeout=5):
        """Sends a POST request to the remote laboratory for the object and
        action passed-in
        """
        if not isinstance(obj, (list, tuple, set)):
            obj = [obj]
        items = [get_object_info(obj) for obj in obj]
        payload = {
            "consumer": "senaite.referral.consumer",
            "lab_code": get_lab_code(),
            "action": action,
            "items": items,
        }
        return self.session.post("push", payload, timeout=timeout)

    def create_inbound_shipment(self, shipment, timeout=5):
        """Creates an Inbound Shipment counterpart object for the shipment
        passed-in in the remote laboratory
        """

        def get_sample_info(sample_brain_uid):
            sample = api.get_object(sample_brain_uid)
            if not IAnalysisRequest.providedBy(sample):
                return None

            sample_type = sample.getSampleType()
            date_sampled = sample.getDateSampled()

            state = ["registered", "unassigned", "assigned"]
            analyses = sample.getAnalyses(full_objects=False, review_state=state)
            return {
                "id": api.get_id(sample),
                "sample_type": api.get_title(sample_type),
                "date_sampled": date_sampled.strftime("%Y-%m-%d"),
                "analyses": map(lambda an: an.getKeyword, analyses)
            }

        dispatched = shipment.get_dispatched_datetime()
        samples = map(get_sample_info, shipment.get_samples())
        payload = {
            "consumer": "senaite.referral.inbound_shipment",
            "lab_code": get_lab_code(),
            "shipment_id": api.get_id(shipment),
            "dispatched": dispatched.strftime("%Y-%m-%d %H:%M:%S"),
            "samples": filter(None, samples),
        }

        now = datetime.now()
        shipment.set_dispatch_notification_datetime(now)
        shipment.set_dispatch_notification_payload(payload)

        try:
            response = self.session.post("push", payload, timeout=timeout)
            response_text = "[{}] {}".format(response.status_code, response.text)
            shipment.set_dispatch_notification_response(response_text)
        except Exception as e:
            logger.error(str(e))
            response = json.dumps({"success": False, "message": str(e)})
            response_text = "[500] {}".format(response)
            shipment.set_dispatch_notification_response(response_text)

    def update_analyses(self, sample, timeout=5):
        """Update the analyses from the remote laboratory with the information
        provided with the sample passed-in
        """

        def get_sample_info(sample):
            # Extract the shipment the sample belongs to
            shipment = sample.getInboundShipment()

            # We are only interested in analyses results. Referring laboratory
            # does not care about the information set at sample level
            valid = ["verified", "published"]
            analyses = sample.getAnalyses(full_objects=True)
            analyses = filter(lambda a: api.get_review_status(a) in valid, analyses)
            analyses = [get_analysis_info(analysis) for analysis in analyses]
            return {
                "id": api.get_id(sample),
                "referring_id": sample.getClientSampleID(),
                "shipment_id": shipment.get_shipment_id(),
                "analyses": analyses,
            }

        def get_analysis_info(analysis):
            result_date = analysis.getResultCaptureDate()
            verification_date = analysis.getDateVerified()
            return {
                "keyword": analysis.getKeyword(),
                "result": analysis.getResult(),
                "result_options": analysis.getResultOptions(),
                "interim_fields": analysis.getInterimFields(),
                "formatted_result": get_formatted_result(analysis) or "NA",
                "result_date": result_date.strftime("%Y-%m-%d"),
                "verification_date": verification_date.strftime("%Y-%m-%d"),
            }

        def get_formatted_result(analysis):
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

        payload = {
            "consumer": "senaite.referral.outbound_sample",
            "lab_code": get_lab_code(),
            "sample": get_sample_info(sample),
        }

        try:
            self.session.post("push", payload, timeout=timeout)
        except Exception as e:
            logger.error(str(e))

