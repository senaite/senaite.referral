# -*- coding: utf-8 -*-

import copy

from senaite.core.supermodel import SuperModel
from senaite.referral.utils import get_lab_code

from bika.lims import api
from remotesession import RemoteSession


class RemoteLab(object):

    _session = None

    def __init__(self, external_laboratory):
        self.laboratory = external_laboratory

    @property
    def laboratory_url(self):
        return self.laboratory.getUrl()

    @property
    def session(self):
        if self._session is None:
            self._session = RemoteSession(self.laboratory_url)
        return self._session

    def auth(self):
        username = self.laboratory.getUsername()
        password = self.laboratory.getPassword()
        return self.session.auth(username, password)

    def do_action(self, obj, action, timeout=5):
        """Sends a POST request to the remote laboratory for the object and
        action passed-in
        """
        if isinstance(obj, (list, tuple, set)):
            items = [self.get_object_info(obj) for obj in obj]
        else:
            items = [self.get_object_info(obj)]

        payload = {
            "consumer": "senaite.referral.consumer",
            "lab_code": get_lab_code(),
            "action": action,
            "items": items,
        }
        return self.session.post(self.laboratory, "push", payload, timeout=timeout)

    def get_object_info(self, obj):
        """Returns a dict representation of the object passed-in, suitable for
        being injected into a POST payload
        """
        if not api.is_object(obj):
            n_obj = api.get_object(obj, default=None)
            if not n_obj:
                raise ValueError("Type not supported: {}".format(repr(obj)))
            return self.get_object_info(n_obj)

        # Basic information
        basic_info = {
            "id": api.get_id(obj),
            "uid": api.get_uid(obj),
            "portal_type": api.get_portal_type(obj),
        }

        # Find out if there is a specific adapter converter
        # adapter = queryAdapter(obj, IReferralObjectInfo)
        # if adapter:
        #     return adapter.to_dict()

        # Rely on supermodel
        sm = SuperModel(obj)
        info = sm.to_dict()
        basic_info.update(info)
        return basic_info
