# -*- coding: utf-8 -*-

from senaite.referral.workflow import TransitionEventHandler
from senaite.referral.workflow.inboundsampleshipment import events


def AfterTransitionEventHandler(shipment, event): # noqa lowercase
    """Actions to be done just after a transition for an Inbound Sample
    shipment takes place
    """
    TransitionEventHandler("after", shipment, events, event)
