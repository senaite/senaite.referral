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

import copy
import json
from datetime import datetime

from senaite.core.workflow import ANALYSIS_WORKFLOW
from senaite.jsonapi.exceptions import APIError
from senaite.jsonapi.interfaces import IPushConsumer
from zope.interface import alsoProvides
from zope.interface import implementer

from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.interfaces import ISubmitted
from bika.lims.utils import changeWorkflowState
from bika.lims.workflow import doActionFor


@implementer(IPushConsumer)
class OutboundSampleConsumer(object):
    """Handles push requests for name senaite.referral.outbound_sample
    Receives information from a sample that was dispatched to a reference
    laboratory and updates the analyses results in accordance
    """

    def __init__(self, data):
        self.data = data

    def process(self):
        """Processes the data sent via POST. Look for sample and updates their
        analyses in accordance with the received data
        """
        # Validate data first
        data = self.get_data()
        self.validate(data)

        # Find the sample with the given referring id
        sample_record = data.get("sample")
        sample_id = sample_record.get("referring_id")
        sample = self.get_sample(sample_id)

        # If the sample is invalidated, update the retest instead
        while self.is_invalidated(sample):
            sample = sample.getRetest()
            if not sample:
                msg = "No retest found for '%s'" % sample_id
                raise APIError(500, "ValueError: {}".format(msg))

        # Do not allow to modify the sample if not referred
        if api.get_review_status(sample) != "shipped":
            # We don't rise an exception here because maybe the sample was
            # updated earlier, but the reference lab got a timeout error and
            # the remote user is now retrying the notification
            # TODO Keep track of the incoming notifications in current object
            return True

        # TODO Performance - convert to queue task
        # Create a keyword -> analysis mapping
        allowed = ["referred"]
        analyses = sample.getAnalyses(full_objects=True, review_state=allowed)
        analyses = dict([(an.getKeyword(), an) for an in analyses])

        # Update the analyses passed-in
        analysis_records = sample_record.get("analyses")
        for analysis_record in analysis_records:
            keyword = analysis_record.get("keyword")
            analysis = analyses.get(keyword)
            try:
                self.update_analysis(analysis, analysis_record)
            except Exception as e:
                raise APIError(500, "{}: {}".format(type(e).__name__, str(e)))

        return True

    def get_data(self):
        out = {}
        for key in self.data.keys():
            out[key] = self.get_record(self.data, key)
        return out

    def get_record(self, payload, id):
        record = payload.get(id)
        if isinstance(record, (list, tuple, list, dict)):
            return copy.deepcopy(record)
        try:
            return json.loads(record)
        except:
            return record

    def validate(self, payload):
        """Validates that the payload passed-in is meets the expected format
        """
        field_names = ["referring_id", "analyses", "shipment_id"]
        sample_record = payload.get("sample")
        self.validate_nonempty(field_names, sample_record)

        field_names = ["keyword", "formatted_result"]
        analysis_records = sample_record.get("analyses")
        self.validate_nonempty(field_names, analysis_records)

    def validate_nonempty(self, field_name, record):
        """Validates if the value for the attr_name from the record passed-in
        is empty or missing
        """
        if isinstance(field_name, (list, tuple)):
            for fn in field_name:
                self.validate_nonempty(fn, record)
            return

        if isinstance(record, (list, tuple)):
            for rec in record:
                self.validate_nonempty(field_name, rec)
            return

        if field_name not in record:
            raise ValueError("Field is missing: '{}'".format(field_name))

        value = record.get(field_name)
        if not value:
            raise ValueError("Field is empty: '{}'".format(field_name))

    def get_sample(self, sample_id):
        """Returns the sample for the given ID, if any
        """
        query = {"portal_type": "AnalysisRequest", "id": sample_id}
        brains = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
        if not brains:
            raise ValueError("Sample not found: {}".format(sample_id))
        if len(brains) > 1:
            raise ValueError("More than one sample: {}".format(sample_id))

        # Get the sample object
        return api.get_object(brains[0])

    def update_analysis(self, analysis, record):
        if not analysis:
            return

        # Set the formatted result, cause we do not know if the configuration
        # of the analysis in the reference lab is the same
        result = record.get("formatted_result")

        # Cleanup the analysis object to prioritize the formatted result
        analysis.setStringResult(True)
        analysis.setResultOptions([])
        analysis.setAllowManualDetectionLimit(False)
        analysis.setCalculation(None)
        analysis.setDetectionLimitSelector(False)
        analysis.setDetectionLimitOperand("")
        analysis.setInterimFields([])
        analysis.setAttachmentRequired(False)
        analysis.setPointOfCapture("lab")
        analysis.setUnit("")

        # Avoid all analysis built-in logic for result assignment
        analysis.getField("Result").set(analysis, result)

        # Set Result capture date
        default_date = datetime.now()
        capture_date = record.get("result_date")
        capture_date = api.to_date(capture_date, default_date)
        analysis.setResultCaptureDate(capture_date)

        # Store the instrument and method
        instrument = record.get("instrument", "")
        analysis.setReferenceInstrument(instrument)
        method = record.get("method", "")
        analysis.setReferenceMethod(method)

        # Inject the remote analysts
        analysts = record.get("analysts")
        analysis.setReferenceAnalysts(analysts)

        # Inject the remote verifiers
        verifiers = record.get("verifiers")
        analysis.setReferenceVerifiers(verifiers)

        # Do a manual transition to overcome core's default guards. For
        # instance system won't allow the submission of an analysis if the
        # setting "Allow to submit analysis if not assigned" from setup is set
        # to False. Obviously, this analysis is not assigned to a Worksheet,
        # cause is processed externally.
        # TODO 2.x Do not do manual transition, fix getAllowToSubmitNotAssigned
        alsoProvides(analysis, ISubmitted)
        wf_id = ANALYSIS_WORKFLOW
        wf_state = {"action": "submit"}
        changeWorkflowState(analysis, wf_id, "to_be_verified", **wf_state)

        # Auto-verify the analysis
        analysis.setSelfVerification(1)
        analysis.setNumberOfRequiredVerifications(1)
        doActionFor(analysis, "verify")

        # Reindex the analysis
        analysis.reindexObject()

    def is_invalidated(self, sample):
        """Returns whether the sample was invalidated in present laboratory
        or at reference laboratory
        """
        statuses = ["invalid", "invalidated_at_reference"]
        return api.get_review_status(sample) in statuses
