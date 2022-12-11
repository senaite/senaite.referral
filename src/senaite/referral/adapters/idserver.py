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

from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.interfaces import IOutboundSampleShipment
from zope.interface import implementer

from bika.lims import api
from bika.lims.idserver import get_type_id
from bika.lims.interfaces import IIdServerVariables

SHIPMENT_TYPES = [
    "InboundSampleShipment",
    "OutboundSampleShipment",
]


@implementer(IIdServerVariables)
class IDServerVariablesAdapter(object):
    """An adapter for the generation of Variables for ID Server
    """

    def __init__(self, context):
        self.context = context

    def get_variables(self, **kw):
        """Returns additional variables for ID Server depending on the type of
        the current context
        """
        variables = {}
        portal_type = get_type_id(self.context, **kw)

        if portal_type in SHIPMENT_TYPES:
            variables.update({
                "lab_code": self.get_lab_code(self.context)
            })

        return variables

    def get_lab_code(self, shipment):
        """Returns the code of the laboratory the shipment is assigned to
        """
        shipment = api.get_object(shipment)
        if IOutboundSampleShipment.providedBy(shipment):
            laboratory = shipment.getReferenceLaboratory()
        elif IInboundSampleShipment.providedBy(shipment):
            laboratory = shipment.getReferringLaboratory()
        else:
            str_type = repr(type(shipment))
            return ValueError("Type not supported: {}".format(str_type))
        return laboratory.getCode()
