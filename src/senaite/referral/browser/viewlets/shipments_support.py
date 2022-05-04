# -*- coding: utf-8 -*-

from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed
from senaite.referral.utils import is_valid_url


class ShipmentsSupportViewlet(ViewletBase):
    """Viewlet that notifies the user that current external laboratory does not
    support the automatic submission of shipments
    """
    index = ViewPageTemplateFile("templates/shipments_support.pt")

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        current_url = self.request.get("URL")
        if not current_url.endswith("outbound_shipments"):
            return False

        if not self.is_reference_lab():
            return True
        if not self.is_valid_lab_url():
            return True
        if not self.is_valid_credentials():
            return True
        return False

    def is_reference_lab(self):
        return self.context.getReference()

    def is_valid_lab_url(self):
        url = self.context.getUrl()
        return is_valid_url(url)

    def is_valid_credentials(self):
        username = self.context.getUsername()
        password = self.context.getPassword()
        return all([username, password])
