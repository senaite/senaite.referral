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

from bika.lims import api
from bika.lims.adapters.widgetvisibility import SenaiteATWidgetVisibility


class InboundShipmentFieldVisibility(SenaiteATWidgetVisibility):
    """Adapter that handles the visibility of Sample's InboundShipment field
    """
    def __init__(self, context):
        super(InboundShipmentFieldVisibility, self).__init__(
            context=context, sort=10, field_names=["InboundShipment"])

    def isVisible(self, field, mode="view", default="visible"):
        """Returns the visibility of this field in a given mode
        """
        # Do not display the field if current user is client
        if api.get_current_client():
            return "invisible"

        # Do not display the field unless "view" mode. The assignment of the
        # sample to an existing inbound shipment cannot be done manually
        if mode != "view":
            return "invisible"

        # In view mode, do not display the field unless it has a value set
        if not self.context.hasInboundShipment():
            return "invisible"

        return default


class OutboundShipmentFieldVisibility(SenaiteATWidgetVisibility):
    """Adapter that handles the visibility of Sample's OutboundShipment field
    """
    def __init__(self, context):
        super(OutboundShipmentFieldVisibility, self).__init__(
            context=context, sort=10, field_names=["OutboundShipment"])

    def isVisible(self, field, mode="view", default="visible"):
        """Returns the visibility of this field in a given mode
        """
        # Do not display the field if current user is client
        if api.get_current_client():
            return "invisible"

        # Display the field if mode is "add" (a sample can be directly assigned
        # to an outbound shipment on creation)
        if mode == "add":
            return "visible"

        # Do not display the field unless "view" mode. The assignment of the
        # sample to an existing shipment can only be done through "Add to
        # shipment" (ship) transition
        if mode != "view":
            return "invisible"

        # In view mode, do not display the field unless it has a value set
        if not self.context.hasOutboundShipment():
            return "invisible"

        return default
