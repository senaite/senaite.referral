# -*- coding: utf-8 -*-

from AccessControl import ClassSecurityInfo
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from Products.CMFCore import permissions
from Products.CMFPlone.utils import safe_unicode
from senaite.referral import messageFactory as _
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.utils import get_by_code
from senaite.referral.utils import get_uids_field_value
from senaite.referral.utils import is_valid_code
from senaite.referral.utils import is_valid_url
from senaite.referral.utils import set_uids_field_value
from six import string_types
from zope import schema
from zope.interface import implementer
from zope.interface import Invalid
from zope.interface import invariant

from bika.lims import api
from bika.lims.interfaces import IDeactivable


def is_true(value):
    """Checks whether the value passed-in has to be evaluated as True
    """
    if isinstance(value, bool):
        return value is True
    if isinstance(value, string_types):
        return value.lower() in ["y", "yes", "1", "true", True]
    return is_true(str(value))


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

    referring_client = schema.Choice(
        title=_(u"label_externallaboratory_referring_client",
                default=u"Default client"),
        description=_(
            U"The default client for inbound sample shipments received from "
            U"this external laboratory"
        ),
        vocabulary="senaite.referral.vocabularies.clients",
        required=False,
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
    model.fieldset(
        "reference_laboratory",
        label=_(u"Reference Laboratory"),
        fields=["reference"]
    )

    # Referring Laboratory fieldset
    model.fieldset(
        "referring_laboratory",
        label=_(u"Referring Laboratory"),
        fields=["referring", "referring_client"]
    )

    # Connectivity fieldset
    model.fieldset(
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
            raise Invalid(_("Code cannot contain special characters or spaces"))

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
        client = client and client[0] or None
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

    @security.private
    def accessor(self, fieldname):
        """Return the field accessor for the fieldname
        """
        schema = api.get_schema(self)
        if fieldname not in schema:
            return None
        return schema[fieldname].get

    @security.private
    def mutator(self, fieldname):
        """Return the field mutator for the fieldname
        """
        schema = api.get_schema(self)
        if fieldname not in schema:
            return None
        return schema[fieldname].set

    @security.private
    def set_string_value(self, field_name, value, validator=None):
        """Stores the value for the field with the given name as unicode
        """
        if not isinstance(value, string_types):
            value = u""

        value = value.strip()
        if validator:
            validator(value)

        mutator = self.mutator(field_name)
        mutator(self, safe_unicode(value))

    @security.private
    def get_string_value(self, field_name, default=""):
        """Returns the value stored for the field with the given name as an
        utf-8 encoded string
        """
        accessor = self.accessor(field_name)
        value = accessor(self) or default
        return value.encode("utf-8")

    @security.protected(permissions.ModifyPortalContent)
    def setReference(self, value):
        """Sets whether this external laboratory can act as reference
        laboratory, that can receive dispatched samples from this instance
        """
        mutator = self.mutator("reference")
        mutator(self, is_true(value))

    @security.protected(permissions.View)
    def getReference(self):
        """Returns whether this external laboratory can act as a reference
        laboratory that can receive dispatched samples from this instance
        """
        accessor = self.accessor("reference")
        return is_true(accessor(self))

    @security.protected(permissions.ModifyPortalContent)
    def setReferring(self, value):
        """Sets whether this external laboratory can act as referring
        laboratory, that can dispatch samples to this instance
        """
        mutator = self.mutator("referring")
        mutator(self, is_true(value))

    @security.protected(permissions.View)
    def getReferring(self):
        """Returns whether this external laboratory can act as a referring
        laboratory that can dispatch sampels to this instance
        """
        accessor = self.accessor("referring")
        return is_true(accessor(self))

    @security.protected(permissions.ModifyPortalContent)
    def setCode(self, value):
        """Sets the code that uniquely identifies this external laboratory
        """
        if not is_valid_code(value):
            raise ValueError("Code cannot contain special characters or spaces")

        lab = get_by_code("ExternalLaboratory", value)
        if lab and lab != self:
            raise Invalid("Code must be unique")

        self.set_string_value("code", value)

    @security.protected(permissions.View)
    def getCode(self):
        """Returns the code that uniquely identifies this external laboratory
        """
        return self.get_string_value("code")

    @security.protected(permissions.ModifyPortalContent)
    def setReferringClient(self, value):
        """Sets the default client the samples from inbound shipments will
        be assigned to
        """
        set_uids_field_value(self, "referring_client", value)

    @security.protected(permissions.View)
    def getReferringClient(self):
        """Returns the default client that samples from inbound shipments from
        this laboratory will be assigned to
        """
        value = get_uids_field_value(self, "referring_client")
        if not value:
            return None
        return value[0]

    @security.protected(permissions.ModifyPortalContent)
    def setUrl(self, value):
        """Sets the URL of the SENAITE instance of the external laboratory
        """
        def validate_url(url):
            if url and not is_valid_url(url):
                raise ValueError("URL is not valid")

        self.set_string_value("url", value, validator=validate_url)

    @security.protected(permissions.View)
    def getUrl(self):
        """The URL of the SENAITE instance of the external laboratory, if any
        """
        return self.get_string_value("url")

    @security.protected(permissions.ModifyPortalContent)
    def setUsername(self, value):
        """Sets the username of the account used to authenticate against the
        SENAITE instance of the external laboratory in order to send POST
        requests
        """
        self.set_string_value("username", value)

    @security.protected(permissions.View)
    def getUsername(self):
        """Returns the username of the account used to authenticate against the
        SENAITE instance of the external laboratory in order to send POST
        requests
        """
        return self.get_string_value("username")

    @security.protected(permissions.ModifyPortalContent)
    def setPassword(self, value):
        """Sets the password of the account used to authenticate against the
        SENAITE instance of the external laboratory in order to send POST
        requests
        """
        self.set_string_value("password", value)

    @security.protected(permissions.View)
    def getPassword(self):
        """Returns the password of the account used to authenticate against the
        SENAITE instance of the external laboratory in order to send POST
        requests
        """
        return self.get_string_value("password")
