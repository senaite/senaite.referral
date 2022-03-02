# -*- coding: utf-8 -*-

import requests
from datetime import datetime
from senaite.referral import logger
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.utils import get_lab_code
from senaite.referral.utils import get_object_by_title as get_obj
from senaite.referral.utils import is_valid_url

from bika.lims import api
from bika.lims.catalog import SETUP_CATALOG
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.utils.analysisrequest import create_analysisrequest


def after_receive(shipment):
    """ Event fired after transition "received" for an Inbound Sample Shipment
    is triggered. System creates the samples defined in the inbound shipment
    as required
    with the following criteria:
    - The Client contact is the contact id provided if exists. Picks the first
      client contact otherwise. If client does not have a contact, system
      creates a default one automatically.
    - The original sample ID (from the referring lab) is stored in Client Sample
      ID field for traceability purposes.
    - The Analyses to create are resolved based on the keywords mapping
    - The Sample Types are resolved based on the sample types mapping
    - The Containers are resolved based on the containers mapping
    """
    request = api.get_request()
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
        sample = create_analysisrequest(client, request, values, service_uids)
        samples.append(sample)

    # Assign the sample objects to the shipment
    sample_uids = map(api.get_uid, samples)
    shipment.set_samples(sample_uids)
