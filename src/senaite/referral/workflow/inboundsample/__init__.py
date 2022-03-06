# -*- coding: utf-8 -*-

from senaite.referral.workflow import TransitionEventHandler
from senaite.referral.workflow.inboundsample import events


def AfterTransitionEventHandler(inbound_sample, event): # noqa lowercase
    """Actions to be done just after a transition for an Inbound Sample
    """
    TransitionEventHandler("after", inbound_sample, events, event)
