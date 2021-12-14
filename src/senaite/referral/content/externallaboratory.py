# -*- coding: utf-8 -*-

from plone.autoform import directives
from plone.dexterity.content import Container
from plone.supermodel import model
from senaite.referral import messageFactory as _
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.utils import get_by_code
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

    reference_url = schema.TextLine(
        title=_(u"label_externallaboratory_reference_url", default=u"URL"),
        description=_(
            u"URL of the external laboratory. If filled, your system will use "
            u"this URL to automatically dispatch the samples to the external "
            u"laboratory"
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

    referring_username = schema.TextLine(
        title=_(u"label_externallaboratory_referring_username",
                default=u"Username"),
        description=_(
            u"Username of the user the samples will be created on behalf of "
            u"the external laboratory"
        ),
        required=False,
    )

    referring_password = schema.Password(
        title=_(u"label_externallaboratory_referring_password",
                default=u"Password"),
        description=_(
            u"Password of the user the samples will be created on behalf of "
            u"the external laboratory"
        ),
        required=False,
    )

    # Make the code the first field
    directives.order_before(code='*')

    # Reference Laboratory fieldset
    model.fieldset(
        "reference_laboratory",
        label=_(u"Reference Laboratory"),
        fields=["reference", "reference_url"]
    )

    # Referring Laboratory fieldset
    model.fieldset(
        "referring_laboratory",
        label=_(u"Referring Laboratory"),
        fields=["referring", "referring_username", "referring_password"]
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

        lab = get_by_code("ExternalLaboratory", code)
        if lab:
            raise Invalid(_("Code must be unique"))

    @invariant
    def validate_reference_url(data):
        """Checks if the value for field reference_url is a well-formed URL
        """
        if not data.reference_url:
            return

        if not is_valid_url(data.reference_url):
            raise Invalid(_("Reference URL is not valid"))


@implementer(IExternalLaboratory, IExternalLaboratorySchema)
class ExternalLaboratory(Container):
    """Organization that can act as a reference laboratory, as a referring
    laboratory or both
    Item(PasteBehaviourMixin, BrowserDefaultMixin, DexterityContent):

        PasteBehaviourMixin, DAVCollectionMixin, BrowserDefaultMixin,
        CMFCatalogAware, CMFOrderedBTreeFolderBase, DexterityContent):
    """
    _catalogs = ["portal_catalog", ]

    def get_code(self):
        code = self.code
        if not code:
            return u""
        return self.code

    def set_code(self, value):
        value = value.strip()
        if self.code == value:
            # nothing changed
            return

        symptom = get_by_code("ExternalLaboratory", value)
        if symptom:
            raise ValueError("An External laboratory with Code '{}' already "
                             "exists".format(value))
        self.code = value

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

    def get_referring_username(self):
        return self.referring_username

    def set_referring_username(self, value):
        value = value.strip()
        if self.referring_username == value:
            return
        self.referring_username = value

    def get_referring_password(self):
        return self.referring_password

    def set_referring_password(self, value):
        value = value.strip()
        if self.referring_password == value:
            return
        self.referring_password = value
