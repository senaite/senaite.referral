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
