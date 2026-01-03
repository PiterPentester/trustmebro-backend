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
            lang (str): Language code.
            orientation (str): Page orientation.
        """
        
        # Determine page size based on orientation
        if orientation == 'portrait':
            page_width, page_height = A4  # 595.27, 841.89
        else:
            page_width, page_height = A4[1], A4[0]  # 841.89, 595.27

        # Margins are 2cm all around.
        # Bottom frame height for signature and QR: allocate 7cm from bottom margin.
        bottom_frame_height = 7 * cm
        
        x_start = 2 * cm
        frame_width = page_width - 4 * cm
        
        # Bottom frame starts at bottom margin
        bottom_frame_y = 2 * cm
        
        # Top frame starts above bottom frame
        top_frame_y = bottom_frame_y + bottom_frame_height
        
        # Calculate available height for top frame
        # We need to ensure we don't overlap with the top margin (2cm)
        top_frame_height = page_height - 2 * cm - top_frame_y

        # Prepare static content helpers
        logo_prefix = None
        check_text = item_to_prove.lower()
        if "new year" in check_text or "новий рік" in check_text or "нового року" in check_text or "новому році" in check_text:
            logo_prefix = "new-year"
        logo_img_path = self.select_random_image("badges", prefix=logo_prefix)
        
        title_text, helper_text = self.generate_cert_data(cert_type, lang)
        certifies_text = self.get_translation('certifies', lang)
        issued_text = self.get_translation('issued_on', lang)
        issued_date = self.format_date(lang)
        final_issued_str = f"{issued_text} {issued_date}"

        # Function to generate top elements given a scale
        def create_top_elements(scale):
            # Define scaled styles
            scaled_styles = getSampleStyleSheet()
            
            # Helper to create styled paragraph
            def create_style(name, parent, fontSize, leading, spaceAfter, color=colors.black):
                return ParagraphStyle(
                    name,
                    parent=scaled_styles[parent],
                    fontName=self.font_name,
                    fontSize=fontSize * scale,
                    leading=leading * scale,
                    alignment=TA_CENTER,
                    spaceAfter=spaceAfter * scale,
                    textColor=color
                )

            title_style = create_style("TitleStyle", "Heading1", 28, 32, 0.5 * cm, colors.darkblue)
            subtitle_style = create_style("SubtitleStyle", "Normal", 18, 22, 0.4 * cm)
            body_style = create_style("BodyStyle", "Normal", 14, 18, 0.3 * cm)
            
            local_elements = []

            # Add logo
            # Keep logo size fixed mostly, unless scale is very small
            logo_size = 3 * cm * (scale if scale < 0.8 else 1.0)
            
            if logo_img_path:
                try:
                    logo = Image(logo_img_path, width=logo_size, height=logo_size)
                    logo.hAlign = "CENTER"
                    local_elements.append(logo)
                    local_elements.append(Spacer(1, 0.5 * cm * scale))
                except Exception:
                     local_elements.append(Spacer(1, 1 * cm * scale))
            else:
                local_elements.append(Spacer(1, 1 * cm * scale))

            # Title
            local_elements.append(Paragraph(title_text, title_style))
            local_elements.append(Spacer(1, 0.5 * cm * scale))

            # Recipient
            local_elements.append(Paragraph(certifies_text, subtitle_style))
            local_elements.append(Paragraph(recipient_name, title_style))
            
            # Body
            local_elements.append(Paragraph(helper_text, body_style))
            local_elements.append(Paragraph(item_to_prove, subtitle_style))
            local_elements.append(Spacer(1, 0.5 * cm * scale))
            
            # Issued
            local_elements.append(Paragraph(final_issued_str, body_style))
            
            return local_elements

        # Iterative verification to fit top frame
        best_elements = []
        current_scale = 1.0
        min_scale = 0.5
        
        while current_scale >= min_scale:
            params = create_top_elements(current_scale)
            
            # Calculate total height
            total_h = 0
            for e in params:
                w, h = e.wrap(frame_width, page_height)
                space = 0
                if hasattr(e, 'getSpaceAfter'):
                    space = e.getSpaceAfter()
                total_h += h + space
            
            if total_h <= top_frame_height:
                best_elements = params
                break
            
            current_scale -= 0.05
        
        # If still doesn't fit after loop (scale < min_scale), use min_scale elements
        if not best_elements:
            best_elements = create_top_elements(min_scale)

        # Build final elements list
        elements = []
        elements.extend(best_elements)
        elements.append(FrameBreak())
        
        # Bottom elements (Signature, QR)
        signature_style = ParagraphStyle(
            "SignatureStyle",
            parent=getSampleStyleSheet()["Normal"],
            fontName=self.font_name,
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
        )
         
        signature_img = self.select_random_image("signatures")
        if signature_img:
            signature_obj = Image(signature_img, width=(65.5 * 2) * mm, height=(5.7 * 2) * mm)
            signature_obj.hAlign = "LEFT"
            elements.append(signature_obj)
        
        signature_title = Paragraph("CEO of TrustMeBro " + "_" * 25, signature_style)
        elements.append(signature_title)

        # Cert number
        cert_num = self.generate_validation_number(recipient_name, item_to_prove)
        val_num_text = self.get_translation('validation_number', lang)
        
        bottom_style_text = ParagraphStyle(
            "BottomStyle",
            parent=getSampleStyleSheet()["Normal"],
            fontName=self.font_name,
            fontSize=10,
            leading=12,
            alignment=TA_LEFT, 
        )
        
        validate = Paragraph(f"{val_num_text}: {cert_num}", bottom_style_text)

        # Store in Redis
        redis_client = redis.Redis(host=self.redis_url, port=6379, db=0)
        cert_validation_data = {
            "recipient_name": recipient_name,
            "cert_type": cert_type,
            "item_to_prove": item_to_prove,
            "issued_on": final_issued_str,
            "language": lang
        }
        redis_client.set(
            cert_num, json.dumps(cert_validation_data), ex=60 * 60 * 24 * 30 * 12
        )

        # QR Code
        qr_link = self.generate_qr_link(cert_num)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_link)
        qr.make(fit=True)
        qr_img_obj = qr.make_image(fill_color="black", back_color="white")
        qr_buffer = io.BytesIO()
        qr_img_obj.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)
        qr_size = 2 * cm
        qr_image = Image(qr_buffer, width=qr_size, height=qr_size)

        table_data = [[validate, qr_image]]
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
            w, h = doc.pagesize
            canvas.rect(margin, margin, w - 2 * margin, h - 2 * margin)
            canvas.restoreState()

        # Output
        output_dir = "assets/certs"
        os.makedirs(output_dir, exist_ok=True)

        doc = BaseDocTemplate(
            f"{output_dir}/{cert_num}.pdf",
            pagesize=(page_width, page_height),
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

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
        
        template = PageTemplate(id='cert_template', frames=[top_frame, bottom_frame], onPage=draw_border)
        doc.addPageTemplates([template])
        
        doc.build(elements)

        return cert_num
