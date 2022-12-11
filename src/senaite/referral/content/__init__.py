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

from senaite.referral.utils import is_true
from senaite.referral.utils import to_uids

from bika.lims import api
from six import string_types
from Products.CMFPlone.utils import safe_unicode
from datetime import datetime


def accessor(obj, fieldname):
    """Return the field accessor for the fieldname
    """
    schema = api.get_schema(obj)
    if fieldname not in schema:
        return None
    return schema[fieldname].get


def mutator(obj, fieldname):
    """Return the field mutator for the fieldname
    """
    schema = api.get_schema(obj)
    if fieldname not in schema:
        return None
    return schema[fieldname].set


def set_string_value(obj, field_name, value, validator=None):
    """Stores the value for the field with the given name as unicode
    """
    if not isinstance(value, string_types):
        value = u""

    value = value.strip()
    if validator:
        validator(value)

    setter = mutator(obj, field_name)
    setter(obj, safe_unicode(value))


def get_string_value(obj, field_name, default=""):
    """Returns the value stored for the field with the given name as an
    utf-8 encoded string
    """
    getter = accessor(obj, field_name)
    value = getter(obj) or default
    return value.encode("utf-8")


def set_string_list_value(obj, field_name, value, validator=None):
    """Stores the value for the field with the given list of values as unicode
    """
    if not isinstance(value, (list, tuple, set)):
        value = [value]
    value = filter(None, value)
    value = [safe_unicode(val).strip() for val in value]

    if validator:
        map(validator, value)

    setter = mutator(obj, field_name)
    setter(obj, value)


def get_string_list_value(obj, field_name):
    """Returns the value stored for the field with the given name as a list
    if utf-8 encoded strings
    """
    getter = accessor(obj, field_name)
    value = getter(obj) or []
    return [val.encode("utf-8") for val in value]


def set_bool_value(obj, field_name, value):
    """Stores the value for the field with the given name as unicode
    """
    setter = mutator(obj, field_name)
    setter(obj, is_true(value))


def get_bool_value(obj, field_name, default=False):
    """Returns the value stored for the field with the given name as an
    utf-8 encoded string
    """
    getter = accessor(obj, field_name)
    value = getter(obj) or default
    return is_true(value)


def set_datetime_value(obj, field_name, value):
    """Stores the value for the field with the given name as datetime
    """
    if value and not isinstance(value, datetime):
        value = api.to_date(value)
        value = value.asdatetime()

    value = value or None
    setter = mutator(obj, field_name)
    setter(obj, value)


def get_datetime_value(obj, field_name, default=None):
    """Returns the value for the field with the given name as datetime
    """
    getter = accessor(obj, field_name)
    value = getter(obj)
    if not value:
        return default
    # TODO 2.x Avoid `UnknownTimeZoneError` by using the date API for conversion
    # also see https://github.com/senaite/senaite.patient/pull/29
    if not isinstance(value, datetime):
        value = api.to_date(value, None)
        if not value:
            return default
        return value.asdatetime()
    if isinstance(value, datetime):
        return value
    return default


def set_uids_field_value(obj, field_name, value, validator=None):
    """Sets the value to a field that stores UIDs
    """
    # Convert the value to a list of UIDs
    uids = to_uids(value)

    # Check the values
    if validator:
        map(validator, uids)

    # Assign the value
    setter = mutator(obj, field_name)
    setter(obj, uids)


def get_uids_field_value(obj, field_name):
    """Returns the value from a field that stores UIDs
    """
    getter = accessor(obj, field_name)
    value = getter(obj)
    if not value:
        value = []
    if not isinstance(value, list):
        value = [value]
    value = filter(None, value)
    return to_uids(value)
