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

from senaite.referral import messageFactory as _
from senaite.referral.workflow import recover_sample
from zope.interface import implementer

from bika.lims import api
from bika.lims.browser.workflow import RequestContextAware
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IWorkflowActionUIDsAdapter


@implementer(IWorkflowActionUIDsAdapter)
class RecoverFromShipmentAdapter(RequestContextAware):
    """Adapter that handles "recover_from_shipment" action. Removes the
    samples from the outbound shipment
    """

    def __call__(self, action, uids):
        """Remove the samples from the outbound shipment
        """

        # Remove samples from current context (OutboundShipment)
        shipped_samples = self.context.getRawSamples()

        # Bail out those uids that are not present in the OutboundShipment
        uids = filter(lambda uid: uid in shipped_samples, uids)

        # Remove the samples from the outbound shipment
        shipped_samples = filter(lambda uid: uid not in uids, shipped_samples)
        self.context.setSamples(shipped_samples)

        sample_ids = []
        for uid in uids:
            sample = api.get_object(uid, default=None)
            sample_ids.append(api.get_id(sample))
            if not IAnalysisRequest.providedBy(sample):
                continue

            # Recover the sample
            recover_sample(sample, shipment=self.context)

        ids = ", ".join(sample_ids)
        message = _("These samples have been recovered: {}").format(ids)
        self.add_status_message(message=message)

        return self.redirect()
