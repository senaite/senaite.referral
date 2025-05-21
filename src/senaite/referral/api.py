# -*- coding: utf-8 -*-

import json

from bika.lims.api import get_object
from bika.lims.api import get_tool
from bika.lims.api import is_at_content
from bika.lims.api import parse_json
from bika.lims.api import UID_CATALOG
from BTrees.OOBTree import OOBTree
from Products.Archetypes.utils import getRelURL
from senaite.referral.config import REFERRAL_STORAGE
from senaite.referral.interfaces import IRemoteContent
from senaite.referral.interfaces import IRemoteResource
from zope.annotation.interfaces import IAnnotations
from zope.interface import alsoProvides
from zope.interface import noLongerProvides
from senaite.jsonapi import api as jsonapi

_marker = object


def is_remote_content(obj):
    """Determines whether the provided object has corresponding referral
    content in a remote laboratory
    """
    return IRemoteContent.providedBy(obj)


def is_remote_resource(obj):
    """Returns whether the object passed in is a remote resource
    """
    return IRemoteResource.providedBy(obj)


def to_remote_resource(obj):
    """Returns a RemoteResource from a remote content
    """
    if is_remote_resource(obj):
        return obj

    # Use jsonapi's `get_info` to retrieve the dictionary representation of the
    # object. This ensures consistency between data pushed to the remote
    # instance and data pulled by the remote instance from this instance.
    info = jsonapi.get_info(obj)

    # Prevent circular dependencies
    from senaite.referral.remote.resource import RemoteResource
    return RemoteResource(info)


def get_referral_storage(obj):
    """Get or creates the referral storage for the given object

    :param obj: Content object
    :returns: PersistentDict
    """
    annotation = IAnnotations(obj)
    if annotation.get(REFERRAL_STORAGE) is None:
        annotation[REFERRAL_STORAGE] = OOBTree()
    return annotation[REFERRAL_STORAGE]


def get_remote_uid(obj):
    """Returns the UID of the remote object, if any
    """
    if is_remote_resource(obj):
        return obj.UID
    if is_remote_content(obj):
        storage = get_referral_storage(obj)
        return storage.get("remote_uid", None)
    return None


def get_remote_resource(obj):
    """Returns the remote resource of the given object, if any
    """
    if is_remote_resource(obj):
        return obj
    if is_remote_content(obj):
        storage = get_referral_storage(obj)
        data = storage.get("remote_data", None)
        data = parse_json(data, default=None)
        if data:
            # Prevent circular dependencies
            from senaite.referral.remote.resource import RemoteResource
            return RemoteResource(data)
    return None


def link_remote_resource(obj, resource):
    """Links the object to a remote resource, a referral content from a remote
    laboratory
    """
    if not is_remote_resource(resource):
        raise ValueError("Type not supported: %r" % type(resource))

    # mark the object with IRemoteContent, so we can always know before hand
    # if this object has a counterpart resource in a remote lab
    if not IRemoteContent.providedBy(obj):
        alsoProvides(obj, IRemoteContent)

    # json-ify
    data = resource.to_dict()
    data = json.dumps(data)

    # assign the remote uid, along with current data so we can always use
    # the original information, even when connection with remove lab is lost
    annotation = get_referral_storage(obj)
    annotation["remote_uid"] = resource.UID
    annotation["remote_data"] = data

    # re-catalog object
    catalog_object(obj)


def unlink_remote_resource(obj):
    """Unlinks the remote resource from the given object
    """
    if IRemoteContent.providedBy(obj):
        noLongerProvides(obj, IRemoteContent)

    IAnnotations(obj)
    annotation = get_referral_storage(obj)
    if "remote_uid" in annotation:
        del(annotation["remote_uid"])
    if "remote_date" in annotation:
        del(annotation["remote_data"])

    # re-catalog object
    catalog_object(obj)


def get_brain_by_remote_uid(uid, default=None):
    """Returns the brain of the current instance linked to a remote referral
    content with the specified UID, if it exists.

    :param uid: The remote UID to search by
    :type uid: string
    :rtype: CatalogBrain
    :returns: Found brain or default
    """
    if not uid:
        return default

    uc = get_tool(UID_CATALOG)
    brains = uc(remote_uid=uid)
    if len(brains) != 1:
        return default
    return brains[0]


def get_object_by_remote_uid(uid, default=_marker):
    """Returns the object of the current instance linked to a remote referral
    content with the specified UID, if it exists.

    :param uid: The remote UID to search by
    :type uid: string
    :rtype: ATContentType/DexterityContentType
    :returns: Found object or default
    """
    if not uid:
        if default is not _marker:
            return default
        raise ValueError("uid not set")

    brain = get_brain_by_remote_uid(uid)
    if not brain:
        if default is not _marker:
            return default
        raise ValueError("No object found for remote uid %s" % uid)

    return get_object(brain)


def catalog_object(obj):
    """Catalog the object in all registered catalogs
    """
    uid_catalog = get_tool(UID_CATALOG)
    if is_at_content(obj):
        # For ATs, the uids of uid_catalog are relative paths to portal root
        # see Products.Archetypes.UIDCatalog.UIDResolver.catalog_object
        url = getRelURL(uid_catalog, obj.getPhysicalPath())
    else:
        # For DXs, the uids of uid_catalog are absolute paths to portal root
        # see plone.app.referencablebehavior.uidcatalog
        url = "/".join(obj.getPhysicalPath())

    # explicitly catalog in uid_catalog
    uid_catalog.catalog_object(obj, url)

    # reindex in registered catalogs
    obj.reindexObject()
