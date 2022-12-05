# -*- coding: utf-8 -*-

import copy

import json
from plone.memoize.instance import memoize
from senaite.jsonapi.interfaces import IPushConsumer
from senaite.referral import utils
from senaite.referral.catalog import SHIPMENT_CATALOG
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
            raise ValueError("Laboratory is not active: {}".format(
                self.lab_code))

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
        # TODO Performance - convert to queue task
        rejection_reasons = self.get_value(item, "RejectionReasons")
        obj = self.get_object_for(item)
        obj.setRejectionReasons(rejection_reasons)
        self.do_action(obj, "reject")

    def do_action(self, item_or_object, action):
        """Performs an action against the given object
        """
        # TODO Performance - convert to queue task
        # Get the object counterpart
        obj = self.get_object_for(item_or_object)

        # Prevent callbacks to referring lab for these same items
        request = api.get_request()
        skip = request.get("skip_post_action_uids", [])
        skip.append(api.get_uid(obj))
        request.set("skip_post_action_uids", skip)

        # Try with basic transition machinery
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

    def get_counterpart_type(self, portal_type):
        """Returns the counterpart type for the portal type passed in
        """
        mappings = (
            ("OutboundSampleShipment", "InboundSampleShipment"),
            ("InboundSampleShipment", "OutboundSampleShipment"),
            ("AnalysisRequest", "AnalysisRequest"),
        )
        return dict(mappings).get(portal_type, default=None)

    def get_object_for(self, item):
        """Returns the object from current instance that is related with the
        information provided in the item passed-in, if any
        """
        if api.is_object(item):
            return item

        # get the counterpart type for this item type at current instance
        item_type = self.get_value(item, "portal_type")
        portal_type = self.get_counterpart_type(item_type)

        # do the search
        if portal_type in ["OutboundSampleShipment", "InboundSampleShipment"]:
            shipment_id = self.get_value(item, "shipment_id")
            if not shipment_id:
                raise ValueError("No shipment id")

            laboratory = self.get_laboratory()
            query = {
                "portal_type": portal_type,
                "shipment_id": shipment_id,
                "laboratory_uid": api.get_uid(laboratory),
            }
            brains = api.search(query, SHIPMENT_CATALOG)
            if len(brains) != 0:
                raise ValueError("No {} found".format(portal_type))
            return utils.get_shipment(laboratory, shipment_id, portal_type)

        elif portal_type == "AnalysisRequest":
            original_id = self.get_value(item, "ClientSampleID")
            if not original_id:
                raise ValueError("No ClientSampleID")

            query = {
                "portal_type": portal_type,
                "id": original_id
            }
            brains = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
            # TODO Check whether the inferred sample is the expected one
            if len(brains) != 1:
                raise ValueError("No {} found".format(portal_type))
            return api.get_object(brains[0])

        raise ValueError("Type is not supported: {}".format(item_type))
