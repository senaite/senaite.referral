# -*- coding: utf-8 -*-

from senaite.referral.utils import get_object_by_title as get_obj
from senaite.referral.utils import set_field_value

from bika.lims import api
from bika.lims.catalog import SETUP_CATALOG
from bika.lims.utils.analysisrequest import create_analysisrequest


def after_receive_inbound_shipment(shipment):
    """ Event fired after transition "receive_inbounf_shipment" for an Inbound
    Sample Shipment is triggered. System creates the counterpart samples in
    current instance
    """
    request = api.get_request()
    shipment_uid = api.get_uid(shipment)
    client = shipment.getReferringClient()
    client = api.get_object(client)
    samples = []
    for sample_info in shipment.get_samples():
        if api.is_uid(sample_info):
            # Nothing to do here, maybe it has been created already
            continue

        # Create the sample object
        sample_type = sample_info.get("sample_type")
        sample_type = get_obj("SampleType", sample_type, catalog=SETUP_CATALOG)

        service_uids = []
        keywords = sample_info.get("analyses") or []
        if keywords:
            query = {
                "portal_type": "AnalysisService",
                "getKeyword": keywords
            }
            brains = api.search(query, SETUP_CATALOG)
            service_uids = map(api.get_uid, brains)

        values = {
            "Client": api.get_uid(client),
            "Contact": None,
            "ClientSampleID": sample_info.get("id"),
            "DateSampled": sample_info.get("date_sampled"),
            "SampleType": api.get_uid(sample_type)
        }

        #  Create the sample and assign the shipment
        sample = create_analysisrequest(client, request, values, service_uids)
        set_field_value(sample, "InboundShipment", shipment_uid)
        samples.append(sample)

    # Assign the sample objects to the shipment
    sample_uids = map(api.get_uid, samples)
    shipment.set_samples(sample_uids)
