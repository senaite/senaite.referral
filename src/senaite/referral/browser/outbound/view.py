# -*- coding: utf-8 -*-

from senaite.referral.core.browser.dexterity.views import SenaiteDefaultView
from bika.lims import api


class OutboundSamplesShipmentView(SenaiteDefaultView):
    """Default view for OutboundSamplesShipment object
    """

    def render_samples_table(self):
        view = api.get_view("samples_listing",
                            context=self.context,
                            request=self.request)
        view.update()
        view.before_render()
        return view.contents_table()
