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

from AccessControl import ClassSecurityInfo
from bika.lims import api
from bika.lims.interfaces import IDeactivable
from plone.autoform import directives
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from Products.CMFCore import permissions
from senaite.core.catalog import CLIENT_CATALOG
from senaite.core.content.base import Container
from senaite.core.schema import UIDReferenceField
from senaite.core.z3cform.widgets.uidreference import UIDReferenceWidgetFactory
from senaite.referral import messageFactory as _
from senaite.referral.content import get_bool_value
from senaite.referral.content import get_string_value
from senaite.referral.content import set_bool_value
from senaite.referral.content import set_string_value
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.utils import get_by_code
from senaite.referral.utils import is_valid_code
from senaite.referral.utils import is_valid_url
from zope import schema
from zope.interface import implementer
from zope.interface import Invalid
from zope.interface import invariant


class IExternalLaboratorySchema(model.Schema):
    """ExternalLaboratory content schema
    """

    code = schema.TextLine(
        title=_(u"label_externallaboratory_code", default=u"Code"),
        description=_(
            u"Unique code of the external laboratory. This code is used to "
            u"ensure your laboratory and the external laboratory know each "
            u"other on data transfer"
        ),
        required=True,
    )

    reference = schema.Bool(
        title=_(u"label_externallaboratory_reference",
                default=u"Reference Laboratory"),
        description=_(
            u"Whether this external laboratory is capable of analysis or "
            u"testing on samples sent from the current laboratory. When "
            u"checked, this external laboratory will be displayed for "
            u"selection when dispatching a sample"
        ),
        required=False,
    )

    referring = schema.Bool(
        title=_(u"label_externallaboratory_referring",
                default=u"Referring Laboratory"),
        description=_(
            u"Whether this external laboratory can send samples to your "
            u"laboratory for additional analysis or testing. When checked, "
            u"your SENAITE instance will accept samples for testing sent from "
            u"this external laboratory"
        ),
        required=False,
    )

    referring_client = UIDReferenceField(
        title=_(u"label_externallaboratory_referring_client",
                default=u"Default client"),
        description=_(
            U"The default client for inbound sample shipments received from "
            U"this external laboratory"
        ),
        allowed_types=("Client", ),
        multi_valued=False,
        required=False,
    )

    directives.widget(
        "referring_client",
        UIDReferenceWidgetFactory,
        catalog=CLIENT_CATALOG,
        query={
            "portal_type": "Client",
            "is_active": True,
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        },
        limit=15,
    )

    url = schema.TextLine(
        title=_(u"label_externallaboratory_url", default=u"URL"),
        description=_(
            u"URL of the external laboratory's SENAITE instance. If the "
            u"external laboratory is configured as a reference laboratory "
            u"(destination), your system will use this URL to remotely create "
            u"the dispatched samples on the destination laboratory. When the "
            u"external laboratory is configured as a referring laboratory "
            u"(origin), your system will use this URL to send updates about "
            u"the referred samples to the laboratory of origin"
        ),
        required=False,
    )

    username = schema.TextLine(
        title=_(u"label_externallaboratory_username", default=u"Username"),
        description=_(
            u"Username of the user account from the external laboratory that"
            u"will be used for the remote creation of dispatched samples when "
            u"the external laboratory is configured as a reference laboratory "
            u"or for updates regarding referred samples when configured as a "
            u"referring laboratory"
        ),
        required=False,
    )

    password = schema.Password(
        title=_(u"label_externallaboratory_password", default=u"Password"),
        description=_(
            u"Password of the user account from the external laboratory that"
            u"will be used for the remote creation of dispatched samples when "
            u"the external laboratory is configured as a reference laboratory "
            u"or for updates regarding referred samples when configured as a "
            u"referring laboratory"
        ),
        required=False,
    )

    # Make the code the first field
    directives.order_before(code='*')

    # Reference Laboratory fieldset
    fieldset(
        "reference_laboratory",
        label=_(u"Reference Laboratory"),
        fields=["reference"]
    )

    # Referring Laboratory fieldset
    fieldset(
        "referring_laboratory",
        label=_(u"Referring Laboratory"),
        fields=["referring", "referring_client"]
    )

    # Connectivity fieldset
    fieldset(
        "connectivity",
        label=_(u"Connectivity"),
        fields=["url", "username", "password"]
    )

    @invariant
    def validate_code(data):
        """Checks if the external laboratory code is unique
        """
        code = data.code

        # https://community.plone.org/t/dexterity-unique-field-validation
        context = getattr(data, "__context__", None)
        if context is not None:
            if context.code == code:
                # nothing changed
                return

        if not is_valid_code(code):
            raise Invalid(
                _("Code cannot contain special characters or spaces")
            )

        lab = get_by_code("ExternalLaboratory", code)
        if lab and lab != context:
            raise Invalid(_("Code must be unique"))

    @invariant
    def validate_url(data):
        """Checks if the value for field url is a well-formed URL
        """
        if not data.url:
            return

        url = data.url.strip()
        if not is_valid_url(url):
            raise Invalid(_("URL is not valid"))

    @invariant
    def validate_referring(data):
        """Checks if all the information required for this external laboratory
        to be able to act as a referring laboratory has been filled correctly
        """
        value = data.referring
        if not value:
            return

        # Check if a default client for this referring laboratory has been set
        request = api.get_request()
        client = request.form.get("form.widgets.referring_client")
        if api.is_uid(client):
            return

        # mark the request to avoid multiple raising
        key = "_v_referring_checked"
        if getattr(request, key, False):
            return
        setattr(request, key, True)
        msg = _("Please set the default client to use when creating "
                "samples from this referring laboratory first")
        raise Invalid(msg)


