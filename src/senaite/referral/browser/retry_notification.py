# -*- coding: utf-8 -*-
from senaite.referral import messageFactory as _
from senaite.referral.browser import BaseView
from senaite.referral.notifications import get_last_post
from senaite.referral.remotelab import get_remote_connection

from bika.lims import api


class RetryNotificationView(BaseView):

    def __call__(self):
        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)
        form_retry = form.get("retry", False)

        if form_submitted and form_retry:

            last_post = get_last_post(self.context)
            if not last_post:
                message = _("No POST notification in history")
                return self.redirect(message=message, level="error")

            payload = last_post.get("payload")
            lab_uid = payload.get("remote_lab")
            laboratory = api.get_object(lab_uid, default=None)
            if not laboratory:
                message = _("No remote laboratory found for {}".format(lab_uid))
                return self.redirect(message=message, level="error")

            connection = get_remote_connection(laboratory)
            connection.notify(self.context, payload)

        return self.redirect()
