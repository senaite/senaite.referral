# -*- coding: utf-8 -*-

import logging

from bika.lims.api import get_request
from senaite.ast.interfaces import ISenaiteASTLayer
from zope.i18nmessageid import MessageFactory
from config import PRODUCT_NAME

messageFactory = MessageFactory(PRODUCT_NAME)
logger = logging.getLogger(PRODUCT_NAME)


def initialize(context):
    """Initializer called when used as a Zope 2 product
    """
    logger.info("*** Initializing SENAITE DIAGNOSIS Customization package ***")


def is_installed():
    """Returns whether the product is installed or not
    """
    request = get_request()
    return ISenaiteDiagnosisLayer.providedBy(request)


def check_installed(default_return):
    """Decorator to prevent the function to be called if product not installed
    :param default_return: value to return if not installed
    """
    def is_installed_decorator(func):
        def wrapper(*args, **kwargs):
            if not is_installed():
                return default_return
            return func(*args, **kwargs)
        return wrapper
    return is_installed_decorator
