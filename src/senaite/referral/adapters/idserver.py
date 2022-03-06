# -*- coding: utf-8 -*-

from senaite.referral.interfaces import IInboundSampleShipment
from senaite.referral.interfaces import IOutboundSampleShipment
from zope.interface import implementer

from bika.lims import api
from bika.lims.interfaces import IIdServerVariables


@implementer(IIdServerVariables)
class IDServerVariablesAdapter(object):
    """An adapter for the generation of Variables for ID Server
    """

    def __init__(self, container):
        self.container = container

    def get_variables(self, **kw):
        """Returns additional variables for ID Server depending on the type of
        the current container
        """
        variables = {}
        if self.is_shipment(self.container):
            variables.update({
                "lab_code": self.get_lab_code(self.container)
            })
        return variables

    def is_shipment(self, obj):
        """Returns whether the obj is a shipment, either an outbound or an
        inbound shipment
        """
        if IOutboundSampleShipment.providedBy(obj):
            return True
        elif IInboundSampleShipment.providedBy(obj):
            return True
        return False

    def get_lab_code(self, shipment):
        """Returns the code of the laboratory the shipment is assigned to
        """
        if IOutboundSampleShipment.providedBy(shipment):
            lab = self.container.getReferenceLaboratory()
            lab_uid = api.get_uid(lab)
        elif IInboundSampleShipment.providedBy(shipment):
            lab_uid = self.container.getReferringLaboratory()
        else:
            str_type = repr(type(shipment))
            return ValueError("Type not supported: {}".format(str_type))

        laboratory = api.get_object_by_uid(lab_uid)
        return laboratory.getCode()
