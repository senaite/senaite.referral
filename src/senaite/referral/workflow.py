# -*- coding: utf-8 -*-

from senaite.referral.interfaces import IOutboundSampleShipment
from senaite.referral.utils import get_field_value
from senaite.referral.utils import set_field_value
from zope.lifecycleevent import modified

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.utils import changeWorkflowState
from bika.lims.workflow import doActionFor


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

    # Notify the sample has ben modified
    modified(sample)

    # Reindex the sample
    sample.reindexObject()

    # Reindex the shipment
    shipment.reindexObject()
