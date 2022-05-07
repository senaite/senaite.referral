# -*- coding: utf-8 -*-

import copy
import json

from senaite.jsonapi.interfaces import IPushConsumer
from senaite.referral import utils
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.interfaces import IOutboundSampleShipment
from zope.interface import implementer

from bika.lims import api
from bika.lims.workflow import doActionFor

_marker = object()


class BaseConsumer(object):

    _data = None

    def __init__(self, data):
        self.raw_data = data

    @property
    def data(self):
        if self._data is None:
            self._data = {}
            for key in self.raw_data.keys():
                self._data[key] = self.get_record(self.raw_data, key)
        return self._data

    def get_record(self, payload, id):
        record = payload.get(id)
        if isinstance(record, (list, tuple, list, dict)):
            return copy.deepcopy(record)
        try:
            return json.loads(record)
        except:
            return record

    def get_value(self, item, field_name, default=_marker):
        if field_name not in item:
            if default is _marker:
                raise ValueError("Field is missing: '{}'".format(field_name))
            return default

        value = item.get(field_name)
        if not value:
            if default is _marker:
                raise ValueError("Field is empty: '{}'".format(field_name))
            return default
        return value


@implementer(IPushConsumer)
class ReferralConsumer(BaseConsumer):
    """Handles push requests for name senaite.referral.consumer
    """

    @property
    def action(self):
        return self.get_value(self.data, "action")

    @property
    def items(self):
        return self.get_value(self.data, "items")

    @property
    def lab_code(self):
        """Returns the code of the laboratory that sends the POST request
        """
        return self.get_value(self.data, "lab_code")

    def process(self):
        """Processes the data sent via POST in accordance with the value for
        'action' parameter of the POST request
        """
        # Get the external laboratory object that represents the lab that
        # sends this POST request
        lab = utils.get_by_code("ExternalLaboratory", self.lab_code)
        if not lab:
            raise ValueError("Laboratory not found: {}".format(self.lab_code))
        if not api.is_active(lab):
            raise ValueError("Laboratory is inactive: {}".format(self.lab_code))

        # Iterate through items and process them
        for item in self.items:
            # Get the object counterpart
            obj = self.get_object_for(lab, item)
            doActionFor(obj, self.action)
        return True

    def get_object_for(self, lab, item):
        """Returns the object from current instance that is related with the
        information provided in the item passed-in, if any
        """
        portal_type = self.get_value(item, "portal_type")
        if portal_type == "OutboundSampleShipment":
            # The object in this instance should be an InboundShipment
            # TODO Improve this with shipments own catalog
            shipment_id = self.get_value(item, "shipment_id")
            for shipment in lab.objectValues():
                if IInboundSampleShipment.providedBy(shipment):
                    if shipment.getShipmentID() == shipment_id:
                        return shipment

        elif portal_type == "InboundSampleShipment":
            # The object in this instance should be an OutboundShipment
            # TODO Improve this with shipments own catalog
            shipment_id = self.get_value(item, "shipment_id")
            for shipment in lab.objectValues():
                if IOutboundSampleShipment.providedBy(shipment):
                    if shipment.getShipmentID() == shipment_id:
                        return shipment

        return None
