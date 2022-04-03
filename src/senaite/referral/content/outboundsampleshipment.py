# -*- coding: utf-8 -*-

import json
import re
import six
from AccessControl import ClassSecurityInfo
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from Products.CMFCore import permissions
from senaite.referral import messageFactory as _
from senaite.referral.interfaces import IOutboundSampleShipment
from senaite.referral.utils import get_action_date
from zope import schema
from zope.interface import implementer

from bika.lims import api


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

    directives.omitted("dispatch_notification_datetime")
    dispatch_notification_datetime = schema.Datetime(
        title=_(u"Datetime when shipment was notified to reference lab"),
        readonly=True,
        required=False,
    )

    directives.omitted("dispatch_notification_payload")
    dispatch_notification_payload = schema.SourceText(
        title=_(u"Shipment notification payload"),
        readonly=True,
        required=False,
    )

    directives.omitted("dispatch_notification_response")
    dispatch_notification_response = schema.SourceText(
        title=_(u"Shipment notification response"),
        readonly=True,
        required=False,
    )


@implementer(IOutboundSampleShipment, IOutboundSampleShipmentSchema)
class OutboundSampleShipment(Container):
    """Single physical package containing one or more samples to be sent to an
    external reference laboratory
    """
    _catalogs = ["portal_catalog", ]
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
        """Returns the datetime when this shipment was created in the system
        """
        return api.get_creation_date(self)

    def get_dispatched_datetime(self):
        """Returns the datetime when this shipment was dispatched to the
        destination reference laboratory
        """
        return get_action_date(self, "dispatch_outbound_shipment", default=None)

    def get_delivered_datetime(self):
        """Returns the datetime when this shipment was delivered on the
        destination reference laboratory
        """
        return get_action_date(self, "deliver_outbound_shipment", default=None)

    def get_lost_datetime(self):
        """Returns the datetime when this shipment was labeled as lost
        """
        return get_action_date(self, "lose_outbound_shipment", default=None)

    def get_rejected_datetime(self):
        """Returns the datetime when this shipment was rejected or None
        """
        return get_action_date(self, "reject_outbound_shipment", default=None)

    def get_cancelled_datetime(self):
        """Returns the datetime when this shipment was rejected or None
        """
        return get_action_date(self, "cancel_outbound_shipment", default=None)

    def get_samples(self):
        """Returns the list of sample uids assigned to this shipment
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

        self.samples = []
        map(self.add_sample, value)

    def get_dispatch_notification_datetime(self):
        """Returns the datetime when the reference laboratory was notified
        about this outbound shipment. Returns None if the reference laboratory
        has never been notified about this shipment
        """
        dispatch_notification_datetime = self.dispatch_notification_datetime
        if not dispatch_notification_datetime:
            return None
        return dispatch_notification_datetime

    def set_dispatch_notification_datetime(self, value):
        """Sets the datetime when the reference laboratory was notified
        about this outbound shipment. A None value means the reference lab has
        not been notified at all
        """
        if self.dispatch_notification_datetime == value:
            # nothing changed
            return
        self.dispatch_notification_datetime = value

    def get_dispatch_notification_payload(self):
        """Returns the payload sent to the reference laboratory when this
        outbound shipment was notified
        """
        dispatch_notification_payload = self.dispatch_notification_payload
        if not dispatch_notification_payload:
            return u""
        return dispatch_notification_payload

    def set_dispatch_notification_payload(self, value):
        """Sets the payload sent to the referecne laboratory when this outbound
        shipment was notified
        """
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        elif not value:
            value = u""
        elif not isinstance(value, six.string_types):
            value = repr(value)

        if self.dispatch_notification_payload == value:
            # nothing changed
            return
        self.dispatch_notification_payload = value

    def get_dispatch_notification_response(self):
        """Returns the response from the reference lab once notified
        """
        dispatch_notification_response = self.dispatch_notification_response
        if not dispatch_notification_response:
            return u""
        return dispatch_notification_response

    def set_dispatch_notification_response(self, value):
        """Sets the response from the reference lab once notified
        """
        if self.dispatch_notification_response == value:
            # nothing changed
            return
        self.dispatch_notification_response = value

    def get_dispatch_notification_info(self):
        response = self.get_dispatch_notification_response()
        if not response:
            return None

        match = re.match(r"^\[(\d+)]\s(.*)", response)
        if not match:
            return None

        groups = match.groups()
        if len(groups) < 2:
            return None

        status = groups[0]
        response = groups[1]
        try:
            response = json.loads(response)
        except ValueError:
            # Not JSON deserializable!
            response = {"message": response, "success": status == "200"}

        response.update({"status": status})
        return response

    def get_dispatch_notification_error(self):
        """Returns the error from the response of the reference lab, if any
        """
        error = None
        response = self.get_dispatch_notification_info()
        if response and not response.get("success", False):
            msg = response.get("message", "Unknown error")
            status = response.get("status")
            error = "[{}] {}".format(status, msg)

        return error

    def add_sample(self, value):
        """Adds a sample to this shipment
        """
        if not value:
            return

        samples = self.samples or []
        sample_uid = api.get_uid(value)
        if sample_uid not in samples:
            samples.append(sample_uid)
            self.samples = samples

    def remove_sample(self, value):
        """Removes a sample from this shipment
        """
        if not value:
            return

        samples = self.samples or []
        sample_uid = api.get_uid(value)
        if sample_uid in samples:
            samples.pop(sample_uid)
            self.samples = samples

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
