# -*- coding: utf-8 -*-
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
