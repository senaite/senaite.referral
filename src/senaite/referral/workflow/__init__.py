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
from senaite.referral import logger
from senaite.referral.interfaces import IOutboundSampleShipment
from zope.lifecycleevent import modified

from bika.lims import api
from bika.lims import EditFieldResults
from bika.lims import EditResults
from bika.lims import FieldEditAnalysisResult
from bika.lims.api import security
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
    shipment.add_sample(sample)

    # Assign the shipment to the sample
    sample.setOutboundShipment(shipment)
    doActionFor(sample, "ship")

    # Revoke edition permissions of analyses
    revoke_analyses_permissions(sample)

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
        shipment.remove_sample(sample)

    # Remove the shipment assignment from sample
    sample.setOutboundShipment(None)

    # Transition the sample to the state before it was shipped
    status = api.get_review_status(sample)
    if status == "shipped":
        prev = get_previous_status(sample, default="sample_received")
        changeWorkflowState(sample, "bika_ar_workflow", prev)

    # Restore analyses permissions
    restore_analyses_permissions(sample)

    # Notify the sample has ben modified
    modified(sample)

    # Reindex the sample
    sample.reindexObject()

    # Reindex the shipment
    shipment.reindexObject()


def revoke_analyses_permissions(sample):
    """Revoke edit permissions for analsyes from the sample passed-in
    """
    def revoke_permission(obj, perm, roles):
        try:
            security.revoke_permission_for(obj, perm, roles)
        except ValueError as e:
            # Keep invalid permission silent
            logger.warn(str(e))

    analyses = sample.getAnalyses(full_objects=True)
    for analysis in analyses:
        roles = security.get_valid_roles_for(analysis)
        revoke_permission(analysis, EditFieldResults, roles)
        revoke_permission(analysis, EditResults, roles)
        revoke_permission(analysis, FieldEditAnalysisResult, roles)
        analysis.reindexObject()


def restore_analyses_permissions(sample):
    """Restore the permissions of the analyses from the sample passed-in
    """
    wf_id = "bika_analysis_workflow"
    wf_tool = api.get_tool("portal_workflow")
    wf = wf_tool.getWorkflowById(wf_id)

    analyses = sample.getAnalyses(full_objects=True)
    for analysis in analyses:
        wf.updateRoleMappingsFor(analysis)
        analysis.reindexObject()
