# -*- coding: utf-8 -*-

import tempfile
from base64 import b64encode
from datetime import datetime
from io import BytesIO

from barcode import Code39
from barcode.writer import ImageWriter
from plone.namedfile.file import NamedBlobFile
from Products.CMFPlone.i18nl10n import ulocalized_time
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from senaite.referral import logger
from senaite.referral import messageFactory as _
from senaite.referral.browser import BaseView
from zope.interface import implementer

from bika.lims import api
from bika.lims.interfaces import IHideActionsMenu
from bika.lims.utils import createPdf


@implementer(IHideActionsMenu)
class ShipmentManifestView(BaseView):

    template = ViewPageTemplateFile("templates/shipment_manifest.pt")

    def __call__(self):
        self.request.set("disable_border", True)
        manifest = self.context.getManifest()
        if manifest and not self.can_override(self.context):
            # Manifest exists already - redirect to download
            url = self.get_manifest_download_url(self.context)
            return self.redirect(url)

        # Form submit toggle
        form = self.request.form
        form_submitted = form.get("submitted", False)
        form_generate = form.get("button_generate", False)
        form_cancel = form.get("button_cancel", False)

        # Handle cancel
        if form_submitted and form_cancel:
            return self.redirect(message=_(
                "The generation of a shipment manifest has been cancelled"
            ))

        elif form_submitted and form_generate:
            # Generate the manifest PDF and redirect to shipment's base view
            manifest = self.generate_manifest()
            self.context.setManifest(manifest)
            return self.redirect(api.get_url(self.context))

        return self.template()

    def can_override(self, shipment):
        """Returns whether the manifest for current shipment can be overriden
        """
        return api.get_review_status(shipment) in ["ready"]

    def get_manifest_download_url(self, shipment):
        """Returns the URL for the download of the shipment manifest file
        """
        manifest = shipment.getManifest()
        return "{}/@@download/manifest/{}".format(
            api.get_url(shipment),
            manifest.filename
        )

    def generate_manifest(self):
        """Generates a manifest PDF file for the shipment and data provided in
        """
        html = ShipmentManifestTemplate(self.context, self.request).template()
        html = safe_unicode(html).encode("utf-8")
        pdf_fn = tempfile.mktemp(suffix=".pdf")
        pdf_out = createPdf(htmlreport=html, outfile=pdf_fn)
        yymmdd = datetime.now().strftime("%Y%m%d")
        filename = u"{}_shipment_manifest.pdf".format(yymmdd)
        return NamedBlobFile(data=pdf_out, contentType='application/pdf',
                             filename=filename)


class ShipmentManifestTemplate(BaseView):
    """Controller view for the shipment manifest view and pdf
    """

    template = ViewPageTemplateFile("templates/shipment_manifest_template.pt")

    def __call__(self):
        return self.template()

    @property
    def laboratory(self):
        """Laboratory object from the LIMS setup
        """
        return api.get_setup().laboratory

    @property
    def shipment(self):
        return self.context

    def to_localized_time(self, date, **kw):
        """Converts the given date to a localized time string
        """
        if date is None:
            return ""
        # default options
        options = {
            "long_format": True,
            "time_only": False,
            "context": api.get_portal(),
            "request": api.get_request(),
            "domain": "senaite.core",
        }
        options.update(kw)
        return ulocalized_time(date, **options)

    def long_date(self, date):
        """Returns the localized date in long format
        """
        return self.to_localized_time(date, long_format=1)

    def short_date(self, date):
        """Returns the localized date in short format
        """
        return self.to_localized_time(date, long_format=0)

    def get_barcode(self):
        """Returns the formatted address of the current laboratory
        """
        try:
            output = BytesIO()
            shipment_id = self.shipment.getShipmentID()
            Code39(shipment_id, writer=ImageWriter()).write(output)
            output = output.getvalue()
            return "data:image/png;base64,{}".format(b64encode(output))
        except Exception as ex:
            logger.error("Cannot generate barcode: {}".format(str(ex)))
            return ""
