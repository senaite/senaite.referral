# -*- coding: utf-8 -*-

from bika.lims.workflow import doActionFor as do_action_for
from senaite.referral.remotelab import get_remote_connection


def after_receive_inbound_shipment(shipment):
    """ Event fired after transition "receive_inbound_shipment" for an Inbound
    Sample Shipment is triggered. System receives all the inbound samples that
    have not been received yet
    """
    for inbound_sample in shipment.getInboundSamples():
        # Try to receive the inbound sample. Won't be transitioned unless the
        # transition is allowed for its current status
        do_action_for(inbound_sample, "receive_inbound_sample")

    # Notify the remote laboratory
    lab = shipment.getReferringLaboratory()
    remote_lab = get_remote_connection(lab)
    if not remote_lab:
        return

    # Mark the outbound shipment counterpart as delivered
    remote_lab.do_action(shipment, "deliver_outbound_shipment")


def after_reject_inbound_shipment(shipment):
    """Event fired after transition "reject_inbound_shipment" for an Inbound
    Sample Shipment is triggered. All Samples from the shipment, even if not
    yet received, are rejected too
    """
    # Reject all InboundSample objects (not-yet-received)
    for inbound_sample in shipment.getInboundSamples():
        do_action_for(inbound_sample, "reject_inbound_sample")

    # Reject all AnalysisRequest objects (received samples)
    for sample in shipment.getSamples():
        do_action_for(sample, "reject")
