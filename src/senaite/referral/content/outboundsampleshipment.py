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

from AccessControl import ClassSecurityInfo
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from plone.namedfile.field import NamedBlobFile
from Products.CMFCore import permissions
from senaite.referral import messageFactory as _
from senaite.referral.catalog import SHIPMENT_CATALOG
from senaite.referral.content import mutator
from senaite.referral.content import accessor
from senaite.referral.content import get_string_value
from senaite.referral.content import get_uids_field_value
from senaite.referral.content import set_string_value
from senaite.referral.content import set_uids_field_value
from senaite.referral.interfaces import IOutboundSampleShipment
from senaite.referral.utils import get_action_date
from zope import schema
from zope.interface import implementer

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest


class IOutboundSampleShipmentSchema(model.Schema):
    """OutboundSampleShipment content schema
    """

    directives.omitted("title")
    title = schema.TextLine(
        title=u"Title",
        required=False
    )

    directives.omitted("description")
    description = schema.Text(
        title=u"Description",
        required=False
    )

    comments = schema.TextLine(
        title=_(u"label_outboundsampleshipment_comments",
                default=u"Comments"),
        required=False,
    )

    shipment_id = schema.TextLine(
        title=_(u"label_outboundsampleshipment_shipment_id",
                default=u"Shipment ID"),
        # Automatically set, see property
        readonly=True,
    )

    directives.omitted("samples")
    samples = schema.List(
        title=_(u"Samples"),
        required=True,
    )

    # Shipment manifest cannot be set manually. After a shipment is transitioned
    # to finished status, user can create the manifest in pdf format via the
    # browser view form "add_shipment_manifest". Transition "dispatch" is only
    # available after a shipment manifest is present
    directives.omitted("manifest")
    manifest = NamedBlobFile(
        title=_(u"label_outboundsampleshipment_manifest",
                default=u"Shipment Manifest"),
        required=False,
    )


def check_sample(thing):
    """Checks if the thing is an object of AnalysisRequest type
    """
    obj = api.get_object(thing, default=None)
    if not IAnalysisRequest.providedBy(obj):
        raise ValueError("Type is not supported: {}".format(repr(obj)))
    return True


@implementer(IOutboundSampleShipment, IOutboundSampleShipmentSchema)
class OutboundSampleShipment(Container):
    """Single physical package containing one or more samples to be sent to an
    external reference laboratory
    """
    _catalogs = [SHIPMENT_CATALOG, ]
    exclude_from_nav = True
    security = ClassSecurityInfo()

    @property
    def shipment_id(self):
        """The unique ID of this outbound shipment object
        """
        return api.get_id(self)

    def _get_title(self):
        return self.shipment_id.encode("utf-8")

    def _set_title(self, title):
        return

    title = property(_get_title, _set_title)

    @security.protected(permissions.ModifyPortalContent)
    def setComments(self, value):
        """Sets the comment text for this Outbound Shipment
        """
        set_string_value(self, "comments", value)

    @security.protected(permissions.View)
    def getComments(self):
        """Returns the comments for this Outbound shipment
        """
        return get_string_value(self, "comments")

    @security.protected(permissions.View)
    def getShipmentID(self):
        """Returns the unique identifier of this Outbound Shipment
        """
        return self.shipment_id

    def getCreatedDateTime(self):
        """Returns the datetime when this shipment was created in the system
        """
        return api.get_creation_date(self)

    def getDispatchedDateTime(self):
        """Returns the datetime when this shipment was dispatched to the
        destination reference laboratory
        """
        return get_action_date(self, "dispatch_outbound_shipment", default=None)

    def getDeliveredDateTime(self):
        """Returns the datetime when this shipment was delivered on the
        destination reference laboratory
        """
        return get_action_date(self, "deliver_outbound_shipment", default=None)

    def getLostDateTime(self):
        """Returns the datetime when this shipment was labeled as lost
        """
        return get_action_date(self, "lose_outbound_shipment", default=None)

    def getRejectedDateTime(self):
        """Returns the datetime when this shipment was rejected or None
        """
        return get_action_date(self, "reject_outbound_shipment", default=None)

    def getCancelledDateTime(self):
        """Returns the datetime when this shipment was rejected or None
        """
        return get_action_date(self, "cancel_outbound_shipment", default=None)

    def getRawSamples(self):
        """Returns the list of sample uids assigned to this shipment
        """
        return get_uids_field_value(self, "samples")

    def getSamples(self):
        """Returns the list of samples assigned to this shipment
        """
        uids = self.getRawSamples()
        return [api.get_object(samp) for samp in uids]

    def setSamples(self, value):
        """Assigns the samples assigned to this shipment
        """
        set_uids_field_value(self, "samples", value, validator=check_sample)

    def addSample(self, value):
        """Adds a sample to this shipment
        """
        if not value:
            return

        uids = self.getRawSamples()
        sample_uid = api.get_uid(value)
        if sample_uid in uids:
            return

        uids.append(sample_uid)
        self.setSamples(uids)

    def removeSample(self, value):
        """Removes a sample from this shipment
        """
        if not value:
            return

        uids = self.getRawSamples()
        sample_uid = api.get_uid(value)
        if sample_uid not in uids:
            return

        uids.remove(sample_uid)
        self.setSamples(uids)

    def in_preparation(self):
        """Return whether the status of the shipment is "preparation"
        """
        return api.get_review_status(self) == "preparation"

    @security.protected(permissions.View)
    def getReferenceLaboratory(self):
        """Returns the external reference laboratory where the shipment has to
        be sent
        """
        return api.get_parent(self)

    @security.protected(permissions.ModifyPortalContent)
    def setManifest(self, value):
        """Sets the manifest pdf file to this shipment
        """
        setter = mutator(self, "manifest")
        setter(self, value)

    @security.protected(permissions.View)
    def getManifest(self):
        """Returns the manifest (pdf file) assigned to this shipment
        """
        getter = accessor(self, "manifest")
        return getter(self)
