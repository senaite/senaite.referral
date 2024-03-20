# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFERRAL.
#
# SENAITE.REFERRAL is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2021-2022 by it's authors.
# Some rights reserved, see README and LICENSE.

from senaite.referral import check_installed
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.interfaces import IOutboundSampleShipment
from senaite.referral.remotelab import get_remote_connection
from senaite.referral.workflow import change_workflow_state
from senaite.referral.workflow import restore_referred_sample
from senaite.referral.workflow import ship_sample

from bika.lims.workflow import doActionFor

SAMPLE_WORKFLOW = "bika_ar_workflow"
ANALYSIS_WORKFLOW = "bika_analysis_workflow"


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

    if event.transition.id == "reject":
        after_reject(sample)

    if event.transition.id == "invalidate":
        after_invalidate(sample)

    if event.transition.id == "invalidate_at_reference":
        after_invalidate_at_reference(sample)

    if event.transition.id == "recall_from_shipment":
        restore_referred_sample(sample)


def after_no_sampling_workflow(sample):
    """Automatically receive and ship samples for which an outbound shipment
    has been specified on creation (Add sample form)
    """
    shipment = sample.getOutboundShipment()
    if not shipment:
        return

    # Transition the sample to received + shipped status
    doActionFor(sample, "receive")
    ship_sample(sample, shipment)


def after_ship(sample):
    """Automatically transitions the analyses from the sample to referred status
    """
    for analysis in sample.getAnalyses(full_objects=True):
        doActionFor(analysis, "refer")


def after_verify(sample):
    """Notify the referring laboratory about this sample
    """
    shipment = sample.getInboundShipment()
    if not shipment:
        return

    # Notify the referring laboratory
    lab = shipment.getReferringLaboratory()
    remote_lab = get_remote_connection(lab)
    if not remote_lab:
        return

    # Update the results for this sample in the remote lab
    remote_lab.update_analyses(sample)


def after_reject(sample):
    """Notify the referring laboratory about this sample
    """
    shipment = sample.getInboundShipment()
    if not shipment:
        return

    # Notify the referring laboratory
    lab = shipment.getReferringLaboratory()
    remote_lab = get_remote_connection(lab)
    if not remote_lab:
        return

    # Notify the sample was rejected to the referring lab
    remote_lab.do_action(sample, "reject")


def get_remote_lab(shipment):
    """Returns the remote laboratory assigned to the given shipment, if any
    """
    lab = None
    if IInboundSampleShipment.providedBy(shipment):
        lab = shipment.getReferringLaboratory()
    elif IOutboundSampleShipment.providedBy(shipment):
        lab = shipment.getReferenceLaboratory()
    return get_remote_connection(lab)


def after_invalidate(sample):
    """"Actions to do when invalidating a sample
    """
    shipment = sample.getInboundShipment()
    referring = get_remote_lab(shipment)
    if referring:
        # notify the referring laboratory
        referring.do_action(sample, "invalidate_at_reference")


def after_invalidate_at_reference(sample):
    """Actions to do when a sample is invalidated at reference laboratory
    """
    retest = sample.getRetest()
    if not retest:
        # transition this sample to 'invalid' status
        doActionFor(sample, "invalidate")
        retest = sample.getRetest()
    else:
        # change workflow manually, but omit action so no after events
        change_workflow_state(sample, SAMPLE_WORKFLOW, "invalid")

    # manually transition the retest to 'referred' status
    change_workflow_state(retest, SAMPLE_WORKFLOW, "shipped", action="ship")

    # and its analyses as well
    for analysis in retest.objectValues("Analysis"):
        change_workflow_state(analysis, ANALYSIS_WORKFLOW,
                              state_id="referred",
                              action="refer")
