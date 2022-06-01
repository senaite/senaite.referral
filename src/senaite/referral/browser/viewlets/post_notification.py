# -*- coding: utf-8 -*-

from bika.lims import api
from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed
from senaite.referral.notifications import get_last_post


class PostNotificationViewlet(ViewletBase):
    """Viewlet that displays information about the POST notification about
    current object to a target laboratory
    """
    index = ViewPageTemplateFile("templates/post_notification.pt")

    _notification = None

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        if not api.is_object(self.context):
            return False
        if self.get_notification():
            return True
        return False

    def get_notification(self):
        if not self._notification:
            post = get_last_post(self.context)
            self._notification = post
        return self._notification

    def is_error(self):
        post = self.get_notification()
        return not post.get("success", False)
