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
            if obj.getReferring():
                # Only those external labs that can act as referring labs
                items.append(to_simple_term(obj))

        return SimpleVocabulary(items)


@implementer(IVocabularyFactory)
class ReferenceLaboratoriesVocabulary(object):
    """Returns a simple vocabulary made of ExternalLaboratories to which we can
    send samples because they have the setting "Reference Laboratory" enabled
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
            if obj.getReference():
                # Only those external labs that can act as referring labs
                items.append(to_simple_term(obj))

        return SimpleVocabulary(items)


@implementer(IVocabularyFactory)
class ClientsVocabulary(object):
    """Returns a simple vocabulary made of active Clients
    """

    def __call__(self, context):
        query = {
            "portal_type": "Client",
            "is_active": True,
            "sort_on": "sortable_title",
            "sort_order": "ascending",
        }
        brains = api.search(query, "portal_catalog")
        items = map(to_simple_term, brains)
        return SimpleVocabulary(items)


ReferringLaboratoriesVocabularyFactory = ReferringLaboratoriesVocabulary()
ReferenceLaboratoriesVocabularyFactory = ReferenceLaboratoriesVocabulary()
ClientsVocabularyFactory = ClientsVocabulary()
