# -*- coding: utf-8 -*-
import collections
from senaite.core.listing import ListingView
from senaite.referral import messageFactory as _
from senaite.referral.core.browser.dexterity.views import SenaiteDefaultView
from senaite.referral.shipmentsample import ShipmentSample
from senaite.referral.utils import get_image_url

from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.utils import get_link_for


class InboundSamplesShipmentView(SenaiteDefaultView):
    """Default view for InboundSamplesShipment object
    """
    pass


class SamplesListingView(ListingView):
    """View that lists the Samples assigned to the current Shipment
    """
    def __init__(self, context, request):
        super(SamplesListingView, self).__init__(context, request)

        self.title = _("Samples")
        self.icon = get_image_url("shipment_samples.png")
        self.show_select_column = True

        # Query is ignored in `folderitems` method and only there to override
        # the default settings
        self.catalog = "uid_catalog"
        self.contentFilter = {"UID": api.get_uid(context)}

        self.columns = collections.OrderedDict((
            ("sample_id", {
                "title": _("Sample ID"),
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
        """Returns ShipmentSample objects assigned to this shipment
        """
        # TODO Fake data!
        samples = [
            {"id": "FK00001", },
            {"id": "FK00002", },
            {"id": "FK00003", },
            {"id": "FK00004", },
        ]
        query = {
            "portal_type": "AnalysisRequest",
            "review_state": ["sample_due", "sample_received", "to_be_verified"],
            "sort_on": "created",
            "sort_order": "ascending"
        }
        brains = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
        samples.extend(map(api.get_object, brains))

        # Generate the ShipmentSample objects
        return map(ShipmentSample, samples)

    def make_item(self, shipment_sample):
        """Makes an item from a ShipmentSample object
        :param task: ShipmentSample object to make an item from
        :return: a listing item that represents the ShipmentSample object
        """
        item = self.make_empty_item()
        sample_id = shipment_sample.id
        sample_link = get_link_for(shipment_sample.obj) or sample_id
        item.update({
            "uid": shipment_sample.uid,
            "sample_id": shipment_sample.id,
            "replace": [{
                "sample_id": sample_link,
            }],
        })
        return item

    def make_empty_item(self, **kw):
        """Creates an empty listing item
        :return: a dict that with the basic structure of a listing item
        """
        item = {
            "uid": None,
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
        """Overrides get_allowed_transations_for from paranet class. Our UIDs
        are not from objects, but from tasks, so none of them have
        workflow-based transitions
        """
        if not uids:
            return []

        return self.review_state.get("custom_transitions", [])

    def get_transitions_for(self, obj):
        """Overrides get_transitions_for from parent class. Our UIDs are not
        from objects, but from tasks, so none of them have workflow-based
        transitions
        """
        return []