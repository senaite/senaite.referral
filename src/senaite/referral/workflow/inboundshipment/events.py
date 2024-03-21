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

from senaite.referral.remotelab import get_remote_connection
from senaite.referral.workflow import do_queue_or_action_for

from bika.lims import api
from bika.lims.workflow import doActionFor as do_action_for


def after_receive_inbound_samples(shipment):
    """Event fired after transition "receive_inbound_samples" for an Inbound
    Sample Shipment is triggered. System receives all the inbound samples that
    have not been received yet and tries to receive the inbound shipment
    afterwards
    """
    # Try to receive (or queue the reception) of inbound samples
    samples = shipment.getInboundSamples()
    do_queue_or_action_for(samples, "receive_inbound_sample", context=shipment)


def after_receive_inbound_shipment(shipment):
    """Event fired after transition "receive_inbound_shipment" for an Inbound
    Sample Shipment is triggered. System notifies the referring laboratory that
    the shipment has been delivered
    """
    # Notify the remote laboratory
    lab = shipment.getReferringLaboratory()
    remote_lab = get_remote_connection(lab)
    if not remote_lab:
        return

    # Collect all the actions to be performed at reference. By default, all
    # samples from outbound shipment are in "referred" status, so there is
    # only the need to transition those that have been rejected
    objects_actions = []
    status_actions = {"rejected": "reject_at_reference"}
    for sample in shipment.getInboundSamples():
        status = api.get_review_status(sample)
        action = status_actions.get(status)
        if action:
            objects_actions.append((sample, action))

    # Mark the outbound shipment counterpart as delivered too
    objects_actions.append((shipment, "deliver_outbound_shipment"))

    # Notify the reference lab
    remote_lab.do_actions(shipment, objects_actions)


def after_reject_inbound_shipment(shipment):
    """Event fired after transition "reject_inbound_shipment" for an Inbound
    Sample Shipment is triggered. All inbound samples from the shipment are
    rejected as well
    """
    # Reject all InboundSample objects (not-yet-received)
    for inbound_sample in shipment.getInboundSamples():
        do_action_for(inbound_sample, "reject_inbound_sample")

    # Notify the remote laboratory
    lab = shipment.getReferringLaboratory()
    remote_lab = get_remote_connection(lab)
    if not remote_lab:
        return

    # Collect all the actions to be performed at reference. By default, all
    # samples from outbound shipment are in "referred" status, so there is
    # only the need to transition those that have been rejected
    objects_actions = []
    status_actions = {"rejected": "reject_at_reference"}
    for sample in shipment.getInboundSamples():
        status = api.get_review_status(sample)
        action = status_actions.get(status)
        if action:
            objects_actions.append((sample, action))

    # Mark the outbound shipment counterpart as rejected
    objects_actions.append((shipment, "reject_outbound_shipment"))

    # Notify the reference lab
    remote_lab.do_actions(shipment, objects_actions)
