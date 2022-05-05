# -*- coding: utf-8 -*-

import copy
import json

from datetime import datetime

from senaite.jsonapi.interfaces import IPushConsumer
from zope.interface import implementer

from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
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

        # Create a keyword -> analysis mapping
        allowed = ["registered", "assigned", "unassigned"]
        analyses = sample.getAnalyses(full_objects=True, review_status=allowed)
        analyses = dict([(an.getKeyword(), an) for an in analyses])

        # Update the analyses passed-in
        analysis_records = sample_record.get("analyses")
        for analysis_record in analysis_records:
            keyword = analysis_record.get("keyword")
            analysis = analyses.get(keyword)
            self.update_analysis(analysis, analysis_record)

        # XXX Rollback the sample to previous status?

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
        if not str(value):
            raise ValueError("Field is empty: '{}'".format(field_name))

    def get_sample(self, sample_id):
        """Returns the sample for the given ID, if any
        """
        query = {"portal_type": "AnalysisRequest", "id": sample_id}
        brains = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
        if not brains:
            raise ValueError("Sample not found: {}".format(sample_id))
        return api.get_object(brains[0])

    def update_analysis(self, analysis, record):
        if not analysis:
            return

        # Set the formatted result, cause we do not know if the configuration
        # of the analysis in the reference lab is the same
        result = record.get("formatted_result")
        original_result = analysis.getFormattedResult()
        if result == original_result:
            return

        # Cleanup the analysis object to prioritize the formatted result
        analysis.setStringResult(True)
        analysis.setResultOptions([])
        analysis.setAllowManualDetectionLimit(False)
        analysis.setCalculation(None)
        analysis.setDetectionLimitSelector(False)
        analysis.setDetectionLimitOperand("")
        analysis.setUnit("")

        # Avoid all analysis built-in logic for result assignment
        analysis.getField("Result").set(analysis, result)

        # Set Result capture date
        default_date = datetime.now()
        capture_date = record.get("result_date")
        capture_date = api.to_date(capture_date, default_date)
        analysis.setResultCaptureDate(capture_date)

        # Submit
        doActionFor(analysis, "submit")
