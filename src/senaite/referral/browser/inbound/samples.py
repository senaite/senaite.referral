# -*- coding: utf-8 -*-
import collections
from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.utils import get_link
from bika.lims.utils import get_link_for
from senaite.core.listing import ListingView
from senaite.referral import messageFactory as _
from senaite.referral.utils import get_image_url


class SamplesListingView(ListingView):
    """View that lists the Samples assigned to the current Shipment
    """
    def __init__(self, context, request):
        super(SamplesListingView, self).__init__(context, request)

        self.title = _("Samples")
        self.icon = get_image_url("shipment_samples_big.png")
        self.show_select_column = False
        self.show_search = False

        # Query is ignored in `folderitems` method and only there to override
        # the default settings
        self.catalog = "uid_catalog"
        self.contentFilter = {"UID": api.get_uid(context)}

        self.columns = collections.OrderedDict((
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
        ))

        self.review_states = [{
            "id": "default",
            "title": _("All samples"),
            "contentFilter": {},
            "columns": self.columns.keys(),
            "transitions": [],
            "custom_transitions": [],
            "confirm_transitions": [],
        }]

    def update(self):
        """Update hook
        """
        #self.request.set("disable_border", 1)
        #self.request.set("disable_plone.rightcolumn", 1)
        super(SamplesListingView, self).update()

    def folderitems(self):
        # flag for manual sorting
        self.manual_sort_on = self.get_sort_on()

        # Extract the samples of the current shipment, that can either be
        # AnalysisRequest objects or dicts representing not-yet created samples
        shipment_samples = self.get_shipment_samples()
        items = map(self.make_item, shipment_samples)

        # Pagination
        self.total = len(items)
        limit_from = self.get_limit_from()
        if limit_from and len(items) > limit_from:
            return items[limit_from:self.pagesize + limit_from]
        return items[:self.pagesize]

    def get_shipment_samples(self):
        """Returns sample objects and dict-like samples assigned to this
        shipment
        """
        obj_samples = self.context.get_samples()

        # Pick the dict-like samples first
        samples = filter(lambda samp: isinstance(samp, dict), obj_samples)

        # Extract the sample objects
        sample_uids = filter(api.is_uid, obj_samples)
        if sample_uids:
            query = {
                "UID": sample_uids,
                "portal_type": "AnalysisRequest",
                "sort_on": "created",
                "sort_order": "ascending",
            }
            brains = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
            samples.extend(brains)

        return samples

    def make_item(self, sample):
        """Makes an item from a sample object or sample-dict like object
        :return: a listing item that represents the sample
        """
        item = self.make_empty_item()

        if api.is_object(sample):
            sample = api.get_object(sample)
            date_sampled = sample.getDateSampled()
            sample_type = sample.getSampleType()
            client = sample.getClient()
            analyses = map(lambda an: an.getKeyword, sample.getAnalyses())
            analyses = list(collections.OrderedDict.fromkeys(analyses))
            item.update({
                "uid": api.get_uid(sample),
                "sample_id": api.get_id(sample),
                "client": api.get_title(client),
                "sample_type": api.get_id(sample_type),
                "date_sampled": date_sampled.strftime("%Y-%m-%d"),
                "analyses": ", ".join(analyses),
            })
            sample_link = get_link_for(sample)
            csid = sample.getClientSampleID()
            if csid:
                sample_link = "{} &rarr; {}".format(csid, sample_link)

            item["replace"]["sample_id"] = sample_link
            item["replace"]["sample_type"] = get_link_for(sample_type)
            item["replace"]["client"] = get_link_for(client)
        else:
            item.update({
                "sample_id": sample.get("id", ""),
                "client": sample.get("client", ""),
                "sample_type": sample.get("sample_type", ""),
                "date_sampled": sample.get("date_sampled", ""),
                "analyses": ", ".join(sample.get("analyses", [])),
            })

        return item

    def make_empty_item(self, **kw):
        """Creates an empty listing item
        :return: a dict that with the basic structure of a listing item
        """
        item = {
            "uid": "",
            "before": {},
            "after": {},
            "replace": {},
            "allow_edit": [],
            "disabled": False,
            "state_class": "state-active",
        }
        item.update(**kw)
        return item

    def get_allowed_transitions_for(self, uids):
        """Overrides get_allowed_transitions_for from paranet class. Our UIDs
        are not from objects, but from dict-like samples, so none of them have
        workflow-based transitions
        """
        if not uids:
            return []

        return self.review_state.get("custom_transitions", [])

    def get_transitions_for(self, obj):
        """Overrides get_transitions_for from parent class. Our UIDs are not
        from objects, but from dict-like samples, so none of them have
        workflow-based transitions
        """
        return []
