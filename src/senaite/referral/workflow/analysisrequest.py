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
from senaite.referral.remotelab import get_remote_connection
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

    if event.transition.id == "reject":
        after_reject(sample)


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
