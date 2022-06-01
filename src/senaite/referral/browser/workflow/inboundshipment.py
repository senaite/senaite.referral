# -*- coding: utf-8 -*-

import itertools

from senaite.referral import PRODUCT_NAME

from bika.lims import api
from bika.lims import senaiteMessageFactory as _s
from bika.lims.browser.workflow import WorkflowActionGenericAdapter


class WorkflowActionReceiveAdapter(WorkflowActionGenericAdapter):
    """Adapter in charge of InboundShipment's 'receive' action. Triggers the
    'receive' transition for the InboundSample objects, as well as their
    sample objects (aka 'AnalysisRequest') counterparts
    """

    def __call__(self, action, objects):
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
