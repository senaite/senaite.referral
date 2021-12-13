# -*- coding: utf-8 -*-
from plone.dexterity.content import Item
from plone.supermodel import model
from senaite.referral import messageFactory as _
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.interfaces import IInboundSampleShipment
from zope import schema
from zope.interface import implementer
from zope.interface import invariant

from bika.lims import api


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


class IInboundSampleShipmentSchema(model.Schema):
    """InboundSampleShipment content schema
    """

    referring_laboratory = schema.Choice(
        title=_(u"label_inboundsampleshipment_referring_laboratory",
                default=u"Referring laboratory"),
        description=_(u"The referring laboratory the samples come from"),
        vocabulary="senaite.referral.vocabularies.referringlaboratories",
        required=True,
    )

    comments = schema.TextLine(
        title=_(u"label_inboundsampleshipment_comments",
                default=u"Comments"),
        description=_(
            u"Additional comments provided by the referring laboratory"
        ),
        required=False,
    )

    shipment_id = schema.TextLine(
        title=_(u"label_inboundsampleshipment_shipment_id",
                default=u"Shipment ID"),
        description=_(
            u"Unique identifier provided by the referring laboratory"
        ),
        required=True,
    )

    dispatch_datetime = schema.Datetime(
        title=_(u"label_inboundsampleshipment_dispatch_datetime",
                default=u"Dispatched"),
        description=_(
            u"Date and time when the shipment was dispatched by the referring "
            u"laboratory"
        ),
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
    def validate_dispatch_datetime(data):
        """Checks if the value for field dispatch_datetime is valid
        """
        val = data.dispatch_datetime
        if not val:
            return

        val = api.to_date(val)
        if not val:
            raise ValueError("Dispatch date time is not valid")


@implementer(IInboundSampleShipment, IInboundSampleShipmentSchema)
class InboundSampleShipment(Item):
    """Single physical package containing one or more samples sent from a
    referring laboratory
    """
    _catalogs = ["portal_catalog", ]

    def get_referring_laboratory(self):
        lab = self.referring_laboratory
        if not lab:
            return u""
        return lab

    def set_referring_laboratory(self, value):
        if api.is_object(value):
            value = api.get_uid(value)

        value = value.strip()
        if self.referring_laboratory == value:
            # nothing changed
            return

        if check_referring_laboratory(value):
            self.referring_laboratory = value

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

    def get_dispatch_datetime(self):
        dispatch_datetime = self.dispatch_datetime
        if not dispatch_datetime:
            return u""
        return dispatch_datetime

    def set_dispatch_datetime(self, value):
        value = api.to_date(value)
        if not value:
            raise ValueError("Dispatch date time is not valid")
        self.dispatch_datetime = value
