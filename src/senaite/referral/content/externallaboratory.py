# -*- coding: utf-8 -*-

from AccessControl import ClassSecurityInfo
from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from Products.CMFCore import permissions
from senaite.referral import messageFactory as _
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.utils import get_by_code
from senaite.referral.utils import is_valid_code
from senaite.referral.utils import is_valid_url
from zope import schema
from zope.interface import implementer
from zope.interface import Invalid
from zope.interface import invariant

from bika.lims import api
from bika.lims.interfaces import IDeactivable


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

    reference_url = schema.TextLine(
        title=_(u"label_externallaboratory_reference_url", default=u"URL"),
        description=_(
            u"URL of the external laboratory. If filled, your system will use "
            u"this URL to automatically dispatch the samples to the external "
            u"laboratory"
        ),
        required=False,
    )

    reference_username = schema.TextLine(
        title=_(u"label_externallaboratory_reference_username",
                default=u"Username"),
        description=_(
            u"Username of the user to use for the automatic creation of inbound "
            u"sample shipments on the reference laboratory on dispatch"
        ),
        required=False,
    )

    reference_password = schema.Password(
        title=_(u"label_externallaboratory_reference_password",
                default=u"Password"),
        description=_(
            u"Password of the user to use for the automatic creation of inbound "
            u"sample shipments on the reference laboratory on dispatch"
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
        title=_("ulabel_externallaboratory_referring_client",
                default=u"Default client"),
        description=_(
            U"The default client for inbound sample shipments received from "
            U"this external laboratory"
        ),
        vocabulary="senaite.referral.vocabularies.clients",
        required=False,
    )

    # Make the code the first field
    directives.order_before(code='*')

    # Reference Laboratory fieldset
    model.fieldset(
        "reference_laboratory",
        label=_(u"Reference Laboratory"),
        fields=["reference", "reference_url", "reference_username",
                "reference_password"]
    )

    # Referring Laboratory fieldset
    model.fieldset(
        "referring_laboratory",
        label=_(u"Referring Laboratory"),
        fields=["referring", "referring_client"]
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
    def validate_reference_url(data):
        """Checks if the value for field reference_url is a well-formed URL
        """
        if not data.reference_url:
            return

        if not is_valid_url(data.reference_url):
            raise Invalid(_("Reference URL is not valid"))

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
    Item(PasteBehaviourMixin, BrowserDefaultMixin, DexterityContent):

        PasteBehaviourMixin, DAVCollectionMixin, BrowserDefaultMixin,
        CMFCatalogAware, CMFOrderedBTreeFolderBase, DexterityContent):
    """
    _catalogs = ["portal_catalog", ]

    security = ClassSecurityInfo()

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

    def get_reference(self):
        return self.reference

    def set_reference(self, value):
        if self.reference == value:
            return
        self.reference = value

    def get_reference_url(self):
        return self.reference_url

    def set_reference_url(self, value):
        value = value.strip()
        if self.reference_url == value:
            return
        self.reference_url = value

    def get_referring(self):
        return self.referring

    def set_referring(self, value):
        if self.referring == value:
            return
        self.referring = value

    def get_reference_username(self):
        return self.reference_username

    def set_reference_username(self, value):
        value = value.strip()
        if self.reference_username == value:
            return
        self.reference_username = value

    def get_reference_password(self):
        return self.reference_password

    def set_reference_password(self, value):
        value = value.strip()
        if self.reference_password == value:
            return
        self.reference_password = value


    @security.protected(permissions.View)
    def getCode(self):
        accessor = self.accessor("code")
        return accessor(self)

    @security.protected(permissions.View)
    def getReferralClient(self):
        accessor = self.accessor("referring_client")
        return accessor(self)

    @security.protected(permissions.ModifyPortalContent)
    def setReferralClient(self, value):
        mutator = self.mutator("referring_client")
        return mutator(self, value)
