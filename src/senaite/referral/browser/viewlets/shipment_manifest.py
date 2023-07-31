# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFERRAL.
#
# SENAITE.REFERRAL is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2021-2022 by it's authors.
# Some rights reserved, see README and LICENSE.

from plone.app.layout.viewlets import ViewletBase
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import check_installed
from senaite.referral.browser.shipment_manifest import ShipmentManifestView

from bika.lims import api


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

        statuses = self.get_review_history_statuses()
        return "ready" in statuses

    def get_review_history_statuses(self):
        """Returns a list with the review status ids of the instance
        """
        history = api.get_review_history(self.context, rev=False)
        return map(lambda event: event["review_state"], history)

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
