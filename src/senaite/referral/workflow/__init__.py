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

from senaite.referral.interfaces import IOutboundSampleShipment
from zope.lifecycleevent import modified

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.utils import changeWorkflowState
from bika.lims.workflow import doActionFor


def TransitionEventHandler(before_after, obj, mod, event): # noqa lowercase
    if not event.transition:
        return

    function_name = "{}_{}".format(before_after, event.transition.id)
    if hasattr(mod, function_name):
        # Call the function from events package
        getattr(mod, function_name)(obj)


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
    shipment.addSample(sample)

    # Assign the shipment to the sample
    sample.setOutboundShipment(shipment)
    doActionFor(sample, "ship")

    # Reindex the sample
    sample.reindexObject()


def recover_sample(sample, shipment=None):
    """Recovers a sample from a shipment
    """
    sample = api.get_object(sample)
    if not IAnalysisRequest.providedBy(sample):
        portal_type = api.get_portal_type(sample)
        raise ValueError("Type not supported: {}".format(portal_type))

    if not shipment:
        # Extract the shipment from the sample
        shipment = sample.getOutboundShipment()

    if api.is_uid(shipment):
        shipment = api.get_object(shipment, default=None)

    if IOutboundSampleShipment.providedBy(shipment):
        # Remove the sample from the shipment
        shipment.removeSample(sample)

    # Remove the shipment assignment from sample
    sample.setOutboundShipment(None)

    # Transition the sample and analyses to the state before sample was shipped
    status = api.get_review_status(sample)
    if status == "shipped":
        prev = get_previous_status(sample, default="sample_received")
        changeWorkflowState(sample, "bika_ar_workflow", prev)

    # Restore status of referred analyses
    restore_referred_analyses(sample)

    # Notify the sample has ben modified
    modified(sample)

    # Reindex the sample
    sample.reindexObject()

    # Reindex the shipment
    shipment.reindexObject()


def restore_referred_analyses(sample):
    """Rolls the status of referred analyses from the given sample back to the
    status they had before being referred
    """
    wf_id = "bika_analysis_workflow"
    analyses = sample.getAnalyses(full_objects=True, review_state="referred")
    for analysis in analyses:
        prev = get_previous_status(analysis, default="unassigned")
        wf_state = {"action": "restore_referred"}
        changeWorkflowState(analysis, wf_id, prev, **wf_state)
