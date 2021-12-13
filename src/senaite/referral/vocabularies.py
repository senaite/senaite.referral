# -*- coding: utf-8 -*-

from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

from bika.lims import api


def to_simple_term(obj, prefix=""):
    """Returns a SimpleTerm object made of the UID of the object as the value
    and its title as the text
    """
    uid = api.get_uid(obj)
    title = "{}{}".format(prefix, api.get_title(obj))
    return SimpleTerm(uid, title=title)


def to_simple_vocabulary(query, catalog_id):
    """Returns a simple vocabulary made of the objects returned for the query
    and catalog passed-in, where each item (SimpleTerm) is made of UID as value
    and title as the text
    """
    brains = api.search(query, catalog_id)
    items = map(to_simple_term, brains)
    return SimpleVocabulary(items)


@implementer(IVocabularyFactory)
class ReferringLaboratoriesVocabulary(object):
    """Returns a simple vocabulary made of ExternalLaboratories that can send
    us samples becasue they have the setting "Referring Laboratory" enabled
    """

    def __call__(self, context):
        query = {
            "portal_type": "ExternalLaboratory",
            "is_active": True,
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        }
        items = []
        for brain in api.search(query, "portal_catalog"):
            obj = api.get_object(brain)
            if obj.get_referring():
                # Only those external labs that can act as referring labs
                items.append(to_simple_term(obj))

        return SimpleVocabulary(items)


ReferringLaboratoriesVocabularyFactory = ReferringLaboratoriesVocabulary()
