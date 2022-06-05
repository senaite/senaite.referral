# -*- coding: utf-8 -*-
from senaite.referral.utils import get_field_value
from senaite.referral.utils import set_field_value


def getReferenceAnalysts(self):
    """Returns the list of remote analysts (from the reference lab) that were
    assigned to the analysis or submitted result
    """
    return get_field_value(self, "ReferenceAnalysts", default=[])


def setReferenceAnalysts(self, value):
    """Sets the value for ReferenceAnalysts field from analysis
    """
    set_field_value(self, "ReferenceAnalysts", value)


def getReferenceVerifiers(self):
    """Returns the list of remote verifiers (from the reference lab) that
    verified the result of current analysis
    """
    return get_field_value(self, "ReferenceVerifiers", default=[])


def setReferenceVerifiers(self, value):
    """Sets the value for ReferenceVerifiers field from analysis
    """
    set_field_value(self, "ReferenceVerifiers", value)


def getReferenceInstrument(self):
    """Returns the name of the instrument used by the reference lab
    """
    return get_field_value(self, "ReferenceInstrument", default="")


def setReferenceInstrument(self, value):
    """Sets the name of the instrument used for this test by the reference lab
    """
    set_field_value(self, "ReferenceInstrument", value)


def getReferenceMethod(self):
    """Returns the name of the method used for this test by the reference lab
    """
    return get_field_value(self, "ReferenceMethod", default="")


def setReferenceMethod(self, value):
    """Sets the name of the method used for this test by the reference lab
    """
    set_field_value(self, "ReferenceMethod", value)
