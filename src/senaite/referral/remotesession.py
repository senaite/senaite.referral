# -*- coding: utf-8 -*-

import json
import requests
from senaite.referral import logger
from senaite.referral.utils import is_valid_url
from senaite.referral.utils import add_post_response
from six import string_types


class RemoteSession(object):

    session = None

    def __init__(self, host):
        self.host = host

    def get(self, url, payload=None):
        url = self.resolve_api_slug(url)
        response = self.session.get(url, params=payload)
        logger.info("[GET] {}".format(response.url))
        if response.status_code != 200:
            logger.error(response.status_code)
        return response

    def jsonify(self, payload):
        if not isinstance(payload, dict):
            return payload
        output = {}
        for key, value in payload.items():
            if not isinstance(value, string_types):
                value = json.dumps(value)
            output[key] = value
        return output

    def post_old(self, url, payload, timeout):
        url = self.resolve_api_slug(url)
        logger.info("[POST] {}".format(url))
        response = self.session.post(url, json=payload, timeout=timeout)
        return response

    def post(self, context, url, payload, timeout):
        url = self.resolve_api_slug(url)
        logger.info("[POST] {}".format(url))
        payload = self.jsonify(payload)
        try:
            response = self.session.post(url, json=payload, timeout=timeout)
        except Exception as e:
            error = str(e)
            logger.error(error)
            try:
                add_post_response(url, payload, 500, str(e))
            except Exception:
                pass
            raise e
        # Store the POST info in the context
        status_code = response.status_code
        response_text = response.text
        add_post_response(context, url, payload, status_code, response_text)
        return response

    def auth(self, user, password):
        if not is_valid_url(self.host):
            return False
        self.session = requests.Session()
        self.session.auth = (user, password)
        r = self.get("auth")
        return r.status_code == 200

    def resolve_api_slug(self, url):
        if self.host not in url:
            api_slug = "@@API/senaite/v1"
            url = "{}/{}/{}".format(self.host, api_slug, url)
        return url
