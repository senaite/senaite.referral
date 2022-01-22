# -*- coding: utf-8 -*-

import json
import six
from bika.lims import api
from senaite.jsonapi.request import is_json_deserializable
from senaite.referral import utils
from senaite.jsonapi.interfaces import IPushConsumer
from zope.interface import implementer
from Products.ATContentTypes.utils import DT2dt


@implementer(IPushConsumer)
class InboundShipmentConsumer(object):
    """Adapter that handles push requests for name
    senaite.referral.inbound_shipment
    """

    def __init__(self, data):
        self.data = data

    def process(self):
        """Processes the data sent via POST. Imports the inbound shipment by
        creating the necessary samples and analyses
        """
        # Sanitize the data first
        self.sanitize(self.data)

        # Validate the data passed-in
        required_fields = ["lab_code", "shipment_id", "dispatched", "samples"]
        self.validate(self.data, required=required_fields)

        # Ensure the samples passed-in are compliant
        required_fields = ["id", ]
        sample_records = self.data.get("samples")
        if isinstance(sample_records, six.string_types):
            if not is_json_deserializable(sample_records):
                raise ValueError("Value for 'samples' is not a valid JSON")
            sample_records = json.loads(sample_records)
        self.validate(sample_records, required=required_fields)

        dispatched = self.data.get("dispatched")
        dispatched_date = api.to_date(dispatched)
        if not dispatched_date:
            raise ValueError("Non-valid datetime format: {}".format(dispatched))

        # Get the lab for the given code
        lab_code = self.data.get("lab_code")
        lab = self.get_external_laboratory(lab_code)

        # Check if a shipment with the given id and lab exists already
        # XXX Improve this with shipments own catalog
        shipment_id = self.data.get("shipment_id")
        for shipment in lab.objectValues("InboundSamplesShipment"):
            if shipment.get_shipment_id() == shipment_id:
                raise ValueError("Inbound shipment already exists: {}"
                                 .format(shipment_id))

        # Create the inbound shipment
        comments = self.data.get("comments")
        values = {
            "shipment_id": str(shipment_id),
            "referring_laboratory": api.get_uid(lab),
            "comments": str(comments),
            "dispatched_datetime": DT2dt(dispatched_date),
            "samples": sample_records,
        }
        shipment = api.create(lab, "InboundSampleShipment", **values)
        if not api.is_object(shipment):
            raise ValueError("Cannot create the Inbound shipment")

        return True

    def sanitize(self, dict_obj):
        """Sanitize the dict obj to ensure that all strings are stripped
        """
        def get_value(dict_obj, key):
            val = dict_obj.get(key, "")
            if isinstance(val, six.string_types):
                val = val.strip()
            elif isinstance(val, (list, tuple)):
                val = filter(None, val)
            return val

        keys = dict_obj.keys()
        for key in keys:
            value = get_value(dict_obj, key)
            if isinstance(value, dict):
                self.sanitize(value)
            dict_obj.update({key: value})

    def validate(self, record, required=None):
        """Checks the sample record(s) passed in has a valid format and with all
        the compulsory information available. Raises a ValueError exception if
        not compliant
        """
        if not required:
            return

        if isinstance(record, (list, tuple)):
            map(lambda rec: self.validate(rec, required=required), record)
            return

        for field in required:
            val = record.get(field)
            if not val:
                raise ValueError("Field is missing or empty: {}".format(field))

    def get_external_laboratory(self, code):
        lab = utils.get_by_code("ExternalLaboratory", code)
        if not lab:
            # External Laboratory not found for the given code
            raise ValueError("Referring lab not found: {}".format(code))

        if not api.is_active(lab):
            # The External laboratory is not active
            raise ValueError("Referring lab is not active: {}".format(code))

        if not lab.get_referring():
            # External Laboratory found, but not a referring lab
            raise ValueError("Not a referring lab: {}".format(code))

        return lab
