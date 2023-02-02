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

from bika.lims import api
from bika.lims.catalog import SETUP_CATALOG
from bika.lims.utils.analysisrequest import create_analysisrequest
from bika.lims.workflow import doActionFor

try:
    from senaite.queue.api import is_queue_ready
    from senaite.queue.api import add_task
except ImportError:
    # Queue is not installed
    is_queue_ready = None
    add_task = None


def after_receive_inbound_sample(inbound_sample):
    """Event fired after a transition "receive_inbound_sample" for an
    InboundSample object is triggered. System creates the counterpart sample
    in current instance and tries to receive the whole inbound shipment
    afterwards
    """
    if inbound_sample.getRawSample():
        # There is a counterpart sample already
        return

    # Create the sample
    sample = create_sample(inbound_sample)

    # Auto-receive the sample object
    doActionFor(sample, "receive")

    # Try with the whole shipment
    shipment = inbound_sample.getInboundShipment()
    doActionFor(shipment, "receive_inbound_shipment")


def after_reject_inbound_sample(inbound_sample):
    """Event fired after a transition "reject_inbound_sample" for an
    InboundSample object is triggered. If all inbound samples from the
    inbound shipment have been rejected and no regular samples have been
    created yet, the inbound shipment is automatically rejected as well
    """
    shipment = inbound_sample.getInboundShipment()
    for sample in shipment.getInboundSamples():
        if api.get_review_status(sample) != "rejected":
            return

    # All inbound samples have been rejected. Reject the shipment
    doActionFor(shipment, "reject_inbound_shipment")


def create_sample(inbound_sample):
    """Creates a counterpart sample for the inbound sample passed in
    """
    # Get the shipment that contains this inbound sample
    shipment = inbound_sample.getInboundShipment()

    # Get the default client for this shipment
    client = shipment.getReferringClient()
    client = api.get_object(client)

    # Get baseline objects mappings
    services = get_services_mapping()
    sample_types = get_sample_types_mapping()

    # Create the sample object
    sample_type = inbound_sample.getSampleType()
    sample_type_uid = sample_types.get(sample_type)

    keywords = inbound_sample.getAnalyses() or []
    services_uids = map(lambda key: services.get(key), keywords)
    services_uids = filter(api.is_uid, services_uids)

    values = {
        "Client": api.get_uid(client),
        "Contact": None,
        "ClientSampleID": inbound_sample.getReferringID(),
        "DateSampled": inbound_sample.getDateSampled(),
        "SampleType": sample_type_uid,
        "Priority": inbound_sample.getPriority(),
        "InboundShipment": api.get_uid(shipment),
    }

    # Create the sample and assign the shipment
    request = api.get_request()
    sample = create_analysisrequest(client, request, values, services_uids)

    # Associate this new Sample with the Inbound Sample
    inbound_sample.setSample(sample)
    return sample


def get_sample_types_mapping():
    """Returns a dict with sample type titles, ids and prefixes as keys and
    values as sample type UIDs to facilitate the retrieval by id, prefix or
    title
    """
    sample_types = dict()
    query = {"portal_type": "SampleType", "is_active": True}
    brains = api.search(query, SETUP_CATALOG)
    for brain in brains:
        obj = api.get_object(brain)
        uid = api.get_uid(obj)
        obj_id = api.get_id(obj)
        title = api.get_title(obj)
        prefix = obj.getPrefix()
        sample_types[obj_id] = uid
        sample_types[title] = uid
        sample_types[prefix] = uid
        sample_types[uid] = uid
    return sample_types


def get_services_mapping():
    """Returns a dict with service ids, titles and keywords as keys and values
    as service UIDs to facilitate the retrieval of services by title, keyword
    or by id
    """
    services = dict()
    query = {"portal_type": "AnalysisService", "is_active": True}
    brains = api.search(query, SETUP_CATALOG)
    for brain in brains:
        uid = api.get_uid(brain)
        obj_id = api.get_id(brain)
        title = api.get_title(brain)
        keyword = brain.getKeyword
        services[obj_id] = uid
        services[title] = uid
        services[keyword] = uid
        services[uid] = uid
    return services
