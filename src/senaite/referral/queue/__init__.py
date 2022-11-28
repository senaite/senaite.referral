# -*- coding: utf-8 -*-

from bika.lims import api

try:
    from senaite.queue.api import is_queue_ready
    from senaite.queue.api import add_action_task
    from senaite.queue.request import get_task_url
except ImportError:
    # Queue is not installed
    is_queue_ready = None
    add_action_task = None


def is_under_consumption(obj):
    """Returns whether the object is being processed by a consumer within the
    current request life-cycle
    """
    request = api.get_request()
    queue_task_uid = request.get("queue_tuid", "")
    return queue_task_uid != "0" and api.is_uid(queue_task_uid)


def do_queue_action(context, action, objects=None, unique=True, chunk_size=1):
    """Returns the queued task for the action to be performed against the given
    object. Returns None if no queue task can be created for this action
    """
    if not callable(is_queue_ready):
        return None
    if not callable(add_action_task):
        return None
    if not is_queue_ready():
        return None
    if not objects:
        objects = [context]
    kwargs = {"unique": unique, "chunk_size": chunk_size, "delay": 120}
    return add_action_task(objects, action, context, **kwargs)
