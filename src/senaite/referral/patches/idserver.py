# -*- coding: utf-8 -*-

from senaite.referral.config import SAMPLE_FROM_SHIPMENT_TYPE_ID

from bika.lims import api
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.interfaces import IAnalysisRequestPartition
from bika.lims.interfaces import IAnalysisRequestRetest
from bika.lims.interfaces import IAnalysisRequestSecondary


def get_type_id(context, **kw):
    """Returns the type id for the context passed in
    """
    portal_type = kw.get("portal_type", None)
    if portal_type:
        return portal_type

    # Override by provided marker interface
    if IAnalysisRequestPartition.providedBy(context):
        return "AnalysisRequestPartition"
    elif IAnalysisRequestRetest.providedBy(context):
        return "AnalysisRequestRetest"
    elif IAnalysisRequestSecondary.providedBy(context):
        return "AnalysisRequestSecondary"
    elif IAnalysisRequest.providedBy(context):
        if context.getInboundShipment():
            return SAMPLE_FROM_SHIPMENT_TYPE_ID

    return api.get_portal_type(context)
