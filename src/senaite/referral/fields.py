# -*- coding: utf-8 -*-

import six
from archetypes.schemaextender.interfaces import IExtensionField
from Products.Archetypes.Storage.annotation import AnnotationStorage
from Products.ATExtensions.field import RecordsField
from zope.component.hooks import getSite
from zope.interface import implementer

from bika.lims.browser.fields import UIDReferenceField


@implementer(IExtensionField)
class ExtensionField(object):
    """Mix-in class to make Archetypes fields not depend on generated
    accessors and mutators, and use AnnotationStorage by default
    """

    storage = AnnotationStorage()

    def __init__(self, *args, **kwargs):
        super(ExtensionField, self).__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs

    def getAccessor(self, instance):
        """Return the accessor method for getting data out of this field
        """
        def accessor():
            if self.getType().endswith('ReferenceField'):
                return self.get(instance.__of__(getSite()))
            else:
                return self.get(instance)
        return accessor

    def getEditAccessor(self, instance):
        """Return the accessor method for getting raw data out of this field
        e.g.: for editing.
        """
        def edit_accessor():
            if self.getType().endswith('ReferenceField'):
                return self.getRaw(instance.__of__(getSite()))
            else:
                return self.getRaw(instance)
        return edit_accessor

    def getMutator(self, instance):
        """Return the mutator method used for changing the value of this field.
        """
        def mutator(value, **kw):
            if self.getType().endswith('ReferenceField'):
                self.set(instance.__of__(getSite()), value)
            else:
                self.set(instance, value)
        return mutator

    def getIndexAccessor(self, instance):
        """Return the index accessor, i.e. the getter for an indexable value.
        """
        name = getattr(self, 'index_method', None)
        if name is None or name == '_at_accessor':
            return self.getAccessor(instance)
        elif name == '_at_edit_accessor':
            return self.getEditAccessor(instance)
        elif not isinstance(name, six.string_types):
            raise ValueError('Bad index accessor value: %r', name)
        else:
            return getattr(instance, name)


class ExtUIDReferenceField(ExtensionField, UIDReferenceField):
    """Field extender for UIDReferenceField
    """
    pass


class ExtRecordsField(ExtensionField, RecordsField):
    """Field Extender of RecordsField
    """
