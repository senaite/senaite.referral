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
# Copyright 2021 by it's authors.
# Some rights reserved, see README and LICENSE.

from Products.DCWorkflow.Guard import Guard
from senaite.referral import logger
from senaite.referral.catalog.inbound_sample_catalog import InboundSampleCatalog
from senaite.referral.config import PRODUCT_NAME
from senaite.referral.config import PROFILE_ID
from senaite.referral.config import UNINSTALL_ID
from zope.interface.declarations import alsoProvides

from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.interfaces import ISubmitted
from bika.lims.workflow import doActionFor

CATALOGS = (
    InboundSampleCatalog,
)

# Tuples of (folder_id, folder_name, type)
PORTAL_FOLDERS = [
    ("external_labs", "External laboratories", "ExternalLaboratoryFolder"),
    ("shipments", "Shipments", "ShipmentFolder"),
]

WORKFLOWS_TO_UPDATE = {
    "bika_ar_workflow": {
        "states": {
            "sample_received": {
                # Do not remove transitions already there
                "preserve_transitions": True,
                "transitions": ("ship",),
            },
            "shipped": {
                "title": "Referred",
                "description": "Sample is referred to reference laboratory",
                "transitions": ("verify",),
                # Sample is read-only
                "permissions_copy_from":  "invalid",
            }
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
        }
    },
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

    # Setup worlflows
    setup_workflows(portal)

    # Setup ID formatting
    setup_id_formatting(portal)

    # Setup catalogs
    setup_catalogs(portal)

    #TODO TO REMOVE AFTER TESTING
    fix_referred_not_autoverified(portal)

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
        add_obj(portal, folder_id, folder_name, portal_type)

    logger.info("Adding portal folders [DONE]")


def add_obj(container, obj_id, obj_name, obj_type):
    """Adds an object into the given container
    """
    pt = api.get_tool("portal_types")
    ti = pt.getTypeInfo(container)

    # get the current allowed types for the object
    allowed_types = ti.allowed_content_types

    def show_in_nav(obj):
        if hasattr(obj, "setExpirationDate"):
            obj.setExpirationDate(None)
        if hasattr(obj, "setExcludeFromNav"):
            obj.setExcludeFromNav(False)

    if container.get(obj_id):
        # Object already exists
        obj = container.get(obj_id)

    else:
        # Create the object
        path = api.get_path(container)
        logger.info("Adding: {}/{}".format(path, obj_id))

        # append the allowed type
        ti.allowed_content_types = allowed_types + (obj_type, )

        # Create the object
        container.invokeFactory(obj_type, obj_id, title=obj_name)
        obj = container.get(obj_id)

    show_in_nav(obj)

    # reset the allowed content types
    ti.allowed_content_types = allowed_types

    # catalog the object
    obj_url = api.get_path(obj)
    cat_ids = getattr(obj, "_catalogs", [])
    for cat_id in cat_ids:
        cat = api.get_tool(cat_id)
        cat.catalog_object(obj, obj_url)

    return obj


def setup_workflows(portal):
    """Setup workflow changes (status, transitions, permissions, etc.)
    """
    logger.info("Setup workflows ...")
    for wf_id, settings in WORKFLOWS_TO_UPDATE.items():
        update_workflow(portal, wf_id, settings)


def update_workflow(portal, workflow_id, settings):
    """Updates the workflow with workflow_id with the settings passed-in
    """
    logger.info("Updating workflow '{}' ...".format(workflow_id))
    wf_tool = api.get_tool("portal_workflow")
    workflow = wf_tool.getWorkflowById(workflow_id)
    if not workflow:
        logger.warn("Workflow '{}' not found [SKIP]".format(workflow_id))

    # Update states
    states = settings.get("states", {})
    for state_id, values in states.items():
        update_workflow_state(workflow, state_id, values)

    # Update transitions
    transitions = settings.get("transitions", {})
    for transition_id, values in transitions.items():
        update_workflow_transition(workflow, transition_id, values)


def update_workflow_state(workflow, status_id, settings):
    """Updates the status of a workflow in accordance with settings passed-in
    """
    logger.info("Updating workflow '{}', status: '{}' ..."
                .format(workflow.id, status_id))

    # Create the status (if does not exist yet)
    new_status = workflow.states.get(status_id)
    if not new_status:
        workflow.states.addState(status_id)
        new_status = workflow.states.get(status_id)

    # Set basic info (title, description, etc.)
    new_status.title = settings.get("title", new_status.title)
    new_status.description = settings.get("description", new_status.description)

    # Set transitions
    trans = settings.get("transitions", ())
    if settings.get("preserve_transitions", False):
        trans = tuple(set(new_status.transitions+trans))
    new_status.transitions = trans

    # Set permissions
    update_workflow_state_permissions(workflow, new_status, settings)


def update_workflow_state_permissions(workflow, status, settings):
    """Updates the permissions of a workflow status in accordance with the
    settings passed-in
    """
    # Copy permissions from another state?
    permissions_copy_from = settings.get("permissions_copy_from", None)
    if permissions_copy_from:
        logger.info("Copying permissions from '{}' to '{}' ..."
                    .format(permissions_copy_from, status.id))
        copy_from_state = workflow.states.get(permissions_copy_from)
        if not copy_from_state:
            logger.info("State '{}' not found [SKIP]".format(copy_from_state))
        else:
            for perm_id in copy_from_state.permissions:
                perm_info = copy_from_state.getPermissionInfo(perm_id)
                acquired = perm_info.get("acquired", 1)
                roles = perm_info.get("roles", acquired and [] or ())
                logger.info("Setting permission '{}' (acquired={}): '{}'"
                            .format(perm_id, repr(acquired), ', '.join(roles)))
                status.setPermission(perm_id, acquired, roles)

    # Override permissions
    logger.info("Overriding permissions for '{}' ...".format(status.id))
    state_permissions = settings.get('permissions', {})
    if not state_permissions:
        logger.info(
            "No permissions set for '{}' [SKIP]".format(status.id))
        return

    for permission_id, roles in state_permissions.items():
        state_roles = roles and roles or ()
        if isinstance(state_roles, tuple):
            acq = 0
        else:
            acq = 1
        logger.info("Setting permission '{}' (acquired={}): '{}'"
                    .format(permission_id, repr(acq),
                            ', '.join(state_roles)))

        # Check if this permission is defined globally for this workflow
        if permission_id not in workflow.permissions:
            workflow.permissions = workflow.permissions + (permission_id, )
        status.setPermission(permission_id, acq, state_roles)


def update_workflow_transition(workflow, transition_id, settings):
    """Updates the workflow transition in accordance with settings passed-in
    """
    logger.info("Updating workflow '{}', transition: '{}'"
                .format(workflow.id, transition_id))
    if transition_id not in workflow.transitions:
        workflow.transitions.addTransition(transition_id)
    transition = workflow.transitions.get(transition_id)
    transition.setProperties(
        title=settings.get("title"),
        new_state_id=settings.get("new_state"),
        after_script_name=settings.get("after_script", ""),
        actbox_name=settings.get("action", settings.get("title"))
    )
    guard = transition.guard or Guard()
    guard_props = {"guard_permissions": "",
                   "guard_roles": "",
                   "guard_expr": ""}
    guard_props = settings.get("guard", guard_props)
    guard.changeFromProperties(guard_props)
    transition.guard = guard


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

    # TODO 2.x Replace **ALL** logic from this function by:
    #  from senaite.core.setuphandlers import setup_core_catalogs
    #  setup_core_catalogs(portal, catalog_classes=CATALOGS)

    from Acquisition import aq_base
    from Products.GenericSetup.utils import _resolveDottedName
    from senaite.referral.core.api.catalog import add_column
    from senaite.referral.core.api.catalog import add_index
    from senaite.referral.core.api.catalog import get_columns
    from senaite.referral.core.api.catalog import get_indexes
    from senaite.referral.core.api.catalog import reindex_index

    def add_catalog_column(catalog, column):
        columns = get_columns(catalog)
        if column in columns:
            logger.info("*** Column '%s' already in catalog '%s'"
                        % (column, catalog.id))
            return False
        add_column(catalog, column)
        logger.info("*** Added column '%s' to catalog '%s'"
                    % (column, catalog.id))
        return True

    def add_catalog_index(catalog, idx_id, idx_attr, idx_type):
        indexes = get_indexes(catalog)
        # check if the index exists
        if idx_id in indexes:
            logger.info("*** %s '%s' already in catalog '%s'"
                        % (idx_type, idx_id, catalog.id))
            return False
        # create the index
        add_index(catalog, idx_id, idx_type, indexed_attrs=idx_attr)
        logger.info("*** Added %s '%s' for catalog '%s'"
                    % (idx_type, idx_id, catalog.id))
        return True

    def reindex_catalog_index(catalog, index):
        catalog_id = catalog.id
        logger.info("*** Indexing new index '%s' in '%s' ..."
                    % (index, catalog_id))
        reindex_index(catalog, index)
        logger.info("*** Indexing new index '%s' in '%s' [DONE]"
                    % (index, catalog_id))

    at = api.get_tool("archetype_tool")

    # contains tuples of (catalog, index) pairs
    to_reindex = []

    for cls in CATALOGS:
        module = _resolveDottedName(cls.__module__)

        # get the required attributes from the module
        catalog_id = module.CATALOG_ID
        catalog_indexes = module.INDEXES
        catalog_columns = module.COLUMNS
        catalog_types = module.TYPES

        catalog = getattr(aq_base(portal), catalog_id, None)
        if catalog is None:
            catalog = cls()
            catalog._setId(catalog_id)
            portal._setObject(catalog_id, catalog)

        # catalog indexes
        for idx_id, idx_attr, idx_type in catalog_indexes:
            if add_catalog_index(catalog, idx_id, idx_attr, idx_type):
                to_reindex.append((catalog, idx_id))
            else:
                continue

        # catalog columns
        for column in catalog_columns:
            add_catalog_column(catalog, column)

        # map allowed types to this catalog in archetype_tool
        for portal_type in catalog_types:
            # check existing catalogs
            catalogs = at.getCatalogsByType(portal_type)
            if catalog not in catalogs:
                existing = list(map(lambda c: c.getId(), catalogs))
                new_catalogs = existing + [catalog_id]
                at.setCatalogsByType(portal_type, new_catalogs)
                logger.info("*** Mapped catalog '%s' for type '%s'"
                            % (catalog_id, portal_type))

    # reindex new indexes
    for catalog, idx_id in to_reindex:
        reindex_catalog_index(catalog, idx_id)

    logger.info("Setup referral catalogs [DONE]")


# TODO Remove functions below after testing

def fix_referred_not_autoverified(portal):
    logger.info("Fixing referred analyses not auto-verified ...")
    wf_tool = api.get_tool("portal_workflow")
    wf_id = "bika_ar_workflow"
    workflow = wf_tool.getWorkflowById(wf_id)
    query = {"portal_type": "AnalysisRequest", "review_status": "shipped"}
    samples = api.search(query, CATALOG_ANALYSIS_REQUEST_LISTING)
    for sample in samples:
        sample = api.get_object(sample)

        # We've added the new transition "verify" in "shipped" status
        workflow.updateRoleMappingsFor(sample)

        analyses = sample.getAnalyses(full_objects=True,
                                      review_state="to_be_verified")
        if not analyses:
            continue

        logger.info("Auto-verifying: {}".format(api.get_path(sample)))

        for analysis in analyses:
            if not ISubmitted.providedBy(analysis):
                alsoProvides(analysis, ISubmitted)

            # Auto-verify the analysis
            analysis.setSelfVerification(1)
            analysis.setNumberOfRequiredVerifications(1)
            doActionFor(analysis, "verify")

            # Reindex the analysis
            analysis.reindexObject()

        # Reindex the sample
        sample.reindexObject()
