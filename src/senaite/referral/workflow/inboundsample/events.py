# -*- coding: utf-8 -*-

from bika.lims import api
from bika.lims.catalog import SETUP_CATALOG
from bika.lims.utils.analysisrequest import create_analysisrequest
from bika.lims.workflow import doActionFor


def after_receive_inbound_sample(inbound_sample):
    """Event fired after a transition "receive_inbound_sample" for an
    InboundSample object is triggered. System creates the counterpart sample
    in current instance
    """
    sample = inbound_sample.getSample()
    if not sample:
        # This inbound sample does not have a Sample assigned yet
        sample = create_sample(inbound_sample)

        # Auto-receive the sample object
        doActionFor(sample, "receive")

    # If all inbound samples have been transitioned, try with the whole shipment
    shipment = inbound_sample.getInboundShipment()
    received = shipment.getInboundSamples()
    received = map(lambda i: api.get_review_status(i) == "received", received)
    if all(received):
        doActionFor(shipment, "receive_inbound_shipment")


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

    #  Create the sample and assign the shipment
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
    as service UIDs to facilitate the retrieval of services by title, keyword or
    by id
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
