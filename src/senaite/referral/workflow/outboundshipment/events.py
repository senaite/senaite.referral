# -*- coding: utf-8 -*-

from senaite.referral.remotelab import get_remote_connection
from senaite.referral.workflow import restore_referred_sample


def after_dispatch_outbound_shipment(shipment):
    """Event fired after transition "dispatch" for an Outbound Shipment is
    triggered. It sends a POST request for the creation of an Inbound Shipment
    counterpart in the receiving (reference) laboratory
    """
    lab = shipment.getReferenceLaboratory()
    remote_lab = get_remote_connection(lab)
    if not remote_lab:
        return

    # Create an inbound shipment counterpart in the receiving laboratory
    remote_lab.create_inbound_shipment(shipment)


def after_reject_outbound_shipment(shipment):
    """Event fired after a transition "reject" for an Outbound Shipment is
    triggered. It sends a POST request to reject the Inbound Shipment
    counterpart and samples in the receiving (reference) laboratory
    """
    lab = shipment.getReferenceLaboratory()
    remote_lab = get_remote_connection(lab)
    if not remote_lab:
        return

    # Reject the inbound shipment counterpart in the receiving laboratory
    remote_lab.do_action(shipment, "reject_inbound_shipment")


def after_cancel_outbound_shipment(shipment):
    """Event fired after a transition "cancel" for an Outbound Shipment is
    triggered. It restores the statuses of the samples contained to their status
    before they were shipped
    """
    for sample in shipment.getSamples():
        restore_referred_sample(sample)
