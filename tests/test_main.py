from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
import pytest

client = TestClient(app)

@pytest.fixture
def mock_redis():
    with patch('core.cert_generator.redis.Redis') as mock:
        yield mock

@pytest.fixture
def mock_cert_generator():
    with patch('main.certificate_generator') as mock:
        yield mock

@pytest.fixture
def mock_validator():
    with patch('main.validator') as mock:
        yield mock

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "pong"}

def test_generate_certificate(mock_cert_generator):
    mock_cert_generator.create_certificate.return_value = "12345"
    
    payload = {
        "cert_type": "achievement",
        "recipient": "Test User",
        "item_to_prove": "Test Item"
    }
    
    response = client.post("/generate", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {"validation_number": "12345"}
    mock_cert_generator.create_certificate.assert_called_once_with(
        "achievement", "Test User", "Test Item"
    )

def test_validate_certificate_valid(mock_validator):
    mock_validator.validate.return_value = (True, {"recipient": "Test User"})
    
    response = client.get("/validate/12345")
    
    assert response.status_code == 200
    assert response.json() == {"valid": True, "certificate": {"recipient": "Test User"}}
    mock_validator.validate.assert_called_once_with("12345")

def test_validate_certificate_invalid(mock_validator):
    mock_validator.validate.return_value = (False, {"error": "Not found"})
    
    response = client.get("/validate/invalid")
    
    assert response.status_code == 200
    assert response.json() == {
        "valid": False,
        "error": "Not found",
        "certificate": None
    }

@patch('main.Path')
@patch('main.os.remove')
def test_download_certificate(mock_remove, mock_path):
    # Mock file existence
    mock_path_obj = MagicMock()
    mock_path_obj.exists.return_value = True
    mock_path.return_value = mock_path_obj
    
    # Mock open
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_file = MagicMock()
        mock_file.__enter__.return_value = [b"pdf content"]
        mock_open.return_value = mock_file
        
        response = client.get("/download/12345")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"] == "attachment; filename=12345.pdf"

@patch('main.Path')
def test_download_certificate_not_found(mock_path):
    mock_path_obj = MagicMock()
    mock_path_obj.exists.return_value = False
    mock_path.return_value = mock_path_obj
    
    response = client.get("/download/nonexistent")
    
    assert response.status_code == 404
    assert response.json() == {"detail": "File not found"}
