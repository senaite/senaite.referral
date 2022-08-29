# -*- coding: utf-8 -*-

from remotesession import RemoteSession
from requests.auth import HTTPBasicAuth
from senaite.core.supermodel import SuperModel
from senaite.referral import logger
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.notifications import get_post_base_info
from senaite.referral.notifications import save_post
from senaite.referral.utils import get_lab_code
from senaite.referral.utils import get_user_info
from senaite.referral.utils import is_valid_url

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IVerified
from bika.lims.utils import format_supsub
from bika.lims.utils.analysis import format_uncertainty


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


def skip_post_action_for(obj):
    """Returns whether POST actions must be skipped for the given object to
    prevent circular calls between referring and referer labs
    """
    uid = api.get_uid(obj)
    uids = api.get_request().get("skip_post_action_uids", [])
    return uid in uids


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

    def get_payload_base_info(self):
        return {
            "consumer": "senaite.referral.consumer",
            "remote_lab": api.get_uid(self.laboratory),
            "lab_code": get_lab_code(),
        }

    def do_action(self, obj, action, timeout=5):
        """Sends a POST request to the remote laboratory for the object and
        action passed-in
        """
        if not isinstance(obj, (list, tuple, set)):
            obj = [obj]

        # Skip objects that are being transitioned by the remote lab via PUSH
        # in current request already. This is to prevent circular POSTs
        obj = filter(lambda ob: not skip_post_action_for(ob), obj)
        if not obj:
            return

        items = [get_object_info(obj) for obj in obj]
        payload = {
            "consumer": "senaite.referral.consumer",
            "action": action,
            "items": items,
        }
        self.notify(obj, payload, timeout=timeout)

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

            state = ["registered", "unassigned", "assigned", "referred"]
            analyses = sample.getAnalyses(full_objects=False, review_state=state)
            return {
                "id": api.get_id(sample),
                "sample_type": api.get_title(sample_type),
                "date_sampled": date_sampled.strftime("%Y-%m-%d"),
                "priority": sample.getPriority(),
                "analyses": map(lambda an: an.getKeyword, analyses)
            }

        dispatched = shipment.getDispatchedDateTime()
        samples = map(get_sample_info, shipment.getSamples())
        payload = {
            "consumer": "senaite.referral.inbound_shipment",
            "shipment_id": api.get_id(shipment),
            "dispatched": dispatched.strftime("%Y-%m-%d %H:%M:%S"),
            "samples": filter(None, samples),
        }
        self.notify(shipment, payload, timeout=timeout)

    def update_analyses(self, sample, timeout=5):
        """Update the analyses from the remote laboratory with the information
        provided with the sample passed-in
        """

        def get_valid_analyses(sample):
            analyses = []
            valid = ["verified", "published"]
            for analysis in sample.getAnalyses(full_objects=True):

                # We only consider Verified analyses
                if not IVerified.providedBy(analysis):
                    continue

                # Skip invalid and others
                if api.get_review_status(analysis) not in valid:
                    continue

                # We only consider "final" analyses
                if analysis.getRetest():
                    continue

                analyses.append(analysis)

            # Sort them by modification date
            analyses = sorted(analyses, key=api.get_modification_date)
            return analyses

        def get_sample_info(sample):
            # Extract the shipment the sample belongs to
            shipment = sample.getInboundShipment()

            # We are only interested in analyses results. Referring laboratory
            # does not care about the information set at sample level
            analyses = get_valid_analyses(sample)
            analyses = [get_analysis_info(analysis) for analysis in analyses]
            return {
                "id": api.get_id(sample),
                "referring_id": sample.getClientSampleID(),
                "shipment_id": shipment.getShipmentID(),
                "analyses": analyses,
            }

        def get_analysis_info(analysis):
            result_date = analysis.getResultCaptureDate()
            return {
                "keyword": analysis.getKeyword(),
                "result": analysis.getResult(),
                "result_options": analysis.getResultOptions(),
                "interim_fields": analysis.getInterimFields(),
                "formatted_result": get_formatted_result(analysis) or "NA",
                "instrument": get_instrument(analysis) or "",
                "method": get_method(analysis) or "",
                "result_date": result_date.strftime("%Y-%m-%d"),
                "verifiers": get_verifiers_info(analysis),
                "analysts": get_analysts_info(analysis),
            }

        def get_analysts_info(analysis):
            """Returns a list of dicts each one representing an analyst
            """
            analyst = analysis.getAnalyst()
            if not analyst:
                return []

            analyst_info = get_user_info(analyst)
            # Update with current's lab code
            lab_code = get_lab_code()
            analyst_info.update({"lab_code": lab_code})
            return [analyst_info]

        def get_verifiers_info(analysis):
            """Returns a list of dicts each one representing a verifier
            """
            verifiers = analysis.getVerificators() or []
            verifiers_info = [get_user_info(verifier) for verifier in verifiers]
            verifiers_info = filter(None, verifiers_info)

            # Update with current's lab code
            lab_code = get_lab_code()
            for verifier in verifiers_info:
                verifier.update({"lab_code": lab_code})
            return verifiers_info

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

        def get_instrument(analysis):
            instrument = analysis.getInstrument()
            if instrument:
                return api.get_title(instrument)
            return None

        def get_method(analysis):
            method = analysis.getMethod()
            if method:
                return api.get_title(method)
            return None

        payload = {
            "consumer": "senaite.referral.outbound_sample",
            "lab_code": get_lab_code(),
            "sample": get_sample_info(sample),
        }
        self.notify(sample, payload, timeout=timeout)

    def notify(self, obj, payload, timeout=5):
        """Sends a post for the given payload and stores the response to the
        object passed-in
        """
        # Be sure we have the basics in place in the payload
        data = self.get_payload_base_info()
        data.update(payload)

        # Do the POST request and store the response for later use if required
        try:
            response = self.session.post("push", data, timeout=timeout)
        except Exception as e:
            # Dummy response
            response = get_post_base_info()
            response.update({
                "url": self.session.get_api_url("push"),
                "status": 500,
                "reason": type(e).__name__,
                "message": str(e),
                "success": False,
            })
            logger.error(str(e))

        # Store the response, so we can keep track of the POSTs made for this
        # given object and retry if necessary
        save_post(obj, data, response)
