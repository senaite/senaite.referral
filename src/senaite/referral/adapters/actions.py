# -*- coding: utf-8 -*-
from senaite.referral import messageFactory as _
from senaite.referral.utils import get_previous_status
from zope.interface import implementer
from zope.lifecycleevent import modified

from bika.lims import api
from bika.lims.browser.workflow import RequestContextAware
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IWorkflowActionUIDsAdapter
from bika.lims.utils import changeWorkflowState


@implementer(IWorkflowActionUIDsAdapter)
class RecoverFromShipmentAdapter(RequestContextAware):
    """Adapter that handles "recover_from_shipment" action. Removes the
    samples from the outbound shipment
    """

    def __call__(self, action, uids):
        """Remove the samples from the outbound shipment
        """

        # Remove samples from current context (OutboundShipment)
        shipped_samples = self.context.get_samples()

        # Bail out those uids that are not present in the OutboundShipment
        uids = filter(lambda uid: uid in shipped_samples, uids)

        # Remove the samples from the outbound shipment
        shipped_samples = filter(lambda uid: uid not in uids, shipped_samples)
        self.context.set_samples(shipped_samples)

        sample_ids = []
        for uid in uids:
            sample = api.get_object(uid, default=None)
            sample_ids.append(api.get_id(sample))
            if not IAnalysisRequest.providedBy(sample):
                continue

            status = api.get_review_status(sample)
            if status != "shipped":
                continue

            # Transition the sample to the state before it was shipped
            prev = get_previous_status(sample, default="sample_received")
            changeWorkflowState(sample, "bika_ar_workflow", prev)

            # Notify the sample has ben modified
            modified(sample)

            # Reindex the sample
            sample.reindexObject()

        ids = ", ".join(sample_ids)
        message = _("These samples have been recovered: {}").format(ids)
        self.add_status_message(message=message)

        return self.redirect()
