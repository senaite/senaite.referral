# -*- coding: utf-8 -*-

import copy

from senaite.referral import messageFactory as _

from bika.lims import api
from bika.lims.catalog import SETUP_CATALOG
from bika.lims.utils import t as _t
from bika.lims.utils import to_utf8
from six.moves.urllib import parse
from bika.lims.workflow import getTransitionDate

_marker = object()


def set_field_value(instance, field_name, value):
    """Sets the value to a Schema field
    """
    field = instance.getField(field_name)
    if field:
        # Schema field available
        if hasattr(field, "mutator") and field.mutator:
            mutator = getattr(instance, field.mutator)
            if mutator:
                mutator(value)
                return

        # Apply the value directly to the schema's field
        field.set(instance, value)

    elif hasattr(instance, field_name):
        # No schema field available
        setattr(instance, field_name, value)


def get_field_value(instance, field_name, default=None):
    """Returns the value of a Schema field
    """
    field = instance.getField(field_name)
    if field:
        # Schema field available
        return field.get(instance)

    # No schema field available
    value = getattr(instance, field_name, default)
    if callable(value):
        value = value()
    return value


def translate(i18n_message, mapping=None):
    """Translates a message and handles mapping
    """
    return to_utf8(_t(_(i18n_message, mapping=mapping)))


def get_by_code(portal_type, code, catalog=SETUP_CATALOG):
    """Returns the first object of the given portal type which code matches
    with de code passed-in
    """
    if not code:
        return None
    query = {
        "portal_type": portal_type,
        "filters": {
            "code": code,
        }
    }
    return search(query, catalog, first_only=True)


def search(query, catalog, first_only=False):
    """Returns the objects for the code passed-in, if any
    """
    qry = copy.deepcopy(query)
    filters = qry.pop("filters", {})

    def is_match(obj):
        for key, value in filters.items():
            obj_value = get_field_value(obj, key)
            if obj_value != value:
                return False
        return True

    matches = []
    brains = api.search(qry, catalog)
    for brain in brains:
        obj = api.get_object(brain)
        if is_match(obj):
            if first_only:
                return obj
            matches.append(obj)

    if first_only:
        return None

    return matches


def is_valid_url(value):
    """Return true if the value is a well-formed url
    """
    try:
        result = parse.urlparse(value)
        return all([result.scheme, result.netloc, result.path])
    except:  # noqa a convenient way to check if the url is ok
        return False


def get_action_date(obj, action, default=_marker):
    """Returns the DateTime when an action took place to the given obj.
    """
    action_date = getTransitionDate(obj, action, return_as_datetime=True)
    if action_date is None:
        if default is _marker:
            api.fail("No ation date for {} and {}".format(repr(obj), action))
        action_date = default
    return action_date
