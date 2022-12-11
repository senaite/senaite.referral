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

from plone.app.registry.browser.controlpanel import ControlPanelFormWrapper
from plone.app.registry.browser.controlpanel import RegistryEditForm
from plone.z3cform import layout
from senaite.referral import messageFactory as _
from zope import schema
from zope.interface import Interface


class IReferralControlPanel(Interface):
    """Control panel Settings for senaite.referral
    """

    code = schema.TextLine(
        title=_(u"label_referral_code", default=u"Code"),
        description=_(
            u"Unique code of current instance's laboratory. This unique code "
            u"is used by reference laboratories to identify this laboratory as "
            u"a valid sample referrer."
        ),
        required=True,
    )

    manual_inbound_permitted = schema.Bool(
        title=_(u"label_referral_manual_inbound_permitted",
                default=u"Allow manual creation of Inbound Shipments"),
        description=_(
            u"Whether the manual creation of inbound sample shipments is "
            u"permitted. If not enabled, the creation of inbound shipments "
            u"will only be possible via POST requests by referral laboratories"
        ),
        default=False,
        required=False,
    )

    barcodes_preview_reception = schema.Bool(
        title=_(u"label_barcodes_preview_reception",
                default=u"Show barcode labels preview on shipment reception"),
        description=_(
            u"Whether the system must redirect the user to the barcode "
            u"stickers preview when receiving samples from an incoming "
            u"shipment"
        ),
        default=False,
        required=False,
    )


class ReferralControlPanelForm(RegistryEditForm):
    schema = IReferralControlPanel
    schema_prefix = "senaite.referral"
    label = _("Referral Settings")


ReferralControlPanelView = layout.wrap_form(ReferralControlPanelForm,
                                            ControlPanelFormWrapper)
