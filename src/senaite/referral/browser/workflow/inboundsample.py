# -*- coding: utf-8 -*-

from senaite.referral import messageFactory as _
from senaite.referral import PRODUCT_NAME
from senaite.referral.queue import do_queue_action

from bika.lims import api
from bika.lims import senaiteMessageFactory as _s
from bika.lims.browser.workflow import WorkflowActionGenericAdapter


class WorkflowActionReceiveAdapter(WorkflowActionGenericAdapter):
    """Adapter in charge of InboundSample's 'receive' action. Triggers the
    'receive' transition for the InboundSample objects, as well as their
    sample objects (aka 'AnalysisRequest') counterparts
    """

    def __call__(self, action, objects):
        task = do_queue_action(self.context, action, objects)
        if task:
            task_uid = task.task_short_uid
            msg = _("A task for the reception of inbound samples has been "
                    "added to the queue: {}").format(task_uid)
            return self.redirect(message=msg)


        inbound_samples = [api.get_object(obj) for obj in objects]
        transitioned = self.do_action(action, inbound_samples)
        if not transitioned:
            return self.redirect(message=_s("No changes made"), level="warning")

        if self.is_barcodes_preview_on_reception_enabled():
            # Get the 'real' samples from the transitioned inbound samples
            samples = [obj.getSample() for obj in inbound_samples]
            samples = filter(api.is_object, samples)

            # Redirect to the barcode stickers preview
            setup = api.get_setup()
            uids = ",".join([api.get_uid(sample) for sample in samples])
            sticker_template = setup.getAutoStickerTemplate()
            url = "{}/sticker?autoprint=1&template={}&items={}".format(
                self.back_url, sticker_template, uids)
            return self.redirect(redirect_url=url)

        # Redirect the user to success page
        return self.success(transitioned)

    def is_barcodes_preview_on_reception_enabled(self):
        """Returns whether the system is configured so user has to be redirected
        to the barcode stickers preview after receiveing inbound samples
        """
        key = "{}.barcodes_preview_reception".format(PRODUCT_NAME)
        return api.get_registry_record(key, default=False)
