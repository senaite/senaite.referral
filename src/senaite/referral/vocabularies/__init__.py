# -*- coding: utf-8 -*-

from senaite.core.schema.vocabulary import to_simple_vocabulary
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory


@implementer(IVocabularyFactory)
class SimpleVocabularyFactory(object):

    def __init__(self, source):
        """Initializes a simple vocabulary factory
        :param source: a tuple or list of (value, text)
        """
        self.source = source

    def __call__(self, context):
        return to_simple_vocabulary(self.source)
