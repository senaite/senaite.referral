# -*- coding: utf-8 -*-

from senaite.referral import check_installed
from senaite.referral.utils import get_field_value
from senaite.referral.workflow import ship_sample

from bika.lims.workflow import doActionFor


@check_installed(None)
def AfterTransitionEventHandler(sample, event): # noqa lowercase
    """Actions to be done just after a transition for a sample takes place
    """
    if not event.transition:
        return

    if event.transition.id == "no_sampling_workflow":
        shipment = get_field_value(sample, "OutboundShipment")
        if shipment:
            # Transition the sample to received + shipped status
            doActionFor(sample, "receive")
            ship_sample(sample, shipment)
