import pytest
from unittest.mock import Mock, patch
from core.cert_validator import Validator
import json


class TestValidator:
    @pytest.fixture
    def validator(self):
        with patch("core.cert_validator.redis.Redis"):
            return Validator("redis://localhost", "http://localhost:8080")

    def test_validate_success(self, validator):
        # Mock Redis return value
        stored_data = {
            "cert_type": "achievement",
            "recipient_name": "Test User",
            "item_to_prove": "Test Item",
            "issued_on": "2023-01-01",
        }
        validator.redis_client.get = Mock(return_value=json.dumps(stored_data).encode())

        is_valid, result = validator.validate("12345")

        assert is_valid is True
        assert result == stored_data
        validator.redis_client.get.assert_called_with("12345")

    def test_validate_not_found(self, validator):
        validator.redis_client.get = Mock(return_value=None)

        is_valid, result = validator.validate("nonexistent")

        assert is_valid is False
        assert "error" in result
        assert result["error"] == "Invalid validation number"

    def test_validate_redis_error(self, validator):
        validator.redis_client.get = Mock(side_effect=Exception("Redis error"))

        is_valid, result = validator.validate("12345")

        assert is_valid is False
        assert "error" in result