@implementer(IExternalLaboratory, IExternalLaboratorySchema, IDeactivable)
class ExternalLaboratory(Container):
    """Organization that can act as a reference laboratory, as a referring
    laboratory or both
    """
    _catalogs = ["portal_catalog", ]

    security = ClassSecurityInfo()
    exclude_from_nav = True

    @security.protected(permissions.ModifyPortalContent)
    def setReference(self, value):
        """Sets whether this external laboratory can act as reference
        laboratory, that can receive dispatched samples from this instance
        """
        set_bool_value(self, "reference", value)

    @security.protected(permissions.View)
    def getReference(self):
        """Returns whether this external laboratory can act as a reference
        laboratory that can receive dispatched samples from this instance
        """
        return get_bool_value(self, "reference")

    @security.protected(permissions.ModifyPortalContent)
    def setReferring(self, value):
        """Sets whether this external laboratory can act as referring
        laboratory, that can dispatch samples to this instance
        """
        set_bool_value(self, "referring", value)

    @security.protected(permissions.View)
    def getReferring(self):
        """Returns whether this external laboratory can act as a referring
        laboratory that can dispatch sampels to this instance
        """
        return get_bool_value(self, "referring")

    @security.protected(permissions.ModifyPortalContent)
    def setCode(self, value):
        """Sets the code that uniquely identifies this external laboratory
        """
        def validate_code(code):
            if not is_valid_code(code):
                raise ValueError("Code cannot contain special chars or spaces")
            lab = get_by_code("ExternalLaboratory", code)
            if lab and lab != self:
                raise ValueError("Code must be unique")

        set_string_value(self, "code", value, validator=validate_code)

    @security.protected(permissions.View)
    def getCode(self):
        """Returns the code that uniquely identifies this external laboratory
        """
        return get_string_value(self, "code")

    @security.protected(permissions.ModifyPortalContent)
    def setReferringClient(self, value):
        """Sets the default client the samples from inbound shipments will
        be assigned to
        """
        mutator = self.mutator("referring_client")
        mutator(self, value)

    @security.protected(permissions.View)
    def getReferringClient(self):
        """Returns the default client that samples from inbound shipments from
        this laboratory will be assigned to
        """
        accessor = self.accessor("referring_client")
        return accessor(self)

    @security.protected(permissions.View)
    def getRawReferringClient(self):
        """Returns the UID of the default client that samples from inbound
        shipments from this laboratory will be assigned to
        """
        accessor = self.accessor("referring_client", raw=True)
        return accessor(self)

    @security.protected(permissions.ModifyPortalContent)
    def setUrl(self, value):
        """Sets the URL of the SENAITE instance of the external laboratory
        """
        def validate_url(url):
            if url and not is_valid_url(url):
                raise ValueError("URL is not valid")

        set_string_value(self, "url", value, validator=validate_url)

    @security.protected(permissions.View)
    def getUrl(self):
        """The URL of the SENAITE instance of the external laboratory, if any
        """
        return get_string_value(self, "url")

    @security.protected(permissions.ModifyPortalContent)
    def setUsername(self, value):
        """Sets the username of the account used to authenticate against the
        SENAITE instance of the external laboratory in order to send POST
        requests
        """
        set_string_value(self, "username", value)

    @security.protected(permissions.View)
    def getUsername(self):
        """Returns the username of the account used to authenticate against the
        SENAITE instance of the external laboratory in order to send POST
        requests
        """
        return get_string_value(self, "username")

    @security.protected(permissions.ModifyPortalContent)
    def setPassword(self, value):
        """Sets the password of the account used to authenticate against the
        SENAITE instance of the external laboratory in order to send POST
        requests
        """
        set_string_value(self, "password", value)

    @security.protected(permissions.View)
    def getPassword(self):
        """Returns the password of the account used to authenticate against the
        SENAITE instance of the external laboratory in order to send POST
        requests
        """
        return get_string_value(self, "password")
