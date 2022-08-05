# -*- coding: utf-8 -*-

import json
from datetime import datetime
from persistent.list import PersistentList
from requests import Response
from senaite.referral.utils import is_true
from zope.annotation.interfaces import IAnnotations

POSTS_STORAGE = "senaite.referral.http_posts"


def get_posts_storage(obj):
    """Returns the storage with the list of notifications (POST requests) sent
    to a target laboratory for the given object
    :param obj: Content object
    :returns: PersistentList
    """
    annotation = IAnnotations(obj)
    if annotation.get(POSTS_STORAGE) is None:
        annotation[POSTS_STORAGE] = PersistentList()
    return annotation[POSTS_STORAGE]


def get_posts(obj):
    """Returns all the posts sent to a target laboratory for the given object,
    sorted from oldest to newest
    :param obj: object the POST is about
    :returns: list of dicts
    """
    posts = get_posts_storage(obj)
    return map(json.loads, posts)


def get_last_post(obj):
    """Returns the last post sent to a remote laboratory about the given object
    or None otherwise
    """
    posts = get_posts(obj)
    if posts:
        return posts[-1]
    return None


def is_error(post):
    """Returns whether the post passed-in errored or not
    """
    return not is_true(post["success"])


def get_response_reason(response):
    """Returns the reason of the given requests response object
    Code grabbed from `requests.raise_for_status`
    """
    reason = response.reason
    if isinstance(reason, bytes):
        # We attempt to decode utf-8 first because some servers
        # choose to localize their reason strings. If the string
        # isn't utf-8, we fall back to iso-8859-1 for all other
        # encodings. (See PR #3538)
        try:
            reason = response.reason.decode('utf-8')
        except UnicodeDecodeError:
            reason = response.reason.decode('iso-8859-1')
    return reason


def get_post_base_info():
    """Returns the basics of a dict-like object that represents the information
    of an HTTPResponse
    """
    return {
        "url": "",
        "payload": "",
        "status": "",
        "reason": "",
        "content": "",
        "content_json": {},
        "message": "",
        "success": False,
        "datetime": datetime.now().isoformat(),
    }


def get_post_info(response):
    """Returns a dict-like object with information about the HTTPResponse
    """
    data = get_post_base_info()
    try:
        # json-encoded content of a response
        content_json = response.json()
    except Exception as e:
        # Not JSON deserializable!
        content_json = {}
    data.update({
        # Final URL location of Response
        "url": response.url,
        # Integer Code of responded HTTP Status, e.g. 404 or 200
        "status": response.status_code,
        # Textual reason of responded HTTP Status, e.g. "Not found"
        "reason": get_response_reason(response),
        # Content of the response, in unicode
        "content": response.text,
        "content_json": content_json,
        "message": content_json.get("message", ""),
        "success": content_json.get("success", False),
    })
    return data


def save_post(obj, payload, data_or_response):
    """Stores the notification (POST request) sent to a target laboratory for
    the given obj with the specified payload and remote response
    """
    data = data_or_response
    if isinstance(data_or_response, Response):
        data = get_post_info(data_or_response)

    if not isinstance(data, dict):
        raise ValueError("Type not supported: {}".format(repr(data)))

    data.update({
        "payload": payload,
    })

    # json-ify
    data = json.dumps(data)

    # Get the storage and append this post
    storage = get_posts_storage(obj)
    storage.append(data)
