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

import os
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from core.cert_generator import TrustMeBroCertificate
from core.cert_validator import Validator
from pathlib import Path

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "localhost")
APP_URL = os.getenv("APP_URL", "http://localhost:8080")

# Initialize the certificate generator and validator
certificate_generator = TrustMeBroCertificate(redis_url=REDIS_URL, app_url=APP_URL)
validator = Validator(redis_host=REDIS_URL, base_url=APP_URL)


class Certificate(BaseModel):
    cert_type: str
    recipient: str
    item_to_prove: str
    language: str = "en"
    orientation: str = "landscape"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "cert_type": "achievement",
                    "recipient": "John Doe",
                    "item_to_prove": "killed the Dead Sea",
                    "language": "en",
                    "orientation": "landscape"
                },
                {
                    "cert_type": "completion",
                    "recipient": "John Doe",
                    "item_to_prove": "endless lessons",
                    "language": "uk",
                    "orientation": "portrait"
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

router = APIRouter(prefix="/api")

# Update origins to include common frontend development URLs
origins = [
    "http://localhost:3000",  # Common React dev server
    "http://127.0.0.1:3000",  # Alternative localhost
    "http://localhost:8080",  # Common alternative port
    "http://127.0.0.1:8080",  # Alternative localhost
    "*",  # Fallback for all origins (not recommended for production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],  # Be explicit about allowed methods
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
    ],  # Be explicit about allowed headers
    expose_headers=["Content-Disposition"],  # Important for file downloads
)


@router.get("/")
async def root():
    return {"message": "pong"}


@router.post("/generate")
async def generate_certificate(data: Certificate):
    """
    Generate a new certificate.

    Args:
        data: Certificate data including type, recipient, item to prove, and language

    Returns:
        dict: Contains the validation number for the generated certificate
    """
    try:
        validation_number = certificate_generator.create_certificate(
            data.cert_type, data.recipient, data.item_to_prove, data.language, data.orientation
        )
        return {"validation_number": validation_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{cert_validation_number}")
async def download_certificate(cert_validation_number: str):
    file_path = Path(f"assets/certs/{cert_validation_number}.pdf")

    # Check if the file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Function to stream file content
    def iterfile():
        with open(file_path, "rb") as file:
            yield from file
        # Delete the file after streaming
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")

    # Return the file as a streaming response
    return StreamingResponse(
        iterfile(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={cert_validation_number}.pdf"
        },
    )


@router.get("/validate/{cert_validation_number}")
async def validate_certificate(cert_validation_number: str):
    """
    Validate a certificate by its validation number.

    Args:
        cert_validation_number: The validation number to check

    Returns:
        dict: A dictionary with validation result and certificate data if valid
    """
    try:
        is_valid, result = validator.validate(cert_validation_number)
        if is_valid:
            return {"valid": True, "certificate": result}
        else:
            return {
                "valid": False,
                "error": result.get("error", "Invalid certificate"),
                "certificate": None,
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error validating certificate: {str(e)}"
        )


@router.get("/version")
async def get_version():
    """
    Get the version of the backend application.
    """
    return {"version": os.environ.get("APP_VERSION", "unknown")}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    REDIS_URL = os.environ.get("REDIS_URL", "localhost")
    APP_PORT = os.environ.get("APP_PORT", "8080")
    APP_URL = os.environ.get("APP_URL", f"http://localhost:{APP_PORT}")
    certificate_generator = TrustMeBroCertificate(REDIS_URL, APP_URL)
    validator = Validator(REDIS_URL, APP_URL)
    uvicorn.run(app, host="0.0.0.0", port=int(APP_PORT))
