# -*- coding: utf-8 -*-

from senaite.referral import messageFactory as _
from senaite.referral.browser import BaseView
from senaite.referral.workflow.outboundsampleshipment import events


class RetryShipmentNotificationView(BaseView):

    def __call__(self):
        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)
        form_retry = form.get("retry", False)

        if form_submitted and form_retry:
            # Try to re-send the notification
            message = events.after_dispatch_outbound_shipment(self.context)
            if message:
                self.add_status_message(_(message), level="error")
            else:
                response = self.context.get_dispatch_notification_info()
                status = response.get("status")
                message = response.get("message")
                message = "[{}] {}".format(status, message)
                level = "info"
                if status != "200":
                    level = "error"

                self.add_status_message(message, level=level)

        return self.redirect()
