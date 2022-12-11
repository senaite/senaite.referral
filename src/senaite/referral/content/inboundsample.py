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
from Products.CMFCore import permissions
from senaite.referral import messageFactory as _
from senaite.referral.catalog import INBOUND_SAMPLE_CATALOG
from senaite.referral.content import get_datetime_value
from senaite.referral.content import get_string_list_value
from senaite.referral.content import get_string_value
from senaite.referral.content import get_uids_field_value
from senaite.referral.content import set_datetime_value
from senaite.referral.content import set_string_list_value
from senaite.referral.content import set_string_value
from senaite.referral.content import set_uids_field_value
from senaite.referral.interfaces import IInboundSample
from senaite.referral.utils import get_action_date
from zope import schema
from zope.interface import implementer
from zope.interface import Invalid
from zope.interface import invariant

from bika.lims import api


def is_referring_id_unique(instance, referring_id):
    """Checks whether the referring id passed-in is unique
    """
    query = {"portal_type": "InboundSample", "referring_id": referring_id }
    brains = api.search(query, catalog=INBOUND_SAMPLE_CATALOG)
    if not brains:
        return True
    elif len(brains) > 1:
        return False

    obj = api.get_object(brains[0])
    return obj == instance


class IInboundSampleSchema(model.Schema):
    """InboundSample content type schema
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

    referring_id = schema.TextLine(
        title=_(u"label_inboundsample_referring_id", default=u"Original ID"),
        description=_(
            u"Unique sample identifier provided by the referring laboratory. "
            u"This ID is later stored as the Sample Client ID when the sample "
            u"is received at the laboratory. This ID can be used then by the "
            u"referring laboratory's LIMS system to identify the sample sent "
            u"earlier"
        ),
        required=True,
    )

    date_sampled = schema.Datetime(
        title=_(u"label_inboundsample_date_sampled", default=u"Date sampled"),
        description=_(
            u"Date and time when the sample was originally collected, either "
            u"by the referring laboratory itself or by the client who sent the "
            u"sample to the referring laboratory"
        ),
        required=True,
    )

    sample_type = schema.TextLine(
        title=_(u"label_inboundsample_sample_type", default=u"Sample Type"),
        description=_(
            u"Name or identifier provided by the referring laboratory for the "
            u"type of the sample. This name or identifier will be used to find "
            u"a sample type counterpart in current instance when receiving "
            u"the sample"
        ),
        required=True,
    )

    priority = schema.TextLine(
        title=_(u"label_inboundsample_priority", default=u"Priority"),
        description=_(
            u"The priority of the original sample in the referring laboratory"
        ),
        required=True,
    )

    analyses = schema.List(
        title=_(u"label_inboundsample_analyses", default=u"Analyses"),
        description=_(
            u"List of names or identifiers of tests/analyses provided by the "
            u"referring laboratory that have to be carried out by the current "
            u"laboratory. These names or identifiers will be used to find "
            u"counterpart analysis services in current instance when receiving "
            u"the sample"
        )
    )

    # TODO 2.x Replace schema.List by senaite.core.schema.UIDReferenceField
    directives.omitted("sample")
    sample = schema.List(
        title=_(u"label_inboundsample_sample", default=u"Sample"),
        description=_(
            u"Sample record automatically generated in current instance after "
            u"receiving the inbound sample"
        )
    )

    @invariant
    def validate_referring_id(data):
        """Checks if the value for field referring_id is valid
        """
        referring_id = data.referring_id

        # https://community.plone.org/t/dexterity-unique-field-validation
        context = getattr(data, "__context__", None)
        if context is not None:
            if context.referring_id == referring_id:
                # nothing changed
                return

        # Check uniqueness
        if not is_referring_id_unique(context, referring_id):
            raise Invalid(_("Referring ID must be unique"))


@implementer(IInboundSample, IInboundSampleSchema)
class InboundSample(Container):
    """Sample sent by a referring laboratory through an Inbound Sample Shipment
    """

    _catalogs = [INBOUND_SAMPLE_CATALOG, ]

    security = ClassSecurityInfo()
    exclude_from_nav = True

    def Title(self):
        """Returns the unique ID provided by the referring laboratory
        """
        referring_id = self.getReferringID()
        return referring_id.encode("utf8")

    @security.protected(permissions.View)
    def getInboundShipment(self):
        """Returns the inbound shipment this inbound sample belongs to
        """
        shipment = api.get_parent(self)
        return shipment

    @security.protected(permissions.View)
    def getReferringLaboratory(self):
        """Returns the laboratory that referred the shipment this inbound
        sample belongs to
        """
        shipment = self.getInboundShipment()
        return shipment.getReferringLaboratory()

    @security.protected(permissions.View)
    def getReferringID(self):
        """Returns the unique ID provided by the referring laboratory for this
        inbound sample
        """
        return get_string_value(self, "referring_id")

    @security.protected(permissions.ModifyPortalContent)
    def setReferringID(self, value):
        """Sets the unique ID provided by the referring laboratory for this
        inbound sample
        """
        # Check uniqueness
        if value and not is_referring_id_unique(self, value):
            raise ValueError("Referring ID must be unique")
        set_string_value(self, "referring_id", value)

    @security.protected(permissions.View)
    def getDateSampled(self):
        """Returns the date when the sample was originally collected, either by
        the referring laboratory or by the client of the referring laboratory
        """
        return get_datetime_value(self, "date_sampled")

    @security.protected(permissions.ModifyPortalContent)
    def setDateSampled(self, value):
        """Sets the date when the sample was originally collected, either by the
        referring laboratory or by the client of the referring laboratory
        """
        set_datetime_value(self, "date_sampled", value)

    @security.protected(permissions.View)
    def getSampleType(self):
        """Returns the name or identifier provided by the referring laboratory
        for the type of the inbound sample
        """
        return get_string_value(self, "sample_type")

    @security.protected(permissions.ModifyPortalContent)
    def setSampleType(self, value):
        """Sets the name or identifier provided by the referring laboratory for
        the type of the inbound sample
        """
        set_string_value(self, "sample_type", value)

    @security.protected(permissions.View)
    def getPriority(self):
        """Returns the priority of the sample in the referring laboratory
        """
        return get_string_value(self, "priority")

    @security.protected(permissions.ModifyPortalContent)
    def setPriority(self, value):
        """Sets the priority of the sample in the referring laboratory
        """
        set_string_value(self, "priority", value)

    @security.protected(permissions.View)
    def getAnalyses(self):
        """Returns the list of names or identifiers of tests/analyses provided
        by the referring laboratory that have to be carried out by the current
        laboratory
        """
        return get_string_list_value(self, "analyses")

    @security.protected(permissions.ModifyPortalContent)
    def setAnalyses(self, value):
        """Sets the list of names or identifiers of tests/analyses provided by
        the referring laboratory that have to be carried out by the current
        laboratory
        """
        set_string_list_value(self, "analyses", value)

    @security.protected(permissions.View)
    def getSample(self):
        """Returns the AnalysisRequest object type counterpart in current
        instance, if any
        """
        uid = self.getRawSample()
        if not api.is_uid(uid):
            return None
        return api.get_object(uid, default=None)

    @security.protected(permissions.View)
    def getRawSample(self):
        """Returns the UID of the AnalysisRequest counterpart in current
        instance, if any
        """
        value = get_uids_field_value(self, "sample")
        if not value:
            return None
        return value[0]

    @security.protected(permissions.ModifyPortalContent)
    def setSample(self, value):
        """Sets the AnalysisRequest object type counterpart in current instance
        once the inbound sample has been received
        """
        set_uids_field_value(self, "sample", value)

    @security.protected(permissions.View)
    def getDateCreated(self):
        """Returns the datetime when this inbound sample was created
        """
        return self.created()

    @security.protected(permissions.View)
    def getDateReceived(self):
        """Returns the datetime when this inbound sample was received or None
        """
        return get_action_date(self, "receive_inbound_sample", default=None)

    @security.protected(permissions.View)
    def getDateRejected(self):
        """Returns the datetime when this inbound sample was rejected or None
        """
        return get_action_date(self, "reject_inbound_sample", default=None)
