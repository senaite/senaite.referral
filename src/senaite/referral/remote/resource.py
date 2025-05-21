# -*- coding: utf-8 -*-

import copy

from bika.lims.api import to_utf8
from senaite.core.api import dtime
from senaite.referral.api import get_object_by_remote_uid
from senaite.referral.interfaces import IRemoteResource
from zope.interface import implementer

_marker = object()


@implementer(IRemoteResource)
class RemoteResource(object):
    """Object that wraps a dict representation of a referral object from a
    remote laboratory
    """

    def __init__(self, data):
        self._data = copy.deepcopy(data) if data else {}

    @property
    def id(self):
        """Returns the ID of this remote resource
        Mimics the behavior of DX and AT types
        """
        return self.get_raw("id")

    @property
    def UID(self):
        """Returns the UID of this remote resource
        Mimics the behavior of DX and AT types
        """
        return self.get_raw("uid")

    @property
    def created(self):
        """Returns the date when this remote resource was created
        Mimics the behavior of DX and AT types
        """
        return dtime.to_dt(self.get_raw("created"))

    @property
    def modified(self):
        """Returns the last modification date of this remote resource
        Mimics te behavior of DX and AT types
        """
        value = self.get_raw("modified", default=self.created)
        return dtime.to_dt(value)

    @property
    def review_state(self):
        """Returns the current status of this remote resource
        Mimics the behavior of DX and AT Types
        """
        return self.get_raw("review_state")

    def getPhysicalPath(self):
        """Returns the physical path of this remote resource
        Mimics the behavior of DX and AT Types
        """
        return self.get_raw("PhysicalPath")

    def Title(self):
        """Returns the title of this remote resource
        Mimics the behavior of DX and AT Types
        """
        val = self.get_raw("title")
        return to_utf8(val)

    def getObject(self):
        """Returns the counterpart SENAITE object of this remote resource
        Mimics the behavior of DX and AT types
        """
        return get_object_by_remote_uid(self.UID, default=None)

    def to_dict(self):
        """Returns a dict representation of this object
        """
        return copy.deepcopy(self._data)

    def get_raw(self, field_name, default=None):
        return self._data.get(field_name, default)

    def get(self, field_name, default=None):
        # is there any converter for this specific field
        func = getattr(self, "_get_{}".format(field_name), None)
        if func and callable(func):
            return func()

        record = self.get_raw(field_name, _marker)
        if record is _marker:
            return default

        return record

    def to_object_info(self):
        """Returns a dict with the necessary information for the creation of
        an object counterpart at senaite
        """
        raise NotImplementedError("To be implemented by subclass")

    def __repr__(self):
        return repr(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()
