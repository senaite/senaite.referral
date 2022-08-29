# -*- coding: utf-8 -*-

import copy

import json
from plone.memoize.instance import memoize
from senaite.jsonapi.interfaces import IPushConsumer
from senaite.referral import utils
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.interfaces import IOutboundSampleShipment
from zope.interface import implementer

from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.utils import changeWorkflowState
from bika.lims.workflow import doActionFor
from bika.lims.workflow import isTransitionAllowed

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

    @memoize
    def get_laboratory(self):
        """Returns the external laboratory object that represents the lab that
        sends the current POST request
        """
        return utils.get_by_code("ExternalLaboratory", self.lab_code)

    def process(self):
        """Processes the data sent via POST in accordance with the value for
        'action' parameter of the POST request
        """
        if not self.action:
            raise ValueError("No action defined")

        if not self.lab_code:
            raise ValueError("No lab_code defined")

        laboratory = self.get_laboratory()
        if not laboratory:
            raise ValueError("Laboratory not found: {}".format(self.lab_code))

        if not api.is_active(laboratory):
            raise ValueError("Laboratory is inactive: {}".format(self.lab_code))

        # Iterate through items and process them
        for item in self.items:
            # Try to delegate to an existing function
            portal_type = self.get_value(item, "portal_type").lower()
            func_name = "do_{}_{}".format(portal_type, self.action.lower())
            func = getattr(self, func_name, None)
            if func:
                func(item)
            else:
                # Rely on default 'do_action'
                self.do_action(item, self.action)

        return True

    def do_analysisrequest_reject(self, item):
        """Rejects a referred sample
        """
        rejection_reasons = self.get_value(item, "RejectionReasons")
        obj = self.get_object_for(item)
        obj.setRejectionReasons(rejection_reasons)
        self.do_action(obj, "reject")

    def do_action(self, item_or_object, action):
        """Performs an action against the given object
        """
        # Get the object counterpart
        obj = self.get_object_for(item_or_object)
        if isTransitionAllowed(obj, action):
            doActionFor(obj, action)
            return

        # Check whether the action was performed already
        history = api.get_review_history(obj)
        if history and history[0].get("action", None) == action:
            return

        # Do force the transition
        workflows = api.get_workflows_for(obj)
        wf_tool = api.get_tool("portal_workflow")
        for wf_id in workflows:
            workflow = wf_tool.getWorkflowById(wf_id)
            if action not in workflow.transitions:
                continue
            transition = workflow.transitions[action]
            status = transition.new_state_id
            kwargs = {"action": action}
            changeWorkflowState(obj, wf_id, status, **kwargs)

    def get_object_for(self, item):
        """Returns the object from current instance that is related with the
        information provided in the item passed-in, if any
        """
        if api.is_object(item):
            return item

        portal_type = self.get_value(item, "portal_type")
        if portal_type == "OutboundSampleShipment":
            # The object in this instance should be an InboundShipment
            # TODO Improve this with shipments own catalog
            shipment_id = self.get_value(item, "shipment_id")
            lab = self.get_laboratory()
            for shipment in lab.objectValues():
                if IInboundSampleShipment.providedBy(shipment):
                    if shipment.getShipmentID() == shipment_id:
                        return shipment

        elif portal_type == "InboundSampleShipment":
            # The object in this instance should be an OutboundShipment
            # TODO Improve this with shipments own catalog
            shipment_id = self.get_value(item, "shipment_id")
            lab = self.get_laboratory()
            for shipment in lab.objectValues():
                if IOutboundSampleShipment.providedBy(shipment):
                    if shipment.getShipmentID() == shipment_id:
                        return shipment

        elif portal_type == "AnalysisRequest":
            original_id = self.get_value(item, "ClientSampleID")
            if not original_id:
                return None

            query = {"portal_type": "AnalysisRequest", "id": original_id}
            brains = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
            # TODO Check whether the inferred sample is the expected one
            if len(brains) == 1:
                return api.get_object(brains[0])

        raise ValueError("Counterpart object not found")
