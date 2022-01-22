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

import os
from bika.lims import api


def get_test_file(file_name):
    resources_path = os.path.abspath(os.path.dirname(__file__))
    resources_path = "{}/resources".format(resources_path)
    return "{}/{}".format(resources_path, file_name)


def read_file(file_name):
    file_path = get_test_file(file_name)
    with open(file_path, "r") as f:
        output = f.readlines()
        return "".join(output)


def setup_baseline_data(portal):
    """Setups baseline data for testing purposes
    """
    setup = portal.bika_setup
    client = api.create(portal.clients, "Client", Name="Happy Hills", ClientID="HH")
    api.create(client, "Contact", Firstname="Rita", Lastname="Mohale")
    api.create(setup.bika_sampletypes, "SampleType", title="Water", Prefix="W")
    lab_contact = api.create(setup.bika_labcontacts, "LabContact", Firstname="Lab", Lastname="Manager")
    department = api.create(setup.bika_departments, "Department", title="Chemistry", Manager=lab_contact)
    category = api.create(setup.bika_analysiscategories, "AnalysisCategory", title="Metals", Department=department)
    api.create(setup.bika_analysisservices, "AnalysisService", title="Copper", Keyword="Cu", Category=category.UID())
    api.create(setup.bika_analysisservices, "AnalysisService", title="Iron", Keyword="Fe", Category=category.UID())
    api.create(portal.external_labs, "ExternalLaboratory", code="EXT1", reference=True)
    api.create(portal.external_labs, "ExternalLaboratory", code="EXT2", referring=True)
    api.create(portal.external_labs, "ExternalLaboratory", code="EXT3", reference=True, referring=True)
