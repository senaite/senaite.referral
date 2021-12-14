# -*- coding: utf-8 -*-
from plone.dexterity.content import Item
from plone.supermodel import model
from senaite.referral import messageFactory as _
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.utils import get_action_date
from zope import schema
from zope.interface import implementer
from zope.interface import invariant

from bika.lims import api


def check_reference_laboratory(thing):
    """Checks if the reference laboratory passed in is valid
    """
    obj = api.get_object(thing, default=None)
    if not IExternalLaboratory.providedBy(obj):
        raise ValueError("Type is not supported: {}".format(repr(obj)))

    if not obj.get_reference():
        # The external laboratory must be enabled as reference laboratory
        raise ValueError("The external laboratory cannot act as a "
                         "reference laboratory")

    return True


class IOutboundSampleShipmentSchema(model.Schema):
    """OutboundSampleShipment content schema
    """

    reference_laboratory = schema.Choice(
        title=_(u"label_outboundsampleshipment_reference_laboratory",
                default=u"Destination reference laboratory"),
        description=_(u"The external reference laboratory where the shipment "
                      u"has to be sent"),
        vocabulary="senaite.referral.vocabularies.referencelaboratories",
        required=True,
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

    created_datetime = schema.Datetime(
        title=_(u"label_outboundsampleshipment_created_datetime",
                default=u"Created"),
        description=_(
            u"Date and time when the shipment was created"
        ),
        # Automatically set, see property
        readonly=True
    )

    dispatched_datetime = schema.Datetime(
        title=_(u"label_outboundsampleshipment_dispatched_datetime",
                default=u"Dispatched"),
        description=_(
            u"Date and time when the shipment was dispatched to the reference "
            u"laboratory"
        ),
        # Automatically set, see property
        readonly=True
    )

    delivered_datetime = schema.Datetime(
        title=_(u"label_outboundsampleshipment_delivered_datetime",
                default=u"Delivered"),
        description=_(
            u"Date and time when the shipment was physically delivered to the "
            u"reference laboratory"
        ),
        # Automatically set, see property
        readonly=True
    )

    rejected_datetime = schema.Datetime(
        title=_(u"label_outboundsampleshipment_rejected_datetime",
                default=u"Delivered"),
        description=_(
            u"Date and time when the shipment was rejected"
        ),
        # Automatically set, see property
        readonly=True
    )

    @invariant
    def validate_reference_laboratory(data):
        """Checks if the value for field referring_laboratory is valid
        """
        val = data.reference_laboratory
        if not val:
            return
        check_reference_laboratory(val)


@implementer(IInboundSampleShipment, IOutboundSampleShipmentSchema)
class OutboundSampleShipment(Item):
    """Single physical package containing one or more samples to be sent to an
    external reference laboratory
    """
    _catalogs = ["portal_catalog", ]

    @property
    def shipment_id(self):
        """The unique ID of this outbound shipment object
        """
        return api.get_id(self)

    @property
    def created_datetime(self):
        """The datetime when this object was created/registered in the system
        """
        return api.get_creation_date(self)

    @property
    def dispatched_datetime(self):
        """The datetime when this object was dispatched
        """
        return get_action_date(self, "dispatch", default=None)

    @property
    def delivered_datetime(self):
        """The datetime when this object was delivered
        """
        return get_action_date(self, "deliver", default=None)

    @property
    def rejected_datetime(self):
        """The datetime when this object was rejected
        """
        return get_action_date(self, "reject", default=None)

    def get_reference_laboratory(self):
        lab = self.reference_laboratory
        if not lab:
            return u""
        return lab

    def set_reference_laboratory(self, value):
        if api.is_object(value):
            value = api.get_uid(value)

        value = value.strip()
        if self.reference_laboratory == value:
            # nothing changed
            return

        if check_reference_laboratory(value):
            self.reference_laboratory = value

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
        return self.shipment_id

    def get_created_datetime(self):
        return self.created_datetime

    def get_dispatched_datetime(self):
        return self.dispatched_datetime

    def get_delivered_datetime(self):
        return self.delivered_datetime

    def get_rejected_datetime(self):
        return self.rejected_datetime
