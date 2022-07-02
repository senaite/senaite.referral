# -*- coding: utf-8 -*-

import itertools

from senaite.referral import messageFactory as _
from senaite.referral import PRODUCT_NAME
from senaite.referral.queue import do_queue_action

from bika.lims import api
from bika.lims import senaiteMessageFactory as _s
from bika.lims.browser.workflow import WorkflowActionGenericAdapter
from bika.lims.workflow import isTransitionAllowed as is_transition_allowed


class WorkflowActionReceiveAdapter(WorkflowActionGenericAdapter):
    """Adapter in charge of InboundShipment's 'receive' action. Triggers the
    'receive' transition for the InboundSample objects, as well as their
    sample objects (aka 'AnalysisRequest') counterparts
    """

    def __call__(self, action, objects):
        # Instead of receiving the whole shipment (up to down), receive the
        # individual inbound samples each shipment contains, so the queue can
        # handle these tasks in a more efficient way
        task_uids = []
        for shipment in objects:
            task = self.do_queue_receive(shipment)
            if task:
                task_uids.append(task.task_short_uid)

        if task_uids:
            task_uids = ", ".join(task_uids)
            msg = _("One or more tasks for the reception of inbound shipments "
                    "have been added to the queue: {}").format(task_uids)
            return self.redirect(message=msg)

        transitioned = self.do_action(action, objects)
        if not transitioned:
            return self.redirect(message=_s("No changes made"), level="warning")

        if self.is_barcodes_preview_on_reception_enabled():
            # Get the 'real' samples from the transitioned inbound samples
            samples = self.get_samples(objects)

            # Redirect to the barcode stickers preview
            setup = api.get_setup()
            uids = ",".join([api.get_uid(sample) for sample in samples])
            sticker_template = setup.getAutoStickerTemplate()
            url = "{}/sticker?autoprint=1&template={}&items={}".format(
                self.back_url, sticker_template, uids)
            return self.redirect(redirect_url=url)

        # Redirect the user to success page
        return self.success(transitioned)

    def get_samples(self, inbound_shipment):
        """Returns the sample objects (aka AnalysisRequest) that have been
        generated because of the reception of the inbound shipment passed-in
        """
        if isinstance(inbound_shipment, (list, tuple)):
            samples = [self.get_samples(obj) for obj in inbound_shipment]
            return list(itertools.chain.from_iterable(samples))

        inbound_shipment = api.get_object(inbound_shipment)
        inbound_samples = inbound_shipment.getInboundSamples()
        samples = [obj.getSample() for obj in inbound_samples]
        return filter(api.is_object, samples)

    def is_barcodes_preview_on_reception_enabled(self):
        """Returns whether the system is configured so user has to be redirected
        to the barcode stickers preview after receiveing inbound samples
        """
        key = "{}.barcodes_preview_reception".format(PRODUCT_NAME)
        return api.get_registry_record(key, default=False)

    def do_queue_receive(self, shipment_or_uid):
        """Tries to queue the reception of this inbound shipment, but for all
        individual contained instead, so samples are received in handy chunks
        """
        shipment = api.get_object(shipment_or_uid)
        samples = shipment.getInboundSamples()

        def can_receive(sample):
            return api.get_review_status(sample) == "due"

        # This is reception, so we are only interested on those that are in a
        # suitable status for reception
        samples = filter(can_receive, samples)
        if not samples:
            # Maybe the shipment is in an intermediate state. No option other
            # than queueing the whole shipment
            action = "receive_inbound_shipment"
            return do_queue_action(shipment, action)

        action = "receive_inbound_sample"
        return do_queue_action(shipment, action, samples)
