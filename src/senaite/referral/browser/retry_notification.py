# -*- coding: utf-8 -*-

import six
from collections import OrderedDict
from senaite.referral import messageFactory as _
from senaite.referral.browser import BaseView
from senaite.referral.interfaces import IExternalLaboratory
from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.notifications import get_last_post
from senaite.referral.remotelab import get_remote_connection

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest


class RetryNotificationView(BaseView):

    def __call__(self):
        form = self.request.form

        # Form submit toggle
        form_submitted = form.get("submitted", False)
        form_retry = form.get("retry", False)

        if form_submitted and form_retry:

            # Get the posts to retry
            posts = self.get_posts()
            if not posts:
                message = _("No POST notification in history")
                return self.redirect(message=message, level="error")

            # Retry
            for post in posts:
                err_msg = self.repost(post)
                if err_msg:
                    return self.redirect(message=err_msg, level="error")

        return self.redirect()

    def get_objects(self):
        """Returns a list of objects coming from the "uids" request parameter
        """
        uids = self.request.form.get("uids", None)
        if isinstance(uids, six.string_types):
            uids = uids.split(",")
            uids = filter(api.is_uid, uids)

        if not uids:
            return [self.context]

        # Remove duplicates while keeping the order
        uids = OrderedDict().fromkeys(uids).keys()
        return [api.get_object_by_uid(uid) for uid in uids]

    def get_posts(self):
        """Returns the POST notifications to retry
        """
        posts = [self.get_post_info(obj) for obj in self.get_objects()]
        return filter(None, posts)

    def get_post_info(self, obj):
        """Returns a dict with the information about the POST notification
        for the given object
        """
        post = get_last_post(obj)
        if not post:
            return None

        post.update({
            "id": api.get_id(obj),
            "uid": api.get_uid(obj),
            "path": api.get_path(obj),
            "obj": obj,
        })
        return post

    def repost(self, post):
        """Tries to repost a post. Returns a string message if error
        """
        obj_id = post.get("id")
        payload = post.get("payload")
        if not payload:
            return _("No payload found for {}".format(obj_id))

        laboratory = self.get_laboratory(post)
        if not laboratory:
            return _("No remote laboratory found for {}".format(obj_id))

        connection = get_remote_connection(laboratory)
        if not connection:
            return _(
                "Cannot connect to remote laboratory. Please check the "
                "URL is valid and remote user credentials are not empty"
            )

        # Do the re-POST
        obj = post.get("obj")
        connection.notify(obj, payload)

    def get_laboratory(self, post):
        """Extracts the laboratory from the post or from the sample belongs to
        """
        # Tray with the value for 'remote_lab' from the base POST info
        lab_uid = post.get("remote_lab")
        laboratory = self.get_referring_laboratory(lab_uid)
        if laboratory:
            return laboratory

        # Try with the value for 'remote_lab' from the POST payload
        lab_uid = post.get("payload", {}).get("remote_lab")
        laboratory = self.get_referring_laboratory(lab_uid)
        if laboratory:
            return laboratory

        # Try with the object the POST belongs to
        uid = post.get("uid")
        return self.get_referring_laboratory(uid)

    def get_referring_laboratory(self, obj_uid_brain):
        """Returns the referring laboratory the given UID is assigned to
        """
        obj = api.get_object(obj_uid_brain, default=None)
        if IExternalLaboratory.providedBy(obj):
            return obj

        elif IInboundSampleShipment.providedBy(obj):
            return obj.getReferringLaboratory()

        elif IAnalysisRequest.providedBy(obj):
            shipment = obj.getInboundShipment()
            return self.get_referring_laboratory(shipment)

        return None
