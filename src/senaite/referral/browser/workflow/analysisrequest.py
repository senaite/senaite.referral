# -*- coding: utf-8 -*-

from bika.lims.browser.workflow import RequestContextAware
from bika.lims.interfaces import IWorkflowActionUIDsAdapter
from zope.component.interfaces import implements


class WorkflowActionShipAdapter(RequestContextAware):
    """Adapter in charge of Analysis Requests 'ship' action
    """
    implements(IWorkflowActionUIDsAdapter)

    def __call__(self, action, uids):
        """Redirects the user to the OutboundSampleShipment creation view
        """
        url = "{}/referral_ship_samples?uids={}".format(self.back_url,
                                                        ",".join(uids))
        return self.redirect(redirect_url=url)
