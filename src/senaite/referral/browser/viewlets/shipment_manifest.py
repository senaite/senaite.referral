# -*- coding: utf-8 -*-

from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed
from senaite.referral.browser.shipment_manifest import ShipmentManifestView

from bika.lims import api
from bika.lims.workflow import get_review_history_statuses


class ShipmentManifestViewlet(ViewletBase):
    """Viewlet displayed once an outbound shipment has been finalised, that
    prompts the user for the generation of a shipment manifest if does not
    exist yet or displays a link for the download of the document otherwise
    """
    index = ViewPageTemplateFile("templates/shipment_manifest.pt")

    @check_installed(False)
    def is_visible(self):
        """Returns whether the viewlet must be visible or not
        """
        if isinstance(self.view, ShipmentManifestView):
            # Do not display if current view is the form for generation of
            # a shipment manifest
            return False

        statuses = get_review_history_statuses(self.context)
        return "ready" in statuses

    def is_ready(self):
        """Returns whether the shipment is in ready for shipment status
        """
        return api.get_review_status(self.context) == "ready"

    def has_manifest(self):
        """Returns whether a shipment manifest has already been generated for
        this shipment
        """
        manifest = self.context.getManifest()
        if manifest:
            return True
        return False

    def get_manifest_download_url(self):
        """Returns the URL for the download of the shipment manifest file
        """
        manifest = self.context.getManifest()
        return "{}/@@download/manifest/{}".format(
            api.get_url(self.context),
            manifest.filename
        )
