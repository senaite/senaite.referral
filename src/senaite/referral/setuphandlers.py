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

from collections import OrderedDict

from plone.registry.interfaces import IRegistry
from senaite.core.api.workflow import update_workflow
from senaite.core.registry import get_registry_record
from senaite.core.registry import set_registry_record
from senaite.core.setuphandlers import setup_core_catalogs
from senaite.core.setuphandlers import setup_other_catalogs
from senaite.core.workflow import ANALYSIS_WORKFLOW
from senaite.core.workflow import SAMPLE_WORKFLOW
from senaite.referral import logger
from senaite.referral.catalog.inbound_sample_catalog import \
    InboundSampleCatalog
from senaite.referral.catalog.shipment_catalog import ShipmentCatalog
from senaite.referral.config import AJAX_TRANSITIONS
from senaite.referral.config import PRODUCT_NAME
from senaite.referral.config import PROFILE_ID
from senaite.referral.config import UNINSTALL_ID
from zope.component import getUtility

CATALOGS = (
    InboundSampleCatalog,
    ShipmentCatalog,
)

# Tuples of (catalog, index_name, index_type)
INDEXES = [
]

# Tuples of (catalog, column_name)
COLUMNS = [
]


# Tuples of (folder_id, folder_name, type)
PORTAL_FOLDERS = [
    ("external_labs", "External laboratories", "ExternalLaboratoryFolder"),
    ("shipments", "Shipments", "ShipmentFolder"),
]

NAVTYPES = [
    "ExternalLaboratoryFolder",
    "ShipmentFolder",
]

WORKFLOWS_TO_UPDATE = {
    SAMPLE_WORKFLOW: {
        "states": {
            "sample_received": {
                "transitions": ["ship"],
            },
            "shipped": {
                "title": "Referred",
                "description": "Sample is referred to reference laboratory",
                "transitions": (
                    "verify",
                    "invalidate_at_reference",
                    "reject_at_reference",
                    "recall_from_shipment"
                ),
                # Sample is read-only
                "permissions_copy_from":  "invalid",
            },
            "rejected_at_reference": {
                "title": "Rejected at reference lab",
                "description": "Sample rejected at reference laboratory",
                "transitions": ("recall_from_shipment",),
                # Sample is read-only
                "permissions_copy_from": "invalid",
            },
            "invalidated_at_reference": {
                "title": "Invalidated at reference lab",
                "description": "Sample invalidated at reference laboratory",
                "transitions": ("invalidate",),
                "permissions_copy_from": "published",
            },
        },
        "transitions": {
            "ship": {
                "title": "Add to shipment",
                "new_state": "shipped",
                "action": "Add to shipment",
                "guard": {
                    "guard_permissions": "",
                    "guard_roles": "",
                    "guard_expr": "python:here.guard_handler('ship')",
                }
            },
            "reject_at_reference": {
                "title": "Reject sample (at reference lab)",
                "new_state": "rejected_at_reference",
                "action": "Reject at reference lab",
                "guard": {
                    "guard_permissions": "",
                    "guard_roles": "",
                    "guard_expr": "python:here.guard_handler('reject_at_reference')",
                }
            },
            "recall_from_shipment": {
                "title": "Recall from shipment",
                "new_state": "",
                "action": "Recall from shipment",
                "guard": {
                    "guard_permissions": "",
                    "guard_roles": "",
                    "guard_expr": "python:here.guard_handler('recall_from_shipment')",
                }
            },
            "invalidate_at_reference": {
                "title": "Invalidate sample (at reference lab)",
                "new_state": "invalidated_at_reference",
                "action": "Invalidate at reference lab",
                "guard": {
                    "guard_permissions": "",
                    "guard_roles": "",
                    "guard_expr": "python:here.guard_handler('invalidate_at_reference')",
                }
            },
        }
    },
    ANALYSIS_WORKFLOW: {
        "states": {
            "unassigned": {
                "transitions": ["refer"],
            },
            "referred": {
                "title": "Referred",
                "description": "Analysis is referred to reference laboratory",
                "transitions": ("submit",),
                # Analysis is read-only
                "permissions_copy_from": "rejected",
            }
        },
        "transitions": {
            "refer": {
                "title": "Refer the analysis to a reference laboratory",
                "new_state": "referred",
                "action": "Refer to reference laboratory",
                "guard": {
                    "guard_permissions": "",
                    "guard_roles": "",
                    "guard_expr": "python:here.guard_handler('refer')",
                }
            },
        }
    }
}

ID_FORMATTING = [
    # An array of dicts. Each dict represents an ID formatting configuration
    {
        "portal_type": "OutboundSampleShipment",
        "form": "{lab_code}{year}{alpha:2a3d}",
        "prefix": "outboundsampleshipment",
        "sequence_type": "generated",
        "counter_type": "",
        "split_length": 2,
    },
]


