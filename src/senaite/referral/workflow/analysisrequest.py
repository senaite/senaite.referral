# -*- coding: utf-8 -*-

from senaite.referral import check_installed
from senaite.referral.remotelab import get_remote_connection
from senaite.referral.utils import get_field_value
from senaite.referral.workflow import revoke_analyses_permissions
from senaite.referral.workflow import ship_sample

from bika.lims.workflow import doActionFor


@check_installed(None)
def AfterTransitionEventHandler(sample, event): # noqa lowercase
    """Actions to be done just after a transition for a sample takes place
    """
    if not event.transition:
        return

    if event.transition.id == "no_sampling_workflow":
        after_no_sampling_workflow(sample)

    if event.transition.id == "ship":
        after_ship(sample)

    if event.transition.id == "verify":
        after_verify(sample)


def after_no_sampling_workflow(sample):
    """Automatically receive and ship samples for which an outbound shipment
    has been specified on creation (Add sample form)
    """
    shipment = get_field_value(sample, "OutboundShipment")
    if not shipment:
        return

    # Transition the sample to received + shipped status
    doActionFor(sample, "receive")
    ship_sample(sample, shipment)


def after_ship(sample):
    """Automatically revoke edit permissions for analyses from this sample
    """
    revoke_analyses_permissions(sample)


def after_verify(sample):
    """Notify the referring laboratory about this sample
    """
    shipment = get_field_value(sample, "InboundShipment")
    if not shipment:
        return

    # Notify the referring laboratory
    lab = shipment.getReferringLaboratory()
    remote_lab = get_remote_connection(lab)
    if not remote_lab:
        return

    # Update the results for this sample in the remote lab
    remote_lab.update_analyses(sample)
