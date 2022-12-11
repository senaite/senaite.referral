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
