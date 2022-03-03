# -*- coding: utf-8 -*-

import json
import requests
from datetime import datetime
from senaite.referral import logger
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.utils import get_lab_code
from senaite.referral.utils import is_valid_url

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest


def after_dispatch(shipment):
    """ Event fired after transition "dispatch" is triggered
    """
    notify_outbound_shipment(shipment)


def notify_outbound_shipment(shipment):
    lab_code = get_lab_code()
    if not lab_code:
        # No valid code set for the current lab. Do nothing
        msg = "No valid code set for the current laboratory"
        logger.error(msg)
        return msg

    lab = shipment.get_reference_laboratory()
    if api.is_uid(lab):
        lab = api.get_object(lab)

    if not IExternalLaboratory.providedBy(lab):
        # Not an external laboratory!
        msg = "Shipment does not belong to an external lab"
        logger.error(msg)
        return msg

    if not lab.get_reference():
        # External lab not set as reference lab
        msg = "External lab is not set as a reference laboratory"
        logger.error(msg)
        return msg

    url = lab.get_reference_url()
    if not is_valid_url(url):
        # External Lab URL not valid
        msg = "External lab's URL is not valid: {}".format(url)
        logger.error(msg)
        return msg

    username = lab.get_reference_username()
    password = lab.get_reference_password()
    if not all([username, password]):
        # Empty username or password
        msg = "No valid credentials"
        logger.error(msg)
        return msg

    dispatcher = ShipmentDispatcher(url)
    if not dispatcher.auth(username, password):
        # Unable to authenticate
        msg = "Cannot authenticate against reference laboratory"
        logger.error(msg)
        return msg

    # Send the shipment via post
    try:
        dispatcher.send(shipment)
    except Exception as e:
        logger.error(str(e))
        response = json.dumps({"success": False, "message": str(e)})
        response_text = "[500] {}".format(response)
        shipment.set_dispatch_notification_response(response_text)

    return None


class ShipmentDispatcher(object):

    session = None

    def __init__(self, host):
        self.host = host

    def send(self, shipment, timeout=5):
        dispatched = shipment.get_dispatched_datetime() or datetime.now()
        samples = map(self.get_sample_info, shipment.get_samples())
        payload = {
            "consumer": "senaite.referral.inbound_shipment",
            "lab_code": get_lab_code(),
            "shipment_id": shipment.get_shipment_id(),
            "dispatched": dispatched.strftime("%Y-%m-%d %H:%M:%S"),
            "samples": filter(None, samples),
        }

        now = datetime.now()
        shipment.set_dispatch_notification_datetime(now)
        shipment.set_dispatch_notification_payload(payload)

        response = self.post("push", payload, timeout)
        response_text = "[{}] {}".format(response.status_code, response.text)
        shipment.set_dispatch_notification_response(response_text)

    def get_sample_info(self, sample_brain_uid):
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

    def get(self, url, payload=None):
        url = self.resolve_api_slug(url)
        response = self.session.get(url, params=payload)
        logger.info("[GET] {}".format(response.url))
        if response.status_code != 200:
            logger.error(response.status_code)
        return response

    def post(self, url, payload, timeout):
        url = self.resolve_api_slug(url)
        logger.info("[POST] {}".format(url))
        response = self.session.post(url, json=payload, timeout=timeout)
        return response

    def auth(self, user, password):
        if not is_valid_url(self.host):
            return False
        self.session = requests.Session()
        self.session.auth = (user, password)
        r = self.get("auth")
        return r.status_code == 200

    def resolve_api_slug(self, url):
        if self.host not in url:
            api_slug = "@@API/senaite/v1"
            url = "{}/{}/{}".format(self.host, api_slug, url)
        return url
