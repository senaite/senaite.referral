# -*- coding: utf-8 -*-

from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed


class DispatchNotificationViewlet(ViewletBase):
    """Viewlet that displays information about the dispatch notification of the
    current OutboundShipment to the reference laboratory
    """
    index = ViewPageTemplateFile("templates/dispatch_notification.pt")

    _notification_response = None

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        if self.get_notification_response():
            return True
        return False

    def get_notification_response(self):
        if not self._notification_response:
            response = self.context.get_dispatch_notification_info()
            self._notification_response = response
        return self._notification_response

    def is_error(self):
        """Returns whether the dispatch notification errored
        """
        response = self.get_notification_response()
        return not response.get("success", False)

    def get_message(self):
        response = self.get_notification_response()
        return response.get("message")

    def get_status_code(self):
        response = self.get_notification_response()
        return response.get("status")
