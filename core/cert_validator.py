import redis
import json

class Validator():
    def __init__(self, redis_url, app_url):
        self.redis_url = redis_url
        self.app_url = app_url

    def validate(self, validation_number):
        redis_client = redis.Redis(host=self.redis_url, port=6379, db=0)
        validation_data = redis_client.get(validation_number)
        if validation_data is None:
            return False, {"error": "Invalid validation number"}
        return True, json.loads(validation_data)