# -*- coding: utf-8 -*-

from senaite.referral.remotelab import get_remote_connection


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
