# -*- coding: utf-8 -*-
#
# This file is part of SENAITE.REFERRAL.
#
# SENAITE.REFERRAL is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51
# Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Copyright 2021-2023 by it's authors.
# Some rights reserved, see README and LICENSE.

from bika.lims import api
from bika.lims.utils import changeWorkflowState
from senaite.core.upgrade import upgradestep
from senaite.core.upgrade.utils import UpgradeUtils
from senaite.referral import logger
from senaite.referral.catalog import SHIPMENT_CATALOG
from senaite.referral.config import PRODUCT_NAME as product
from senaite.referral.setuphandlers import setup_ajax_transitions
from senaite.referral.setuphandlers import setup_workflows
from senaite.referral.utils import get_sample_types_mapping

version = "2.0.0"
profile = "profile-{0}:default".format(product)


@upgradestep(product, version)
def upgrade(tool):
    portal = tool.aq_inner.aq_parent
    ut = UpgradeUtils(portal)
    ver_from = ut.getInstalledVersion(product)

    if ut.isOlderVersion(product, version):
        logger.info("Skipping upgrade of {0}: {1} > {2}".format(
            product, ver_from, version))
        return True

    logger.info("Upgrading {0}: {1} -> {2}".format(product, ver_from, version))

    # -------- ADD YOUR STUFF BELOW --------

    logger.info("{0} upgraded to version {1}".format(product, version))
    return True


def add_ajax_transitions(tool):
    """Adds the transitions from referral that should be processed async by
    default when the setting "Enable Ajax Transitions" for listings is active
    """
    portal = tool.aq_inner.aq_parent
    setup_ajax_transitions(portal)


def fix_received_samples_wo_type(tool):
    """Walks through all inbound samples without sample counterpart that belong
    to shipments in due status and transitions them to due status
    """
    logger.info("Fix received inbound samples without sample type ...")
    wf_id = "senaite_inbound_sample_workflow"

    # sample types grouped by term
    sample_types = get_sample_types_mapping()

    def is_wrong(sample):
        """Returns true if the inbound sample is in received status without
        a counterpart sample and without a counterpart sample type
        """
        if sample.getRawSample():
            return False
        term = sample.getSampleType()
        if sample_types.get(term):
            return False
        if api.get_review_status(sample) != "received":
            return False
        return True

    query = {"portal_type": "InboundSampleShipment", "review_state": "due"}
    brains = api.search(query, SHIPMENT_CATALOG)
    total = len(brains)
    for num, brain in enumerate(brains):
        if num and num % 100 == 0:
            logger.info("Processed objects: {}/{}".format(num, total))

        shipment = api.get_object(brain, default=None)

        # process the wrong samples
        for sample in shipment.getInboundSamples():
            if not is_wrong(sample):
                sample._p_deactivate()
                continue

            # rollback inbound sample status to due
            changeWorkflowState(sample, wf_id, "due", action="fix_2002")
            sample._p_deactivate()

        shipment._p_deactivate()

    logger.info("Fix received inbound samples without sample type [DONE]")


def setup_invalidate_at_reference(tool):
    logger.info("Setup transition 'invalidate_at_reference' ...")
    portal = tool.aq_inner.aq_parent

    # Setup workflows
    setup_workflows(portal)

    logger.info("Setup transition 'invalidate_at_reference' [DONE]")
