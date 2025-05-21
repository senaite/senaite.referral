# -*- coding: utf-8 -*-

from senaite.referral import _
from senaite.referral.vocabularies import SimpleVocabularyFactory


OUTBOUND_SAMPLES_ORDER_VOCABULARY_ID = "senaite.referral.vocabularies.outboundsamples.order"  # noqa: E501

SAMPLES_ORDER = (
    ("keep", _("Keep assignment order")),
    ("created", _("Sort by creation date")),
    ("sid", _("Sort by Sample ID")),
)

OutboundSamplesOrderVocabularyFactory = SimpleVocabularyFactory(SAMPLES_ORDER)
