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

from zope.component import adapts

from bika.lims import api
from bika.lims.interfaces import IGetDefaultFieldValueARAddHook


class OutboundShipmentDefaultFieldValue(object):
    """Adapter that returns the default value for field OutboundShipment
    """
    adapts(IGetDefaultFieldValueARAddHook)

    def __init__(self, request):
        self.request = request

    def __call__(self, context):
        uid = self.request.get("OutboundShipment")
        return api.get_object_by_uid(uid, default=None)
