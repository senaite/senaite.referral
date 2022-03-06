# -*- coding: utf-8 -*-

from bika.lims.workflow import doActionFor as do_action_for


def after_receive_inbound_shipment(shipment):
    """ Event fired after transition "receive_inbound_shipment" for an Inbound
    Sample Shipment is triggered. System receives all the inbound samples that
    have not been received yet
    """
    for inbound_sample in shipment.getInboundSamples():
        # Try to receive the inbound sample. Won't be transitioned unless the
        # transition is allowed for its current status
        do_action_for(inbound_sample, "receive_inbound_sample")
