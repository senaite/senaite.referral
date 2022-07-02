# -*- coding: utf-8 -*-

from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.queue import api as qapi


class InboundShipmentViewlet(ViewletBase):
    """Print a viewlet to display a message stating that the current shipment
    is queued or being processed by a queue consumer
    """
    index = ViewPageTemplateFile("templates/queued_shipment.pt")

    def __init__(self, context, request, view, manager=None):
        super(InboundShipmentViewlet, self).__init__(
            context, request, view, manager=manager)
        self.context = context
        self.request = request
        self.view = view

    def is_visible(self):
        """Returns whether this viewlet must be visible or not
        """
        return qapi.is_queued(self.context)
