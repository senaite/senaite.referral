# -*- coding: utf-8 -*-

from plone.app.layout.viewlets import ViewletBase
from plone.memoize import view
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.notifications import get_last_post

from bika.lims import api


class PostNotificationViewlet(ViewletBase):
    """Viewlet that displays information about the POST notification about
    current object to a target laboratory
    """
    index = ViewPageTemplateFile("templates/post_notification.pt")

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        if not api.is_object(self.context):
            return False

        elif IInboundSampleShipment.providedBy(self.context):
            # There is a InboundSampleShipment-specific viewlet that takes
            # the samples from the shipment into account already
            if self.is_error():
                return True

            samples = self.context.getSamples()
            posts = filter(None, [get_last_post(sample) for sample in samples])
            return not posts

        elif self.get_notification():
            return True

        return False

    @view.memoize
    def get_notification(self):
        return get_last_post(self.context)

    def is_error(self):
        post = self.get_notification()
        if not post:
            return False
        return not post.get("success", False)
