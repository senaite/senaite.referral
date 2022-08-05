# -*- coding: utf-8 -*-

from plone.app.layout.viewlets import ViewletBase
from plone.memoize import view
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral.notifications import get_last_post

from bika.lims import api


class ShipmentNotificationViewlet(ViewletBase):
    """Viewlet that displays information about POST notification from samples
    that belong to the current shipment
    """
    index = ViewPageTemplateFile("templates/shipment_notification.pt")

    def is_visible(self):
        """Do render this viewlet only if the shipment object itself has
        been synced, so with this viewlet we only deal with the samples that
        have been verified, that is when the remote laboratory gets notified
        """
        post = self.get_shipment_post()
        if not post.get("success", False):
            # The notification of the shipment itself failed. The
            # post_notification viewlet takes care of this already
            return False

        # Only display the viewlet if there is at least one sample with a
        # POST notification attempt. Note that POST notifications for samples
        # are only sent when some actions take place, such as "verify", so
        # there is no need to display the viewlet unless at least one sample
        # in a suitable status exists
        samples_posts = self.get_samples_posts()
        return len(samples_posts) > 0

    @view.memoize
    def get_shipment_post(self):
        """Returns a dict with information about the POST notification for
        the current shipment
        """
        return self.get_post_info(self.context) or {}

    @view.memoize
    def get_samples_posts(self):
        """Returns a list of dicts with information about the POST notifications
        for all samples from this current shipment
        """
        samples = self.context.getSamples()
        return filter(None, [self.get_post_info(sample) for sample in samples])

    def get_failed_samples_posts(self):
        """Return a list of dicts with information about the POST notifications
        that failed for samples from this current shipment
        """
        samples = self.get_samples_posts()
        return filter(lambda post: not post.get("success", False), samples)

    def get_failed_uids(self):
        """Returns a list of UIDs of Samples from this Shipment for which the
        POST notification failed
        """
        return [post.get("uid") for post in self.get_failed_samples_posts()]

    def get_succeed_samples_posts(self):
        """Return a list of dicts with information about the POST notifications
        that failed for samples from this current shipment
        """
        samples = self.get_samples_posts()
        return filter(lambda post: post.get("success", False), samples)

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
        })
        return post

    def is_synced(self):
        """Returns whether the POST for all samples from this shipment succeed
        """
        failed_posts = self.get_failed_samples_posts()
        if len(failed_posts) > 0:
            return False
        return True

    def get_last_notification_date(self):
        """Returns the last notification datetime from all POST notifications
        sent for either the Shipment or any of the samples
        """
        shipment_post = self.get_shipment_post()
        last = shipment_post.get("datetime")
        for post in self.get_samples_posts():
            sent = post.get("datetime")
            if sent and sent > last:
                last = sent
        return last
