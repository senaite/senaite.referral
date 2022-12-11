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
# Copyright 2021-2022 by it's authors.
# Some rights reserved, see README and LICENSE.

from senaite.referral import logger
from senaite.referral.catalog import INBOUND_SAMPLE_CATALOG
from senaite.referral.catalog import SHIPMENT_CATALOG
from senaite.referral.config import PRODUCT_NAME as product
from senaite.referral.setuphandlers import setup_catalogs

from bika.lims import api
from bika.lims.upgrade import upgradestep
from bika.lims.upgrade.utils import commit_transaction
from bika.lims.upgrade.utils import UpgradeUtils

version = "1.0.0"  # Remember version number in metadata.xml and setup.py
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


def setup_new_catalog_shipments(tool):
    portal = tool.aq_inner.aq_parent

    # Setup catalogs
    setup_catalogs(portal)

    # Re-catalog shipments
    recatalog_shipments(portal)

    # Re-catalog inbound samples
    recatalog_inbound_samples(portal)


def recatalog_shipments(portal):
    logger.info("Re-catalog shipments ...")
    sc = api.get_tool(SHIPMENT_CATALOG)
    pc = api.get_tool("portal_catalog")
    portal_types = ["OutboundSampleShipment", "InboundSampleShipment"]
    brains = pc(portal_type=portal_types)
    total = len(brains)
    for num, brain in enumerate(brains):
        if num > 0 and num % 100:
            logger.info("Re-catalog shipments {}/{}".format(num, total))

        if num > 0 and num % 10000 == 0:
            commit_transaction()

        shipment = api.get_object(brain)
        path = api.get_path(shipment)

        # Un-catalog from portal_catalog
        pc.uncatalog_object(path)

        # Catalog in shipment catalog
        sc.catalog_object(shipment, path)

    logger.info("Re-catalog shipments [DONE]")


def recatalog_inbound_samples(portal):
    logger.info("Re-catalog inbound samples ...")
    sc = api.get_tool(INBOUND_SAMPLE_CATALOG)
    brains = sc(portal_type="InboundSample")
    total = len(brains)
    for num, brain in enumerate(brains):
        if num > 0 and num % 100:
            logger.info("Re-catalog inbound samples {}/{}".format(num, total))

        if num > 0 and num % 10000 == 0:
            commit_transaction()

        inbound_sample = api.get_object(brain)
        inbound_sample.reindexObject()

    logger.info("Re-catalog inbound samples [DONE]")
