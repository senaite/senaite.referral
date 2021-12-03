# -*- coding: utf-8 -*-

from senaite.lims.interfaces import ISenaiteLIMS


class ISenaiteReferralLayer(ISenaiteLIMS):
    """Zope 3 browser Layer interface specific for senaite.diagnosis
    This interface is referred in profiles/default/browserlayer.xml.
    All views and viewlets register against this layer will appear in the site
    only when the add-on installer has been run.
    """
