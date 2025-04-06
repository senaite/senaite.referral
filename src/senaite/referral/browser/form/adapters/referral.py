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
# Copyright 2021-2025 by it's authors.
# Some rights reserved, see README and LICENSE.


from senaite.core.browser.form.adapters import EditFormAdapterBase

WIDGET_DEFAULT_CONTACTS = "form-widgets-default_contact"


class EditFormAdapter(EditFormAdapterBase):
    """Edit form adapter for InboundSampleShipment
    """

    def modified(self, data):
        name = data.get("name")
        value = data.get("value")
        if name == "form.widgets.referring_client":
            client = value[0] if value else None
            self.update_default_contacts(client)

        return self.data

    def update_default_contacts(self, client):
        """Update the default contacts widget with the contacts of the client
        """
        query = {
            "portal_type": "Contact",
            "is_active": True,
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        }

        if not client:
            # search for all contacts
            self.add_state_widget(WIDGET_DEFAULT_CONTACTS, query=query)
            return

        # restrict the available contacts to those of the client
        query["getParentUID"] = client
        self.add_state_widget(WIDGET_DEFAULT_CONTACTS, query=query)
