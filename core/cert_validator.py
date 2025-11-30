"""Certificate validator module."""

import json
import redis
from typing import Tuple, Dict, Any, Optional


class Validator:
    """Class for validating certificates."""

    def __init__(
        self, redis_host: str, base_url: str, redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize the validator with Redis connection details.

        Args:
            redis_host: Redis host address
            base_url: Base URL for the application
            redis_client: Optional Redis client (for testing)
        """
        self.redis_client = redis_client or redis.Redis(
            host=redis_host, port=6379, db=0
        )
        self.base_url = base_url

    def validate(self, validation_number: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a certificate by its validation number.

        Args:
            validation_number: The validation number to check.

        Returns:
            A tuple of (is_valid, result_dict)
        """
        try:
            # Get the certificate data from Redis
            validation_data = self.redis_client.get(validation_number)

            if not validation_data:
                return False, {"error": "Invalid validation number"}

            # Handle empty data
            if validation_data == b"":
                return False, {"error": "No data found for this validation number"}

            # Parse the JSON data
            try:
                cert_data = json.loads(validation_data)

                # Validate required fields
                required_fields = [
                    "recipient_name",
                    "cert_type",
                    "item_to_prove",
                    "issued_on",
                ]
                if not all(field in cert_data for field in required_fields):
                    return False, {
                        "error": "Invalid certificate data: missing required fields"
                    }

                return True, cert_data

            except json.JSONDecodeError:
                return False, {
                    "error": "Invalid certificate data format: not valid JSON"
                }

        except (redis.ConnectionError, redis.TimeoutError) as e:
            return False, {
                "error": f"Could not connect to validation service: {str(e)}"
            }

        except Exception as e:
            return False, {"error": f"Validation error: {str(e)}"}
