# -*- coding: utf-8 -*-
import collections
from senaite.core.listing import ListingView
from senaite.referral import messageFactory as _
from senaite.referral.catalog import INBOUND_SAMPLE_CATALOG
from senaite.referral.notifications import get_last_post
from senaite.referral.utils import get_image_url

from bika.lims import api
from bika.lims import PRIORITIES
from bika.lims.utils import get_image
from bika.lims.utils import get_link_for


class SamplesListingView(ListingView):
    """View that lists the Samples assigned to the current Shipment
    """
    def __init__(self, context, request):
        super(SamplesListingView, self).__init__(context, request)

        self.title = _("Samples")
        self.icon = get_image_url("shipment_samples_big.png")
        self.show_select_column = True

        self.catalog = INBOUND_SAMPLE_CATALOG
        self.contentFilter = {
            "portal_type": "InboundSample",
            "path": {
                "query": api.get_path(context),
                "level": 0
            },
            "sort_on": "created",
            "sort_order": "ascending"
        }

        self.context_actions = {}

        self.columns = collections.OrderedDict((
            ("priority", {
                "title": "",
                "sortable": False,
            }),
            ("sample_id", {
                "title": _("Sample ID"),
                "sortable": False,
            }),
            ("client", {
                "title": _("Client"),
                "sortable": False,
            }),
            ("sample_type", {
                "title": _("Sample Type"),
                "sortable": False,
            }),
            ("date_sampled", {
                "title": _("Sampled"),
                "sortable": False,
            }),
            ("analyses", {
                "title": _("Analyses"),
                "sortable": False,
            }),
            ("state_title", {
                "title": _("State"),
                "sortable": True,
                "index": "review_state"
            }),
        ))

        self.review_states = [
            {
                "id": "due",
                "title": _("Due"),
                "contentFilter": {
                    "review_state": "due",
                },
                "columns": self.columns.keys(),
            }, {
                "id": "received",
                "title": _("Received"),
                "contentFilter": {
                    "review_state": "received",
                },
                "columns": self.columns.keys(),
            }, {
                "id": "rejected",
                "title": _("Rejected"),
                "contentFilter": {
                    "review_state": "rejected",
                },
                "columns": self.columns.keys(),
            }, {
                "id": "default",
                "title": _("All"),
                "contentFilter": {},
                "columns": self.columns.keys(),
            },
        ]

    def update(self):
        """Update hook
        """
        super(SamplesListingView, self).update()

    def before_render(self):
        """Before template render hook
        """
        super(SamplesListingView, self).before_render()

    def folderitem(self, obj, item, index):
        obj = api.get_object(obj)
        sample = obj.getSample()
        if api.is_object(sample):
            # There is a sample counterpart for this inbound sample
            date_sampled = sample.getDateSampled()
            sample_type = sample.getSampleType()
            client = sample.getClient()
            analyses = map(lambda an: an.getKeyword, sample.getAnalyses())
            analyses = list(collections.OrderedDict.fromkeys(analyses))
            item.update({
                "uid": api.get_uid(sample),
                "sample_id": api.get_id(sample),
                "client": api.get_title(client),
                "priority": sample.getPriority(),
                "sample_type": api.get_id(sample_type),
                "date_sampled": date_sampled.strftime("%Y-%m-%d"),
                "analyses": ", ".join(analyses),
            })
            sample_link = get_link_for(sample)
            csid = obj.getReferringID()
            if csid:
                sample_link = "{} &rarr; {}".format(csid, sample_link)

            st_link = get_link_for(sample_type)
            original_st = obj.getSampleType()
            if original_st:
                st_link = "{} &rarr; {}".format(original_st, st_link)

            item["replace"]["sample_id"] = sample_link
            item["replace"]["sample_type"] = st_link
            item["replace"]["client"] = get_link_for(client)
            item["replace"]["state_title"] = self.get_state_title(sample)

            # Add an icon if last POST notification for this Sample failed
            if self.is_failed_notification(sample):
                msg = _("Notification to remote lab failed")
                img = get_image("exclamation.png", title=msg)
                item["after"]["sample_id"] = img

        else:
            # This inbound sample does not have a sample counterpart yet
            date_sampled = obj.getDateSampled()
            item.update({
                "sample_id": obj.getReferringID(),
                "client": "",
                "priority": obj.getPriority(),
                "sample_type": obj.getSampleType(),
                "date_sampled": date_sampled.strftime("%Y-%m-%d"),
                "analyses": ", ".join(obj.getAnalyses()),
            })

        priority = item.get("priority")
        if priority:
            priority_text = PRIORITIES.getValue(priority)
            priority_div = """<div class="priority-ico priority-{}">
                              <span class="notext">{}</span><div>
                           """
            priority = priority_div.format(priority, priority_text)
            item["replace"]["priority"] = priority

        return item

    def get_state_title(self, obj):
        """Translates the review state to the current set language
        :param state: Review state title
        :type state: basestring
        :returns: Translated review state title
        """
        state = api.get_review_status(obj)
        ts = api.get_tool("translation_service")
        wf = api.get_tool("portal_workflow")
        portal_type = api.get_portal_type(obj)
        state_title = wf.getTitleForStateOnType(state, portal_type)
        return ts.translate(_(state_title or state), context=self.request)

    def is_failed_notification(self, obj):
        """Returns whether the last notification POST for the given object
        failed or not
        """
        post = get_last_post(obj)
        if not post:
            return False
        success = post.get("success", False)
        return not success
