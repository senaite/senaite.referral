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

from zope.component.interfaces import implements

from bika.lims.browser.workflow import RequestContextAware
from bika.lims.browser.workflow.analysisrequest import \
    WorkflowActionSaveAnalysesAdapter
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IWorkflowActionUIDsAdapter


class WorkflowActionShipAdapter(RequestContextAware):
    """Adapter in charge of Analysis Requests 'ship' action
    """
    implements(IWorkflowActionUIDsAdapter)

    def __call__(self, action, uids):
        """Redirects the user to the OutboundSampleShipment creation view
        """
        url = "{}/referral_ship_samples?uids={}".format(self.back_url,
                                                        ",".join(uids))
        return self.redirect(redirect_url=url)


class SaveAnalysesAdapter(WorkflowActionSaveAnalysesAdapter):

    def get_uids_from_request(self):
        """Returns the UIDs from the request plus those from the analyses from
        the inound shipment that were once requested, if any
        """
        uids = super(SaveAnalysesAdapter, self).get_uids_from_request()
        if not IAnalysisRequest.providedBy(self.context):
            return uids

        inbound_sample = self.context.getInboundSample()
        if not inbound_sample:
            return uids

        uids.extend(inbound_sample.getRawServices())
        return list(set(uids))
