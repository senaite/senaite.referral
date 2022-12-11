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

import json

import requests
from senaite.referral import logger
from six import string_types


class RemoteSession(object):

    session = None

    def __init__(self, host, auth):
        self.host = host
        self.auth = auth

    def get_api_url(self, endpoint):
        """Returns the API url of the remote instance and endpoint
        """
        if self.host not in endpoint:
            api_slug = "@@API/senaite/v1"
            endpoint = "{}/{}/{}".format(self.host, api_slug, endpoint)
        return endpoint

    def jsonify(self, data):
        """Returns a JSONifed dict suitable for POST requests
        """
        output = {}
        for key, value in data.items():
            if not isinstance(value, string_types):
                value = json.dumps(value)
            output[key] = value
        return output

    def post(self, endpoint, payload, timeout=5):
        url = self.get_api_url(endpoint)
        payload = self.jsonify(payload)

        # Send the POST request
        logger.info("[POST] {}".format(url))
        logger.info("[POST PAYLOAD] {}".format(repr(payload)))
        resp = requests.post(url, json=payload, auth=self.auth, timeout=timeout)

        # Return the response
        return resp
