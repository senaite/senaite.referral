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

from bika.lims import api
from bika.lims.interfaces import IIdServerVariables
from zope.interface import implementer


@implementer(IIdServerVariables)
class IDServerVariablesAdapter(object):
    """An adapter for the generation of Variables for ID Server
    """

    def __init__(self, context):
        self.context = context

    def get_variables(self, **kw):
        """Returns additional variables for ID Server depending on the type of
        the current context
        """
        lab = kw.get("container") or api.get_parent(self.context)
        variables = {
            "lab_code": lab.getCode(),
        }
        return variables
