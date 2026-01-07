# TrustMeBro Backend

<div align="center">

[![CI/CD Status](https://github.com/PiterPentester/trustmebro-backend/actions/workflows/backend-cicd.yaml/badge.svg)](https://github.com/PiterPentester/trustmebro-backend/actions/workflows/backend-cicd.yaml)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)

**Prove Anything**

</div>

## 📖 About

**TrustMeBro** is a "Truth in Certification" service. It allows users to generate authoritative-looking certificates for *anything*—from "Best Dog" to "Certified Couch Potato"—and provides a QR-code based validation mechanism. When someone scans the QR code, they are directed to a validation page that confirms the authenticity of the claim.

The backend service handles certificate data management, PDF generation, and validation logic.

## Frontend is here: [trustmebro-frontend](https://github.com/PiterPentester/trustmebro-frontend)

## ✨ Features

- **Certificate Generation**: Create custom certificates with names, types, and descriptions.
- **Customizable Layouts**: Choose between landscape and portrait orientations.
- **Special Badges**: Unlock hidden badges (like New Year themes) with specific keywords.
- **QR Code Integration**: Embeds scannable validation links directly into the PDF.
- **PDF Export**: High-quality PDF generation using ReportLab.
- **Validation API**: Secure endpoints to verify certificate authenticity.
- **Redis Caching**: High-performance data retrieval.

## 🛠 Tech Stack

- **Language**: Python 3.12
- **Framework**: FastAPI
- **Database/Cache**: Redis
- **PDF Engine**: ReportLab
- **Package Manager**: uv
- **Containerization**: Docker
- **Testing**: Pytest

## 🚀 Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started) & Docker Compose
- [Make](https://www.gnu.org/software/make/) (optional, for convenience)
- [uv](https://github.com/astral-sh/uv) (for local python management)

### Running Locally (Docker)

The easiest way to run the backend is with Docker Compose, which sets up both the API and Redis.

```bash
# Start the services
make run-compose

# The API will be available at http://localhost:8080
# Swagger UI: http://localhost:8080/docs
```

To stop the services:

```bash
make stop-compose
```

### Development

If you want to run it without Docker for development:

```bash
# Install dependencies
uv sync

# Run the server
uv run uvicorn main:app --reload --port 8080
```

## 🧪 Testing & Quality

We use a comprehensive suite of tools to ensure code quality.

```bash
# Format code (Ruff)
make format

# Lint code (Ruff)
make lint

# Security Scan (Bandit)
make scan-security

# Run Tests (Pytest)
make test
```

## 🐳 Deployment

The application is containerized and ready for Kubernetes deployment.

### Docker

```bash
# Build the image
make build

# Scan image for vulnerabilities
make scan-image
```

### Kubernetes

You can deploy the application to a Kubernetes cluster using the provided manifests.

```bash
# Deploy to Kubernetes
make deploy

# Remove from Kubernetes
make undeploy
```

The deployment includes:
- Backend Deployment (Replicas: 2)
- Redis Deployment
- Services for Backend and Redis
- Ingress with TLS (Cert-Manager)

## 📝 License

This project is licensed under the MIT License.

## 📜 Credits

<div align="center">
<a href="https://www.flaticon.com/free-icons/ribbon" title="ribbon icons">Ribbon icons created by cube29 - Flaticon</a> | 
<a href="https://www.flaticon.com/free-icons/certified" title="certified icons">Certified icons created by (many people)</a> |
<a href="https://www.flaticon.com/free-icons/2026" title="2026 icons">2026 icons created by Freepik - Flaticon</a>
</div>