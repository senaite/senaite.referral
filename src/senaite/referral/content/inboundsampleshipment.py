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
from bika.lims import api
from plone.autoform import directives
from plone.supermodel import model
from Products.CMFCore import permissions
from senaite.core.catalog import CLIENT_CATALOG
from senaite.core.catalog import CONTACT_CATALOG
from senaite.core.content.base import Container
from senaite.core.schema import UIDReferenceField
from senaite.core.z3cform.widgets.uidreference import UIDReferenceWidgetFactory
from senaite.referral import messageFactory as _
from senaite.referral.catalog import SHIPMENT_CATALOG
from senaite.referral.content import get_datetime_value
from senaite.referral.content import get_string_value
from senaite.referral.content import set_datetime_value
from senaite.referral.content import set_string_value
from senaite.referral.interfaces import IInboundSample
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.utils import get_action_date
from zope import schema
from zope.interface import implementer
from zope.interface import invariant


class IInboundSampleShipmentSchema(model.Schema):
    """InboundSampleShipment content schema
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

    shipment_id = schema.TextLine(
        title=_(u"label_inboundsampleshipment_shipment_id",
                default=u"Shipment ID"),
        description=_(
            u"Unique identifier provided by the referring laboratory"
        ),
        required=True,
    )

    referring_client = UIDReferenceField(
        title=_(u"label_inboundsampleshipment_referring_client",
                default=u"Referring client"),
        description=_(u"The referring client the samples come from"),
        allowed_types=("Client", ),
        multi_valued=False,
        required=True,
    )

    directives.widget(
        "referring_client",
        UIDReferenceWidgetFactory,
        catalog=CLIENT_CATALOG,
        query={
            "portal_type": "Client",
            "is_active": True,
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        },
        limit=15,
    )

    default_contact = UIDReferenceField(
        title=_(u"label_inboundsampleshipment_default_contact",
                default=u"Default contact"),
        description=_(
            u"The default contact for the samples come from"
        ),
        allowed_types=("Contact",),
        multi_valued=False,
        required=True,
    )

    directives.widget(
        "default_contact",
        UIDReferenceWidgetFactory,
        catalog=CONTACT_CATALOG,
        query="get_contacts_query",
        limit=15,
    )

    comments = schema.Text(
        title=_(u"label_inboundsampleshipment_comments",
                default=u"Comments"),
        description=_(
            u"Additional comments provided by the referring laboratory"
        ),
        required=False,
    )

    dispatched_datetime = schema.Datetime(
        title=_(u"label_inboundsampleshipment_dispatched_datetime",
                default=u"Dispatched"),
        description=_(
            u"Date and time when the shipment was dispatched by the referring "
            u"laboratory"
        ),
        required=True,
    )

    @invariant
    def validate_dispatched_datetime(data):
        """Checks if the value for field dispatch_datetime is valid
        """
        val = data.dispatched_datetime
        if not val:
            return

        val = api.to_date(val)
        if not val:
            raise ValueError("Dispatched date time is not valid")

    @invariant
    def validate_referring(data):
        """Checks if the referring client and default contact are set
        """
        request = api.get_request()
        client = request.form.get("form.widgets.referring_client")
        contact = request.form.get("form.widgets.default_contact")

        if api.is_uid(client) and api.is_uid(contact):
            return

        msg = _("Please set the default client and contact to use when "
                "creating samples from this referring laboratory first")
        raise ValueError(msg)


@implementer(IInboundSampleShipment, IInboundSampleShipmentSchema)
class InboundSampleShipment(Container):
    """Single physical package containing one or more samples sent from a
    referring laboratory
    """
    _catalogs = [SHIPMENT_CATALOG, ]
    exclude_from_nav = True
    security = ClassSecurityInfo()

    @security.private
    def get_contacts_query(self):
        """Return the query for the Contact field
        """
        query = {
            "portal_type": "Contact",
            "is_active": True,
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        }

        # Get contacts belong to referring client if it is set
        referring_client = getattr(self, "referring_client", None)
        if referring_client:
            client_uid = referring_client[0]
            query["path"] = {
                "query": api.get_path(api.get_object_by_uid(client_uid)),
                "level": 0
            }
        return query

    def _get_title(self):
        return self.getShipmentID()

    def _set_title(self, title):
        return

    title = property(_get_title, _set_title)

    @security.protected(permissions.ModifyPortalContent)
    def setComments(self, value):
        """Sets the comment text for this Inbound Shipment
        """
        set_string_value(self, "comments", value)

    @security.protected(permissions.View)
    def getComments(self):
        """Returns the comments for this Inbound shipment
        """
        return get_string_value(self, "comments")

    @security.protected(permissions.ModifyPortalContent)
    def setShipmentID(self, value):
        """Sets the unique identifier provided by the referring laboratory
        """
        set_string_value(self, "shipment_id", value)

    @security.protected(permissions.View)
    def getShipmentID(self):
        """Returns the unique identifier provided by the referring laboratory
        """
        return get_string_value(self, "shipment_id")

    @security.protected(permissions.ModifyPortalContent)
    def setDispatchedDateTime(self, value):
        """Sets the datetime when the shipment was dispatched from the referral
        laboratory
        """
        set_datetime_value(self, "dispatched_datetime", value)

    @security.protected(permissions.View)
    def getDispatchedDateTime(self):
        """Returns the datetime when the shipment was dispatched from the
        referral laboratory
        """
        return get_datetime_value(self, "dispatched_datetime")

    @security.protected(permissions.View)
    def getReceivedDateTime(self):
        """Returns the datetime when this shipment was received or None
        """
        return get_action_date(self, "receive_inbound_shipment", default=None)

    @security.protected(permissions.View)
    def getRejectedDateTime(self):
        """Returns the datetime when this shipment was rejected or None
        """
        return get_action_date(self, "reject_inbound_shipment", default=None)

    @security.protected(permissions.View)
    def getCancelledDateTime(self):
        """Returns the datetime when this shipment was rejected or None
        """
        return get_action_date(self, "cancel", default=None)

    @security.protected(permissions.View)
    def getReferringLaboratory(self):
        """Returns the client the samples come from
        """
        return api.get_parent(self)

    @security.protected(permissions.ModifyPortalContent)
    def setReferringClient(self, value):
        """Sets the default client the samples from inbound shipments will
        be assigned to
        """
        mutator = self.mutator("referring_client")
        mutator(self, value)

    @security.protected(permissions.View)
    def getReferringClient(self):
        """Returns the default client that samples from inbound shipments from
        this laboratory will be assigned to
        """
        accessor = self.accessor("referring_client")
        return accessor(self)

    @security.protected(permissions.View)
    def getRawReferringClient(self):
        """Returns the UID of the default client that samples from inbound
        shipments from this laboratory will be assigned to
        """
        accessor = self.accessor("referring_client", raw=True)
        return accessor(self)

    @security.protected(permissions.View)
    def getInboundSamples(self):
        """Returns the inbound samples assigned to this inbound sample shipment
        """
        samples = self.objectValues() or []
        return filter(IInboundSample.providedBy, samples)

    @security.protected(permissions.View)
    def getRawSamples(self):
        """Returns the UIDs of samples generated because of the partial or fully
        reception of inbound samples assigned to this inbound shipment
        """
        uids = [samp.getRawSample() for samp in self.getInboundSamples()]
        return filter(api.is_uid, uids)

    @security.protected(permissions.View)
    def getSamples(self):
        """Returns the samples generated because of the partial or fully
        reception of inbound samples assigned to this inbound shipment
        """
        uids = filter(None, self.getRawSamples())
        if not uids:
            return []
        query = {"UID": uids}
        samples = api.search(query, "uid_catalog")
        return [api.get_object(sample) for sample in samples]

    @security.protected(permissions.ModifyPortalContent)
    def setDefaultContact(self, value):
        """Sets the default contact the samples from inbound shipments will
        be assigned to
        """
        mutator = self.mutator("default_contact")
        mutator(self, value)

    @security.protected(permissions.View)
    def getDefaultContact(self):
        """Returns the default contact that samples from inbound shipments from
        this laboratory will be assigned to
        """
        accessor = self.accessor("default_contact")
        return accessor(self)

    @security.protected(permissions.View)
    def getRawDefaultContact(self):
        """Returns the UID of the default contact that samples from inbound
        shipments from this laboratory will be assigned to
        """
        accessor = self.accessor("default_contact", raw=True)
        return accessor(self)
