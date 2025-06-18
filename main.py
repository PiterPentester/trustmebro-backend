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

from core.cert_generator import TrustMeBroCertificate
from core.cert_validator import Validator
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

class Certificate(BaseModel):
    cert_type: str
    recipient: str
    item_to_prove: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cert_type": "achievment",
                    "recipient": "John Doe",
                    "item_to_prove": "killed the Dead Sea",
                },
                {
                    "cert_type": "completion",
                    "recipient": "John Doe",
                    "item_to_prove": "endless lessons",
                },
                {
                    "cert_type": "ownership",
                    "recipient": "John Doe",
                    "item_to_prove": "the dark side of the moon",
                },
            ]
        }
    }

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "pong"}

@app.post("/generate")
async def generate_certificate(data: Certificate):
    return certificate_generator.create_certificate(data.cert_type, data.recipient, data.item_to_prove)

@app.get("/download/{cert_validation_number}")
async def download_certificate(cert_validation_number: str):
    headers = {
        f"Content-Disposition": "inline; filename={cert_validation_number}.pdf"
    }
    return FileResponse(f"assets/certs/{cert_validation_number}.pdf", media_type="application/pdf", headers=headers)

@app.get("/validate/{cert_validation_number}")
async def validate_certificate(cert_validation_number: str):
    return validator.validate(cert_validation_number)

if __name__ == "__main__":
    import uvicorn
    REDIS_URL = os.environ.get("REDIS_URL", "localhost")
    APP_PORT = os.environ.get("APP_PORT", "8080")
    APP_URL = os.environ.get("APP_URL", f"http://localhost:{APP_PORT}")
    certificate_generator = TrustMeBroCertificate(REDIS_URL, APP_URL)
    validator = Validator(REDIS_URL, APP_URL)
    uvicorn.run(app, host="0.0.0.0", port=int(APP_PORT))
