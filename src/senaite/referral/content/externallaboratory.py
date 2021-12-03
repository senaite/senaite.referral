# -*- coding: utf-8 -*-

from plone.dexterity.content import Item
from plone.supermodel import model
from senaite.referral import messageFactory as _
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.utils import get_by_code
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
            u"Unique code of this reference laboratory. If the reference "
            u"laboratory has a senaite instance running, this code must match "
            u"with the instance's code. It is used to prevent the manual "
            u"import of an inbound shipment (via file) to a lab other than the "
            u"expected"
        ),
        required=True,
    )

    reference_laboratory = schema.Bool(
        title=_(u"label_referencelaboratory_severity",
                default=u"Reference Laboratory"),
        description=_(
            u"Whether this external laboratory is capable of analysis or "
            u"testing on samples sent from the current laboratory. When "
            u"checked, this external laboratory will be displayed for "
            u"selection when dispatching a sample"
        ),
        required=False,
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


@implementer(IExternalLaboratory, IExternalLaboratorySchema)
class ExternalLaboratory(Item):
    """Organization that can act as a reference laboratory, as a referring
    laboratory or both
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
