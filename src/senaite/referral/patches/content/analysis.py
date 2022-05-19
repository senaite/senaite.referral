# -*- coding: utf-8 -*-
from senaite.referral.utils import get_field_value
from senaite.referral.utils import set_field_value


def getReferenceVerifiers(self):
    """Returns the list of remote verifiers (from the reference lab) that
    verified the result of current analysis
    """
    return get_field_value(self, "ReferenceVerifiers", default=[])


def setReferenceVerifiers(self, value):
    """Sets the value for ReferenceVerifiers field from analysis
    """
    set_field_value(self, "ReferenceVerifiers", value)
