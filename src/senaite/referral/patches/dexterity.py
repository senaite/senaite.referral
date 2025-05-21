# -*- coding: utf-8 -*-

from senaite.referral.api import get_remote_uid


def remote_uid(self):
    """Returns the remote UID of the given object, if any
    """
    return get_remote_uid(self)
