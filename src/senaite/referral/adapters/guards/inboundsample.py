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

from senaite.referral.adapters.guards import BaseGuardAdapter
from zope.interface import implementer

from bika.lims.interfaces import IGuardAdapter


@implementer(IGuardAdapter)
class InboundSampleGuardAdapter(BaseGuardAdapter):

    def guard_receive_inbound_sample(self):
        """Returns true if the inbound sample can be received, either because
        is in a suitable status (due) or because it is received, but without
        a sample counterpart
        """
        if self.context.getRawSample():
            return False
        return True
