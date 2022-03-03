# -*- coding: utf-8 -*-

from senaite.referral import check_installed
from senaite.referral.utils import get_field_value
from senaite.referral.workflow import ship_sample

from bika.lims.utils import changeWorkflowState
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
    """Automatically transition the not-yet-submitted analyses from the sample
    to shipped status, so they cannot be edited by regular users anymore
    """
    wf_id = "bika_analysis_workflow"
    status = ["registered", "unassigned", "assigned"]
    analyses = sample.getAnalyses(full_objects=True, review_state=status)
    for analysis in analyses:
        args = {"action": "ship"}
        changeWorkflowState(analysis, wf_id, "shipped", **args)
        analysis.reindexObject()
