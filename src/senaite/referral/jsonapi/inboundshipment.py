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

import json

import six
from Products.ATContentTypes.utils import DT2dt
from Products.CMFCore.permissions import AddPortalContent
from senaite.jsonapi.interfaces import IPushConsumer
from senaite.jsonapi.request import is_json_deserializable
from senaite.referral import utils
from senaite.referral.catalog import SHIPMENT_CATALOG
from zope.annotation.interfaces import IAnnotations
from zope.interface import implementer

from bika.lims import api
from bika.lims.api.security import revoke_permission_for


@implementer(IPushConsumer)
class InboundShipmentConsumer(object):
    """Handles push requests for name senaite.referral.inbound_shipment
    Receives samples dispatched by a referring laboratory and creates the
    inbound shipment in accordance
    """

    def __init__(self, data):
        self.data = data

    def process(self):
        """Processes the data sent via POST. Imports the inbound shipment by
        creating the necessary samples and analyses
        """
        # Sanitize the data first
        self.sanitize(self.data)

        # Validate the data passed-in
        required_fields = ["lab_code", "shipment_id", "dispatched", "samples"]
        self.validate(self.data, required=required_fields)

        # Ensure the samples passed-in are compliant
        required_fields = ["id", "date_sampled", "sample_type"]
        sample_records = self.data.get("samples")
        if isinstance(sample_records, six.string_types):
            if not is_json_deserializable(sample_records):
                raise ValueError("Value for 'samples' is not a valid JSON")
            sample_records = json.loads(sample_records)
        self.validate(sample_records, required=required_fields)

        # XXX translate sample info (e.g. SampleType) to UIDs

        dispatched = self.data.get("dispatched")
        dispatched_date = api.to_date(dispatched)
        if not dispatched_date:
            raise ValueError("Non-valid datetime format: {}".format(dispatched))

        # Get the lab for the given code
        lab_code = self.data.get("lab_code")
        lab = self.get_external_laboratory(lab_code)

        # Check if a shipment with the given id and lab exists already
        shipment_id = self.data.get("shipment_id")
        shipment = self.get_inbound_shipment(shipment_id, lab)
        if shipment:
            raise ValueError("Inbound shipment already exists: {}"
                             .format(shipment_id))

        # Create the Inbound Shipment and the Inbound Samples
        # TODO Performance - convert to queue task
        comments = self.data.get("comments", "")
        values = {
            "shipment_id": str(shipment_id),
            "referring_laboratory": api.get_uid(lab),
            "referring_client": lab.getReferringClient(),
            "comments": str(comments),
            "dispatched_datetime": DT2dt(dispatched_date),
            "samples": sample_records,
        }
        shipment = api.create(lab, "InboundSampleShipment", **values)
        for record in sample_records:
            self.create_inbound_sample(shipment, record)

        # Disallow the "Add portal content" permission so no more InboundSample
        # objects can be added (and the "Add new..." menu item is not displayed)
        revoke_permission_for(shipment, AddPortalContent, [])

        return True

    def get_inbound_shipment(self, shipment_id, laboratory, full_object=False):
        """Returns the InboundSampleShipment for the shipment id and laboratory
        passed-in, if any. Returns None otherwise
        """
        if not shipment_id:
            return None
        query = {
            "portal_type": "InboundSampleShipment",
            "shipment_id": shipment_id,
            "laboratory_uid": api.get_uid(laboratory)
        }
        brains = api.search(query, SHIPMENT_CATALOG)
        if not brains:
            return None
        if full_object:
            return api.get_object(brains[0])
        return brains[0]

    def sanitize(self, dict_obj):
        """Sanitize the dict obj to ensure that all strings are stripped
        """
        def get_value(dict_obj, key):
            val = dict_obj.get(key, "")
            if isinstance(val, six.string_types):
                val = val.strip()
            elif isinstance(val, (list, tuple)):
                val = filter(None, val)
            return val

        keys = dict_obj.keys()
        for key in keys:
            value = get_value(dict_obj, key)
            if isinstance(value, dict):
                self.sanitize(value)
            dict_obj.update({key: value})

    def validate(self, record, required=None):
        """Checks the sample record(s) passed in has a valid format and with all
        the compulsory information available. Raises a ValueError exception if
        not compliant
        """
        if not required:
            return

        if isinstance(record, (list, tuple)):
            map(lambda rec: self.validate(rec, required=required), record)
            return

        for field in required:
            val = record.get(field)
            if not val:
                raise ValueError("Field is missing or empty: {}".format(field))

    def get_external_laboratory(self, code):
        lab = utils.get_by_code("ExternalLaboratory", code)
        if not lab:
            # External Laboratory not found for the given code
            raise ValueError("Referring lab not found: {}".format(code))

        if not api.is_active(lab):
            # The External laboratory is not active
            raise ValueError("Referring lab is not active: {}".format(code))

        if not lab.getReferring():
            # External Laboratory found, but not a referring lab
            raise ValueError("Not a referring lab: {}".format(code))

        return lab

    def create_inbound_sample(self, shipment, record):
        """Creates an inbound sample inside the shipment with the information
        provided
        """
        date_sampled = api.to_date(record.get("date_sampled"))
        values = {
            "referring_id": record.get("id"),
            "date_sampled": date_sampled,
            "sample_type": record.get("sample_type"),
            "priority": record.get("priority", ""),
            "analyses": record.get("analyses"),
        }
        inbound_sample = api.create(shipment, "InboundSample", **values)

        # Store original data in annotations
        annotation = IAnnotations(inbound_sample)
        annotation["__original__"] = json.dumps(record)

        return inbound_sample