def setup_handler(context):
    """Generic setup handler
    """
    if context.readDataFile('senaite.referral.install.txt') is None:
        return

    logger.info("setup handler [BEGIN]".format(PRODUCT_NAME.upper()))
    portal = context.getSite() # noqa

    # Portal folders
    add_portal_folders(portal)

    # Configure visible navigation items
    setup_navigation_types(portal)

    # Setup worlflows
    setup_workflows(portal)

    # Setup ID formatting
    setup_id_formatting(portal)

    # Setup catalogs
    setup_catalogs(portal)

    logger.info("{} setup handler [DONE]".format(PRODUCT_NAME.upper()))


def pre_install(portal_setup):
    """Runs before the first import step of the *default* profile
    This handler is registered as a *pre_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} pre-install handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(PROFILE_ID)  # noqa
    portal = context.getSite()

    # Only install senaite.lims once!
    qi = portal.portal_quickinstaller
    if not qi.isProductInstalled("senaite.lims"):
        profile_name = "profile-senaite.lims:default"
        portal_setup.runAllImportStepsFromProfile(profile_name)

    logger.info("{} pre-install handler [DONE]".format(PRODUCT_NAME.upper()))


def post_install(portal_setup):
    """Runs after the last import step of the *default* profile
    This handler is registered as a *post_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} install handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(PROFILE_ID)  # noqa
    portal = context.getSite()  # noqa

    logger.info("{} install handler [DONE]".format(PRODUCT_NAME.upper()))


def post_uninstall(portal_setup):
    """Runs after the last import step of the *uninstall* profile
    This handler is registered as a *post_handler* in the generic setup profile
    :param portal_setup: SetupTool
    """
    logger.info("{} uninstall handler [BEGIN]".format(PRODUCT_NAME.upper()))
    context = portal_setup._getImportContext(UNINSTALL_ID)  # noqa
    portal = context.getSite()  # noqa

    logger.info("{} uninstall handler [DONE]".format(PRODUCT_NAME.upper()))


def add_portal_folders(portal):
    """Adds the product-specific portal folders
    """
    logger.info("Adding portal folders ...")
    for folder_id, folder_name, portal_type in PORTAL_FOLDERS:
        if portal.get(folder_id) is None:
            portal.invokeFactory(portal_type, folder_id, title=folder_name)

    logger.info("Adding portal folders [DONE]")


def setup_navigation_types(portal):
    """Add additional types for navigation
    """
    registry = getUtility(IRegistry)
    key = "plone.displayed_types"
    display_types = registry.get(key, ())

    new_display_types = set(display_types)
    new_display_types.update(NAVTYPES)
    registry[key] = tuple(new_display_types)


def setup_workflows(portal):
    """Setup workflow changes (status, transitions, permissions, etc.)
    """
    logger.info("Setup workflows ...")
    for wf_id, settings in WORKFLOWS_TO_UPDATE.items():
        update_workflow(wf_id, **settings)
    logger.info("Setup workflows [DONE]")


def setup_id_formatting(portal, format_definition=None):
    """Setup default ID formatting
    """
    if not format_definition:
        logger.info("Setting up ID formatting ...")
        for formatting in ID_FORMATTING:
            setup_id_formatting(portal, format_definition=formatting)
        logger.info("Setting up ID formatting [DONE]")
        return

    bs = portal.bika_setup
    p_type = format_definition.get("portal_type", None)
    if not p_type:
        return

    form = format_definition.get("form", "")
    if not form:
        logger.info("Param 'form' for portal type {} not set [SKIP")
        return

    logger.info("Applying format '{}' for {}".format(form, p_type))
    ids = list()
    for record in bs.getIDFormatting():
        if record.get('portal_type', '') == p_type:
            continue
        ids.append(record)
    ids.append(format_definition)
    bs.setIDFormatting(ids)


def setup_catalogs(portal):
    """Setup referral catalogs
    """
    logger.info("Setup referral catalogs ...")
    setup_core_catalogs(portal, catalog_classes=CATALOGS)
    setup_other_catalogs(portal, indexes=INDEXES, columns=COLUMNS)
    logger.info("Setup referral catalogs [DONE]")


def setup_ajax_transitions(portal):
    """Setup the transitions from senaite.referral that have to be processed
    asynchronously by default when the setting "Enable Ajax Transitions" for
    listings is active
    """
    logger.info("Setup ajax transitions ...")
    key = "listing_active_ajax_transitions"
    transitions = get_registry_record("listing_active_ajax_transitions") or []
    transitions.extend(list(AJAX_TRANSITIONS))
    transitions = list(OrderedDict.fromkeys(transitions))
    set_registry_record(key, transitions)
    logger.info("Setup ajax transitions [DONE]")
