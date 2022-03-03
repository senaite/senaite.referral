# -*- coding: utf-8 -*-

import collections
import copy

from senaite.referral import logger
from senaite.referral import messageFactory as _
from senaite.referral import PRODUCT_NAME
from six.moves.urllib import parse
from slugify import slugify

from bika.lims import api
from bika.lims.catalog import SETUP_CATALOG
from bika.lims.utils import render_html_attributes
from bika.lims.utils import t as _t
from bika.lims.utils import to_utf8
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


def get_field_value(instance, field_name, default=None, raw=False):
    """Returns the value of a Schema field
    """
    if api.is_at_content(instance):
        field = instance.getField(field_name)
        if field:
            # Schema field available
            if raw:
                return field.getRaw(instance)
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


def get_by_code(portal_type, code, catalog="portal_catalog"):
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


def get_object_by_title(portal_type, title, catalog="portal_catalog",
                        default=_marker):
    """Returns an object for the portal type and title passed-in, if any
    """
    if not all([portal_type, title]):
        if default is _marker:
            raise ValueError("portal_type and/or title not set")
        return default

    query = {
        "portal_type": portal_type,
        "title": title,
    }
    raise_error = default is _marker
    obj = get_object(query, catalog=catalog, raise_error=raise_error)
    if not obj:
        if raise_error:
            msg = "No {} found with title '{}'".format(portal_type, title)
            raise ValueError(msg)
        return default
    return obj


def get_object(query, catalog="portal_catalog", raise_error=True):
    """Returns the object that matches with the query passed-in, if any. Returns
    None otherwise. If more than one object is found for the query and catalog
    passed-in, system raises an a ValueError unless 'raise_error' is False. In
    such case, system returns None
    :param query: dict containing the search criteria
    :param catalog: the catalog to search objects against
    :param raise_error: whether a ValueError is raised if not unique
    """
    objects = search(query, catalog=catalog)
    if not objects:
        return None
    if len(objects) > 1:
        msg = "{} objects found for {}".format(len(objects), repr(query))
        logger.warn(msg)
        if raise_error:
            raise ValueError(msg)
        return None
    return objects[0]


def is_valid_url(value):
    """Return true if the value is a well-formed url
    """
    try:
        result = parse.urlparse(value)
        return all([result.scheme, result.netloc, result.path])
    except:  # noqa a convenient way to check if the url is ok
        return False


def is_valid_code(value):
    """Return whether the value can be used as a laboratory code
    """
    val = value.replace("_", "")
    return value == slugify(val, separator="", lowercase=False)


def get_action_date(obj, action, default=_marker):
    """Returns the DateTime when an action took place to the given obj.
    """
    action_date = getTransitionDate(obj, action, return_as_datetime=True)
    if action_date is None:
        if default is _marker:
            api.fail("No ation date for {} and {}".format(repr(obj), action))
        action_date = default
    return action_date


def get_image(name, **kwargs):
    """Returns a well-formed image
    :param name: file name of the image
    :param kwargs: additional attributes and values
    :return: a well-formed html img
    """
    if not name:
        return ""
    attr = render_html_attributes(**kwargs)
    url = get_image_url(name)
    return '<img src="{}" {}/>'.format(url, attr)


def get_image_url(name):
    """Returns the url for the give image
    """
    portal_url = api.get_url(api.get_portal())
    return "{}/++resource++senaite.referral.static/{}"\
        .format(portal_url, name)


def get_lab_code():
    """Returns the code of the current lab instance
    """
    key = "{}.code".format(PRODUCT_NAME)
    return api.get_registry_record(key)


def is_manual_inbound_shipment_permitted():
    """Returns whether the manual creation of inbound shipments is permitted
    """
    key = "{}.manual_inbound_permitted".format(PRODUCT_NAME)
    return api.get_registry_record(key, default=False)


def to_uids(value):
    """Returns the value passed-in as a list of UIDs
    """
    if not isinstance(value, list):
        value = [value]

    value = filter(None, value)
    value = map(api.get_uid, value)
    value = list(collections.OrderedDict.fromkeys(value))
    return value


def set_uids_field_value(instance, field_name, value, validator=None):
    """Sets the value to a field that stores UIDs
    """
    # Convert the value to a list of UIDs
    uids = to_uids(value)
    if get_field_value(instance, field_name, raw=True) == uids:
        # Nothing changed
        return

    # Check the values
    if validator:
        map(validator, uids)

    # Assign the value
    mutator = instance.mutator(field_name)
    mutator(instance, uids)


def get_uids_field_value(instance, field_name):
    """Returns the value from a field that stores UIDs
    """
    value = get_field_value(instance, field_name, raw=True)
    if not value:
        value = []
    if not isinstance(value, list):
        value = [value]
    return filter(api.is_uid, value)


def is_from_shipment(sample):
    """Returns whether the sample comes from an inbound sample shipment
    """
    shipment = get_field_value(sample, "InboundShipment", raw=True)
    if shipment:
        return True
    return False
