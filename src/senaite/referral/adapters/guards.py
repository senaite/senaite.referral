# -*- coding: utf-8 -*-
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


class BaseGuardAdapter(object):
    """Basic implementation for guard adapters
    """

    def __init__(self, context):
        self.context = context

    def guard(self, action):
        """Returns whether current context supports the given action
        """
        func_name = "guard_{}".format(action)
        func = getattr(self, func_name, None)
        if func:
            return func()

        # No guard intercept here
        return True


@implementer(IGuardAdapter)
class SampleGuardAdapter(BaseGuardAdapter):
    """Adapter for Sample guards
    """

    def guard_ship(self):
        """Returns ture if the sample can be shipped (added to an Outbound
        Sample Shipment). This is, the sample has at least one analysis awaiting
        for result submission
        """
        state = ["registered", "unassigned", "assigned"]
        objs = self.context.getAnalyses(full_objects=False, review_state=state)
        return len(objs) > 0
