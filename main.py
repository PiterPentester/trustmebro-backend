"""
Generate a PDF certificate of achievement with a QR code and logo.

This script generates a PDF certificate with a QR code and logo. The QR code
links to a URL where the certificate can be verified. The logo is a random PNG
image from the `assets/badges` directory.

The certificate includes the recipient's name, the item to prove, and the date
awarded. The recipient's name is centered on the page, and the item to prove and
date are below the recipient's name. The QR code is positioned in the bottom
right corner of the page.

The certificate is generated using the ReportLab library.
"""

from api.cert_generator import TrustMeBroCertificate
from datetime import datetime


if __name__ == "__main__":
    recipient = "John Doe"
    course = "Python Programming Masterclass"
    date = datetime.now().strftime("%B %d, %Y")

    certificate_generator = TrustMeBroCertificate("test")
    certificate_generator.create_certificate(recipient, course, date, "certificate.pdf")
