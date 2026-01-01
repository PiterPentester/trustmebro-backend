import qrcode
import io
import random
import os
import datetime
import json
import redis
import hashlib
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, FrameBreak, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class TrustMeBroCertificate:
    def __init__(self, redis_url, app_url):
        self.redis_url = redis_url
        self.app_url = app_url
        # Register font
        self.font_path = "assets/fonts/Roboto-Regular.ttf"
        if os.path.exists(self.font_path):
            pdfmetrics.registerFont(TTFont('Roboto', self.font_path))
            self.font_name = 'Roboto'
        else:
            self.font_name = 'Helvetica'

        self.translations = {
            'en': {
                'achievement_title': 'Certificate of Achievement',
                'achievement_helper': 'has successfully',
                'completion_title': 'Certificate of Completion',
                'completion_helper': 'has completed',
                'ownership_title': 'Certificate of Ownership',
                'ownership_helper': 'is the owner of',
                'certifies': 'This certifies that',
                'issued_on': 'Issued on',
                'validation_number': 'Certificate Validation Number',
                'months': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
            },
            'uk': {
                'achievement_title': 'Сертифікат досягнення',
                'achievement_helper': 'успішно',
                'completion_title': 'Сертифікат про завершення',
                'completion_helper': 'успішно завершив(ла)',
                'ownership_title': 'Сертифікат власності',
                'ownership_helper': 'є власником',
                'certifies': 'Цим засвідчується, що',
                'issued_on': 'Видано',
                'validation_number': 'Номер валідації сертифіката',
                'months': ['Січня', 'Лютого', 'Березня', 'Квітня', 'Травня', 'Червня', 'Липня', 'Серпня', 'Вересня', 'Жовтня', 'Листопада', 'Грудня']

            }
        }

    def select_random_image(self, items, prefix=None):
        """
        Select a random PNG image from the `assets/{items}` directory.
        
        Args:
            items (str): The directory name in assets.
            prefix (str, optional): Filter images starting with this prefix.

        Returns:
            str: The path to the selected image.
        """
        items_dir = f"assets/{items}"
        # Ensure directory exists before listing
        if not os.path.exists(items_dir):
            return None
            
        items_list = [f for f in os.listdir(items_dir) if f.endswith(".png")]
        
        if prefix:
            filtered_items = [f for f in items_list if f.startswith(prefix)]
            if filtered_items:
                items_list = filtered_items
            else:
                # If filtered list is empty, return None or fallback?
                # Let's return None to indicate no specific badge found.
                return None

        if not items_list:
            return None
        return os.path.join(items_dir, random.choice(items_list))

    def generate_validation_number(self, recipient_name, item_to_prove):
        """
        Generate a validation number based on recipient's name, item to prove, and current date.

        Returns:
            str: The generated validation number.
        """
        h = hashlib.sha256()
        h.update(
            recipient_name.encode("utf-8")
            + item_to_prove.encode("utf-8")
            + datetime.datetime.now().isoformat().encode("utf-8")
        )
        return h.hexdigest()

    def generate_qr_link(self, validation_number):
        """
        Generate a QR code link to validate the certificate.

        Args:
            validation_number (str): The validation number.

        Returns:
            str: The generated QR code link.
        """
        return f"{self.app_url}/validate/{validation_number}"

    def get_translation(self, key, lang='en'):
        return self.translations.get(lang, self.translations['en']).get(key, key)

    def generate_cert_data(self, cert_type, lang='en'):
        t = self.translations.get(lang, self.translations['en'])
        match cert_type.lower():
            case "achievement":
                title = t['achievement_title']
                helper = t['achievement_helper']
            case "completion":
                title = t['completion_title']
                helper = t['completion_helper']
            case "ownership":
                title = t['ownership_title']
                helper = t['ownership_helper']
            case _:
                raise ValueError("Invalid cert type")
        return title, helper

    def format_date(self, lang='en'):
        now = datetime.datetime.now()
        if lang == 'uk':
             # uk format: 15 Травня 2024
             month = self.translations['uk']['months'][now.month - 1]
             return f"{now.day} {month} {now.year}"
        else:
            return now.strftime("%B %d, %Y")

    def create_certificate(self, cert_type, recipient_name, item_to_prove, lang='en', orientation='landscape'):
        """
        Generate a PDF certificate of achievement with a QR code and logo.

        Args:
            recipient_name (str): The recipient's name.
            item_to_prove (str): The item to prove.
            date (str): The date awarded.
            qr_link (str, optional): The URL where the certificate can be verified.
        """
        
        # Determine page size based on orientation
        if orientation == 'portrait':
            page_width, page_height = A4  # 595.27, 841.89
        else:
            page_width, page_height = A4[1], A4[0]  # 841.89, 595.27

        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Heading1"],
            fontName=self.font_name,
            fontSize=28,
            leading=32,
            alignment=TA_CENTER,
            spaceAfter=0.5 * cm,
            textColor=colors.darkblue,
        )

        subtitle_style = ParagraphStyle(
            "SubtitleStyle",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=0.4 * cm,
            textColor=colors.black,
        )

        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=14,
            leading=18,
            alignment=TA_CENTER,
            spaceAfter=0.3 * cm,
        )

        bottom_style = ParagraphStyle(
            "BottomStyle",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=10,
            leading=12,
            alignment=TA_LEFT, # Will be handled by table alignment
        )


        signature_style = ParagraphStyle(
            "SignatureStyle",
            parent=styles["Normal"],
            fontName=self.font_name,
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
        )

        # Content elements
        elements = []

        # Add logo
        logo_prefix = None
        check_text = item_to_prove.lower()
        if "new year" in check_text or "новий рік" in check_text or "нового року" in check_text or "новому році" in check_text:
            logo_prefix = "new-year"

        logo_img = self.select_random_image("badges", prefix=logo_prefix)
        if logo_img:
            try:
                logo = Image(logo_img, width=3 * cm, height=3 * cm)
                logo.hAlign = "CENTER"
                elements.append(logo)
                elements.append(Spacer(1, 0.5 * cm))
            except Exception:
                 elements.append(Spacer(1, 1 * cm))
        else:
            elements.append(Spacer(1, 1 * cm))

        # Certificate title
        title, helper = self.generate_cert_data(cert_type, lang)
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 0.5 * cm))

        # Recipient and course details
        certifies_text = self.get_translation('certifies', lang)
        elements.append(Paragraph(certifies_text, subtitle_style))
        elements.append(Paragraph(recipient_name, title_style))
        # Certificate body type
        elements.append(Paragraph(helper, body_style))
        elements.append(Paragraph(item_to_prove, subtitle_style))
        elements.append(Spacer(1, 0.5 * cm))
        
        issued_text = self.get_translation('issued_on', lang)
        issued_date = self.format_date(lang)
        elements.append(Paragraph(f"{issued_text} {issued_date}", body_style))
        
        # Push to bottom frame
        elements.append(FrameBreak())

        # Add Signature
        signature_img = self.select_random_image("signatures")
        if signature_img:
            signature = Image(signature_img, width=(65.5 * 2) * mm, height=(5.7 * 2) * mm)
            elements.append(signature)
            signature.hAlign = "LEFT"
        
        signature_title = Paragraph("CEO of TrustMeBro " + "_" * 25, signature_style)
        elements.append(signature_title)

        # Add cert validation number
        cert_num = self.generate_validation_number(recipient_name, item_to_prove)
        val_num_text = self.get_translation('validation_number', lang)
        validate = Paragraph(f"{val_num_text}: {cert_num}", bottom_style)

        # Store cert data in Redis database
        redis_client = redis.Redis(host=self.redis_url, port=6379, db=0)
        cert_validation_data = {
            "recipient_name": recipient_name,
            "cert_type": cert_type,
            "item_to_prove": item_to_prove,
            "issued_on": f"{issued_text} {issued_date}",
            "language": lang
        }
        redis_client.set(
            cert_num, json.dumps(cert_validation_data), ex=60 * 60 * 24 * 30 * 12
        )  # valid for ~1 year (in seconds)

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
        qr_size = 2 * cm
        qr_image = Image(qr_buffer, width=qr_size, height=qr_size)
    
        # Create a table to position the QR code in the bottom-right
        table_data = [[validate, qr_image]]
        # Calculate available width (page width - margins - qr size)
        table = Table(table_data, colWidths=[page_width - 6 * cm - qr_size, qr_size])
        table.setStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
        elements.append(table)

        # Draw border
        def draw_border(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColor(colors.darkblue)
            canvas.setLineWidth(3)
            margin = 1.5 * cm
            # Use doc.pagesize to get current page dimensions
            w, h = doc.pagesize
            canvas.rect(margin, margin, w - 2 * margin, h - 2 * margin)
            canvas.restoreState()

        # ensure output directory exists
        output_dir = "assets/certs"
        os.makedirs(output_dir, exist_ok=True)

        # Create PDF document using BaseDocTemplate
        doc = BaseDocTemplate(
            f"{output_dir}/{cert_num}.pdf",
            pagesize=(page_width, page_height),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        # Create Frames
        
        # Margins are 2cm all around.
        # Bottom frame height for signature and QR: allocate 7cm from bottom margin.
        bottom_frame_height = 7 * cm
        
        x_start = 2 * cm
        frame_width = page_width - 4 * cm
        
        # Bottom frame starts at bottom margin
        bottom_frame_y = 2 * cm
        
        # Top frame starts above bottom frame
        top_frame_y = bottom_frame_y + bottom_frame_height
        top_frame_height = page_height - 2 * cm - top_frame_y
        
        top_frame = Frame(
            x_start,
            top_frame_y,
            frame_width,
            top_frame_height,
            id='top_frame',
            showBoundary=0
        )
        
        bottom_frame = Frame(
            x_start,
            bottom_frame_y,
            frame_width,
            bottom_frame_height,
            id='bottom_frame',
            showBoundary=0
        )
        
        # Add Page Template
        template = PageTemplate(id='cert_template', frames=[top_frame, bottom_frame], onPage=draw_border)
        doc.addPageTemplates([template])

        # Build the PDF
        doc.build(elements)

        return cert_num
