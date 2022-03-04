# -*- coding: utf-8 -*-

from AccessControl import ClassSecurityInfo
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from Products.CMFCore import permissions
from senaite.referral import messageFactory as _
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.utils import get_action_date
from senaite.referral.utils import get_uids_field_value
from senaite.referral.utils import set_uids_field_value
from zope import schema
from zope.interface import implementer
from zope.interface import invariant

from bika.lims import api
from bika.lims.interfaces import IClient


def check_referring_laboratory(thing):
    """Checks if the referring laboratory passed in is valid
    """
    obj = api.get_object(thing, default=None)
    if not IExternalLaboratory.providedBy(obj):
        raise ValueError("Type is not supported: {}".format(repr(obj)))

    if not obj.get_referring():
        # The external laboratory must be enabled as referring laboratory
        raise ValueError("The external laboratory cannot act as a "
                         "referring laboratory")

    return True


def check_referring_client(thing):
    """Checks if the referring client passed in is valid
    """
    obj = api.get_object(thing, default=None)
    if not IClient.providedBy(obj):
        raise ValueError("Type is not supported: {}".format(repr(obj)))

    return True


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

    referring_laboratory = schema.Choice(
        title=_(u"label_inboundsampleshipment_referring_laboratory",
                default=u"Referring laboratory"),
        description=_(u"The referring laboratory the samples come from"),
        vocabulary="senaite.referral.vocabularies.referringlaboratories",
        required=True,
    )

    referring_client = schema.Choice(
        title=_(u"label_inboundsampleshipment_referring_client",
                default=u"Referring client"),
        description=_(u"The referring client the samples come from"),
        vocabulary="senaite.referral.vocabularies.clients",
        required=True,
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

    directives.omitted("samples")
    samples = schema.List(
        title=_(u"Samples"),
        required=True,
    )

    @invariant
    def validate_referring_laboratory(data):
        """Checks if the value for field referring_laboratory is valid
        """
        val = data.referring_laboratory
        if not val:
            return
        check_referring_laboratory(val)

    @invariant
    def validate_referring_client(data):
        """Checks if the value for field referring_client is valid
        """
        val = data.referring_client
        if not val:
            return
        check_referring_client(val)

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


@implementer(IInboundSampleShipment, IInboundSampleShipmentSchema)
class InboundSampleShipment(Container):
    """Single physical package containing one or more samples sent from a
    referring laboratory
    """
    _catalogs = ["portal_catalog", ]

    security = ClassSecurityInfo()
    exclude_from_nav = True

    def _get_title(self):
        code = self.get_shipment_id()
        return code.encode("utf-8")

    def _set_title(self, title):
        return

    title = property(_get_title, _set_title)

    @security.private
    def accessor(self, fieldname):
        """Return the field accessor for the fieldname
        """
        schema = api.get_schema(self)
        if fieldname not in schema:
            return None
        return schema[fieldname].get

    @security.private
    def mutator(self, fieldname):
        """Return the field mutator for the fieldname
        """
        schema = api.get_schema(self)
        if fieldname not in schema:
            return None
        return schema[fieldname].set

    def get_comments(self):
        comments = self.comments
        if not comments:
            return u""
        return comments

    def set_comments(self, value):
        value = value.strip()
        if self.comments == value:
            # nothing changed
            return
        self.comments = value

    def get_shipment_id(self):
        shipment_id = self.shipment_id
        if not shipment_id:
            return u""
        return shipment_id

    def set_shipment_id(self, value):
        value = value.strip()
        if self.shipment_id == value:
            # nothing changed
            return
        self.shipment_id = value

    def get_dispatched_datetime(self):
        """Returns the datetime when the shipment was dispatched from the
        referral laboratory
        """
        dispatched_datetime = self.dispatched_datetime
        if not dispatched_datetime:
            return u""
        return dispatched_datetime

    def set_dispatched_datetime(self, value):
        """Sets the datetime when the shipment was dispatched from the referral
        laboratory
        """
        value = api.to_date(value)
        if not value:
            raise ValueError("Dispatch date time is not valid")
        self.dispatched_datetime = value

    def get_received_datetime(self):
        """Returns the datetime when this shipment was received or None
        """
        return get_action_date(self, "receive_inbound_shipment", default=None)

    def get_rejected_datetime(self):
        """Returns the datetime when this shipment was rejected or None
        """
        return get_action_date(self, "reject_inbound_shipment", default=None)

    def get_cancelled_datetime(self):
        """Returns the datetime when this shipment was rejected or None
        """
        return get_action_date(self, "cancel", default=None)

    def get_samples(self):
        """Returns the list of samples assigned to this shipment. Samples can
        either be UIDs (for when shipment has been received) or dicts (when
        shipment has not been received yet):
        """
        samples = self.samples
        if not samples:
            return []
        return samples

    def set_samples(self, value):
        """Assigns the samples assigned to this shipment
        """
        if not isinstance(value, (list, tuple)):
            value = [value]
        self.samples = value

    @security.protected(permissions.View)
    def getReferringLaboratory(self):
        """Returns the client the samples come from
        """
        value = get_uids_field_value(self, "referring_laboratory")
        if not value:
            return None
        return value[0]

    @security.protected(permissions.ModifyPortalContent)
    def setReferringLaboratory(self, value):
        """Sets the client the samples come from
        """
        set_uids_field_value(self, "referring_laboratory", value,
                             validator=check_referring_laboratory)

    @security.protected(permissions.View)
    def getReferringClient(self):
        """Returns the client the samples come from
        """
        value = get_uids_field_value(self, "referring_client")
        if not value:
            return None
        return value[0]

    @security.protected(permissions.ModifyPortalContent)
    def setReferringClient(self, value):
        """Sets the client the samples come from
        """
        set_uids_field_value(self, "referring_client", value,
                             validator=check_referring_client)
