# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFERRAL.
#
# SENAITE.REFERRAL is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2021-2022 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IGuardAdapter
from bika.lims.utils import changeWorkflowState
from bika.lims.workflow import doActionFor
from senaite.referral.interfaces import IOutboundSampleShipment
from senaite.referral.utils import get_field_value
from senaite.referral.utils import set_field_value
from zope.interface import implementer
from zope.lifecycleevent import modified


def TransitionEventHandler(before_after, obj, mod, event): # noqa lowercase
    if not event.transition:
        return

    function_name = "{}_{}".format(before_after, event.transition.id)
    if hasattr(mod, function_name):
        # Call the function from events package
        getattr(mod, function_name)(obj)


@implementer(IGuardAdapter)
class BaseGuardAdapter(object):

    def __init__(self, context):
        self.context = context

    def get_module(self):
        raise NotImplementedError("To be implemented by child classes")

    def guard(self, action):
        func_name = "guard_{}".format(action)
        module = self.get_module()
        func = getattr(module, func_name, None)
        if func:
            return func(self.context)
        return True


def get_previous_status(instance, default=None):
    """Returns the previous state for the given instance from review history
    """
    # Get the current status
    current_status = api.get_review_status(instance)

    # Get the review history, most recent actions first
    history = api.get_review_history(instance)
    for item in history:
        status = item.get("review_state")
        if status and status != current_status:
            return status
    return default


def ship_sample(sample, shipment):
    """Adds the sample to the shipment
    """
    sample = api.get_object(sample)
    if not IAnalysisRequest.providedBy(sample):
        portal_type = api.get_portal_type(sample)
        raise ValueError("Type not supported: {}".format(portal_type))

    shipment = api.get_object(shipment)
    if not IOutboundSampleShipment.providedBy(shipment):
        portal_type = api.get_portal_type(shipment)
        raise ValueError("Type not supported: {}".format(portal_type))

    # Add the sample to the shipment
    shipment.add_sample(sample)

    # Assign the shipment to the sample
    shipment_uid = api.get_uid(shipment)
    set_field_value(sample, "OutboundShipment", shipment_uid)
    doActionFor(sample, "ship")


def recover_sample(sample, shipment=None):
    """Recovers a sample from a shipment
    """
    sample = api.get_object(sample)
    if not IAnalysisRequest.providedBy(sample):
        portal_type = api.get_portal_type(sample)
        raise ValueError("Type not supported: {}".format(portal_type))

    if not shipment:
        # Extract the shipment from the sample
        shipment = get_field_value(sample, "OutboundShipment")

    if api.is_uid(shipment):
        shipment = api.get_object(shipment, default=None)

    if IOutboundSampleShipment.providedBy(shipment):
        # Remove the sample from the shipment
        shipment.remove_sample(sample)

    # Remove the shipment assignment from sample
    set_field_value(sample, "OutboundShipment", None)

    # Transition the sample to the state before it was shipped
    status = api.get_review_status(sample)
    if status == "shipped":
        prev = get_previous_status(sample, default="sample_received")
        changeWorkflowState(sample, "bika_ar_workflow", prev)

    # Transition the "shipped" analyses to their prior status
    analyses = sample.getAnalyses(full_objects=True, review_state="shipped")
    for analysis in analyses:
        prev = get_previous_status(analysis, default="unassigned")
        changeWorkflowState(analysis, "bika_analysis_workflow", prev)
        analysis.reindexObject()

    # Notify the sample has ben modified
    modified(sample)

    # Reindex the sample
    sample.reindexObject()

    # Reindex the shipment
    shipment.reindexObject()
