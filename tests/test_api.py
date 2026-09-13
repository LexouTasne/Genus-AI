import os
import unittest
from unittest.mock import patch

os.environ["GENUS_LOCAL_API_TOKEN"] = "test-token"

from ai_engine.my_api.api import app


class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_is_available_locally(self):
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_chat_requires_token(self):
        self.assertEqual(self.client.post("/chat", json={"messages": [{"role": "user", "content": "oi"}]}).status_code, 401)

    def test_token_is_checked_before_provider(self):
        with patch("ai_engine.my_api.api.API_KEY", "key"):
            response = self.client.post("/chat", headers={"Authorization": "Bearer test-token"}, json={"messages": []})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
