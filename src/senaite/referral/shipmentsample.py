# -*- coding: utf-8 -*-
import copy
from bika.lims import api


class ShipmentSample(object):

    def __init__(self, data):
        self._obj = None
        if api.is_object(data):
            self._obj = data
            self._data = copy.deepcopy(data.__dict__)
            self._data.update({
                "uid": api.get_uid(data),
                "id": api.get_id(data),
            })
        else:
            self._data = data

    @property
    def uid(self):
        return self._data.get("uid", "")

    @property
    def id(self):
        return self._data.get("id", "")

    @property
    def obj(self):
        return self._obj
