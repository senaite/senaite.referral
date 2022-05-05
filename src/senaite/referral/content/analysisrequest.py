# -*- coding: utf-8 -*-

from archetypes.schemaextender.interfaces import IBrowserLayerAwareExtender
from archetypes.schemaextender.interfaces import ISchemaExtender
from Products.CMFCore.permissions import View
from senaite.referral import ISenaiteReferralLayer
from senaite.referral import messageFactory as _
from senaite.referral.fields import ExtUIDReferenceField
from zope.component import adapter
from zope.interface import implementer

from bika.lims.browser.widgets import ReferenceWidget
from bika.lims.fields import ExtStringField
from bika.lims.interfaces import IAnalysisRequest


@adapter(IAnalysisRequest)
@implementer(ISchemaExtender, IBrowserLayerAwareExtender)
class AnalysisRequestSchemaExtender(object):
    """Schema extender for AnalysisRequest object
    """
    layer = ISenaiteReferralLayer
    custom_fields = [

        ExtUIDReferenceField(
            "InboundShipment",
            allowed_types=("InboundSampleShipment",),
            widget=ReferenceWidget(
                # Read-only mode
                label=_("Inbound shipment"),
                render_own_label=True,
            )
        ),

        ExtUIDReferenceField(
            "OutboundShipment",
            allowed_types=("OutboundSampleShipment",),
            read_permission=View,
            widget=ReferenceWidget(
                label=_("Outbound shipment"),
                showOn=True,
                render_own_label=True,
                visible={"add": "edit", "secondary": "disabled"},
                catalog_name="portal_catalog",
                base_query=dict(
                    is_active=True,
                    sort_on="sortable_title",
                    sort_order="ascending"
                ),
            )
        ),
    ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self.custom_fields
