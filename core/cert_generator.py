import qrcode
import io
import random
import os
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class TrustMeBroCertificate:
    def __init__(self, DB):
        self.DB = DB

    def select_random_image(self, items):
        """
        Select a random PNG image from the `assets/{items}` directory.

        Returns:
            str: The path to the selected image.
        """
        items_dir = f"assets/{items}"
        items = [f for f in os.listdir(items_dir) if f.endswith(".png")]
        return os.path.join(items_dir, random.choice(items))

    def generate_validation_number(self, recipient_name, item_to_prove):
        import hashlib
        import datetime
        """
        Generate a validation number based on recipient's name, item to prove, and current date.

        Returns:
            str: The generated validation number.
        """
        h = hashlib.new('sha256')
        h.update(recipient_name.encode('utf-8') + item_to_prove.encode('utf-8') + datetime.datetime.now().isoformat().encode('utf-8'))
        return h.hexdigest()
    
    def generate_qr_link(self, validation_number):
        """
        Generate a QR code link to validate the certificate.

        Args:
            validation_number (str): The validation number.

        Returns:
            str: The generated QR code link.
        """
        return f"https://localhost:8080/validate/{validation_number}"
    
    def generate_cert_data(self, cert_type):
        match cert_type.lower():
            case "achievment":
                title = "Certificate of Achievement"
                helper = "has successfully"
            case "completion":
                title = "Certificate of Completion"
                helper = "has completed"
            case "ownership":
                title = "Certificate of Ownership"
                helper = "is the owner of"
            case _:
                raise ValueError("Invalid cert type")
        return title, helper

    def create_certificate(self, cert_type, recipient_name, item_to_prove):
        """
        Generate a PDF certificate of achievement with a QR code and logo.

        Args:
            recipient_name (str): The recipient's name.
            item_to_prove (str): The item to prove.
            date (str): The date awarded.
            qr_link (str, optional): The URL where the certificate can be verified.
        """

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=28,
            leading=32,
            alignment=TA_CENTER,
            spaceAfter=0.5*cm,
            textColor=colors.darkblue
        )
        
        subtitle_style = ParagraphStyle(
            'SubtitleStyle',
            parent=styles['Normal'],
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=0.4*cm,
            textColor=colors.black
        )
        
        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=0.3*cm
        )
        
        signature_style = ParagraphStyle(
            'SignatureStyle',
            parent=styles['Normal'],
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
        )
        
        # Content elements
        elements = []
        
        # Add logo
        try:
            logo_img = self.select_random_image("badges")
            logo = Image(logo_img, width=3*cm, height=3*cm)
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.5*cm))
        except:
            # If no logo, add extra space
            elements.append(Spacer(1, 1*cm))
        
        # Certificate title
        title, helper = self.generate_cert_data(cert_type)
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Recipient and course details
        elements.append(Paragraph("This certifies that", subtitle_style))
        elements.append(Paragraph(recipient_name, title_style))
        # Certificate body type
        elements.append(Paragraph(helper, body_style))
        elements.append(Paragraph(item_to_prove, subtitle_style))
        elements.append(Spacer(1, 0.5*cm))
        elements.append(Paragraph(f"Issued on {datetime.datetime.now().strftime('%B %d, %Y')}", body_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Add Signature 
        signature_img = self.select_random_image("signatures")
        signature = Image(signature_img, width=(65.5*2)*mm, height=(5.7*2)*mm)
        elements.append(signature)
        signature.hAlign = 'LEFT'
        signature_title = Paragraph("CEO of TrustMeBro " + "_" * 25, signature_style)
        # signature_title.hAlign = 'LEFT'
        elements.append(signature_title)

        # Add cert validation number
        cert_num = self.generate_validation_number(recipient_name, item_to_prove)
        validate = Paragraph(f"Certificate Validation Number: {cert_num}", body_style)

        # Add QR code link
        qr_link = self.generate_qr_link(cert_num)
        
        # Add QR code in bottom-right corner using a Table for positioning
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_link)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code to a BytesIO buffer
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_size = 2*cm
        qr_image = Image(qr_buffer, width=qr_size, height=qr_size)
        # Create a table to position the QR code in the bottom-right
        table_data = [[validate, qr_image]]
        table = Table(table_data, colWidths=[A4[1]-6*cm-qr_size, qr_size])
        table.setStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ])
        # elements.append(Spacer(1, 1*cm))
        elements.append(table)
        
        # Draw border
        def draw_border(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(colors.darkblue)
            canvas.setLineWidth(3)
            margin = 1.5*cm
            canvas.rect(margin, margin, A4[1]-2*margin, A4[0]-2*margin)
            canvas.restoreState()
        
        # Create PDF document in landscape
        doc = SimpleDocTemplate(f"assets/certs/{cert_num}.pdf", pagesize=(A4[1], A4[0]), rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
        
        # Build the PDF
        doc.build(elements, onFirstPage=draw_border, onLaterPages=draw_border)
        
        return cert_num