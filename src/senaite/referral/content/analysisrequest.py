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

from archetypes.schemaextender.interfaces import IBrowserLayerAwareExtender
from archetypes.schemaextender.interfaces import ISchemaExtender
from Products.CMFCore.permissions import View
from senaite.referral import ISenaiteReferralLayer
from senaite.referral import messageFactory as _
from senaite.referral.catalog import SHIPMENT_CATALOG
from senaite.referral.fields import ExtUIDReferenceField
from zope.component import adapter
from zope.interface import implementer

from bika.lims.browser.widgets import ReferenceWidget
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
                catalog_name=SHIPMENT_CATALOG,
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
