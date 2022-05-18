# -*- coding: utf-8 -*-

from senaite.referral.workflow import TransitionEventHandler
from senaite.referral.workflow.outboundshipment import events


def AfterTransitionEventHandler(shipment, event): # noqa lowercase
    """Actions to be done just after a transition for an Outbound Sample
    Shipment takes place
    """
    TransitionEventHandler("after", shipment, events, event)
