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
from senaite.referral.vocabularies.outboundsamples import \
    OUTBOUND_SAMPLES_ORDER_VOCABULARY_ID
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

    chunk_size_receive_inbound_sample = schema.Int(
        title=_(
            u"label_chunk_size_receive_inbound_sample",
            u"Maximum number of inbound samples to receive in a single task"
        ),
        description=_(
            u"description_chunk_size_receive_inbound_sample",
            u"If the number of inbound samples to receive is above this "
            u"value, the queue will split the job in as many tasks as "
            u"required. If the value is 0 or senaite queue is not installed, "
            u"the system won't process the inbound samples asynchronously and "
            u"all them will be held in a single request"
        ),
        default=5,
        required=0,
    )

    outbound_samples_order = schema.Choice(
        title=_(
            u"label_referral_outbound_samples_order",
            default=u"Default sorting order for samples in outbound shipments"
        ),
        description=_(
            u"description_referral_outbound_samples_order",
            default=u"The default sorting strategy to use when adding samples "
                    u"to an outbound shipment."
        ),
        vocabulary=OUTBOUND_SAMPLES_ORDER_VOCABULARY_ID,
    )

    notify_unrequested_analyses = schema.Bool(
        title=_(
            u"label_referral_notify_unrequested_analyses",
            u"Notify the referring laboratory about unrequested analyses"
        ),
        description=_(
            u"description_referral_notify_unrequested_analyses",
            u"If selected, the results of unsolicited analyses will be sent "
            u"back to the referring laboratory after the sample is verified. "
            u"If not selected, only the results of initially requested "
            u"analyses will be shared."
        ),
        default=False,
        required=False,
    )

    notify_retested_analyses = schema.Bool(
        title=_(
            u"label_referral_notify_retested_analyses",
            u"Notify the referring laboratory about retested analyses"
        ),
        description=_(
            u"description_referral_notify_retested_analyses",
            u"If selected, the results of retested analyses will be sent back "
            u"to the referring laboratory after the sample is verified. If "
            u"not selected, only the retest results will be shared."
        ),
        default=False,
        required=False,
    )

    notify_hidden_analyses = schema.Bool(
        title=_(
            u"label_referral_notify_hidden_analyses",
            u"Notify the referring laboratory about hidden analyses"
        ),
        description=_(
            u"description_referral_notify_hidden_analyses",
            u"If selected, the results of hidden analyses will be sent back "
            u"to the referring laboratory after the sample is verified. If "
            u"not selected, the results of analyses flagged as hidden won't "
            u"be shared."
        ),
        default=False,
        required=False,
    )

    create_reference_analyses = schema.Bool(
        title=_(
            u"label_referral_create_reference_analyses",
            u"Create analyses from reference laboratory"
        ),
        description=_(
            u"description_referral_create_reference_analyses",
            u"If selected, the system will create missing analyses in the "
            u"referring laboratory when receiving a notification for results "
            u"update from the reference laboratory. Otherwise, the system "
            u"will skip results for analyses that do not exist in the "
            u"referred sample."
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
