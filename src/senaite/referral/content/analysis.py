# -*- coding: utf-8 -*-

from archetypes.schemaextender.interfaces import IBrowserLayerAwareExtender
from archetypes.schemaextender.interfaces import ISchemaExtender
from senaite.referral import ISenaiteReferralLayer
from senaite.referral.fields import ExtRecordsField
from senaite.referral.fields import ExtStringField
from zope.component import adapter
from zope.interface import implementer

from bika.lims.interfaces import IRoutineAnalysis


@adapter(IRoutineAnalysis)
@implementer(ISchemaExtender, IBrowserLayerAwareExtender)
class AnalysisSchemaExtender(object):
    """Schema extender for IRoutineAnalysis object
    """
    layer = ISenaiteReferralLayer
    custom_fields = [
        ExtRecordsField(
            "ReferenceVerifiers",
            required=False,
            subfields=("userid", "username", "email", "fullname", "lab_code"),
        ),
        ExtRecordsField(
            "ReferenceAnalysts",
            required=False,
            subfields=("userid", "username", "email", "fullname", "lab_code"),
        ),
        ExtStringField(
            "ReferenceInstrument",
            default="",
            required=False,
        ),
        ExtStringField(
            "ReferenceMethod",
            default="",
            required=False,
        )
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.custom_fields
