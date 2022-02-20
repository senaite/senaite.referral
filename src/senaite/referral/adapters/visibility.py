# -*- coding: utf-8 -*-

from bika.lims import api
from bika.lims.adapters.widgetvisibility import SenaiteATWidgetVisibility


class OutboundShipmentFieldVisibility(SenaiteATWidgetVisibility):

    def __init__(self, context):
        super(OutboundShipmentFieldVisibility, self).__init__(
            context=context, sort=10, field_names=["OutboundShipment"])

    def isVisible(self, field, mode="view", default="visible"):
        if self.is_client_user() or mode == "edit":
            return "invisible"
        return default

    def is_client_user(self):
        """Returns whether the current user is from a client
        """
        if api.get_current_client():
            return True
        return False
