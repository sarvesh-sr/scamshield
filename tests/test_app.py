import os
import tempfile
import unittest
from unittest.mock import patch

import app as scam_app


class ScamShieldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        patcher = patch.object(scam_app, "DB_PATH", self.db_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        scam_app.init_db()
        self.client = scam_app.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_empty_input_rejected(self):
        response = self.client.post("/api/analyse", json={"text": "  "})
        self.assertEqual(response.status_code, 400)

    def test_otp_warning_detected(self):
        response = self.client.post(
            "/api/analyse",
            json={"text": "URGENT! Share your OTP immediately or account blocked."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json["risk_score"], 25)
        self.assertTrue(response.json["signals"])

    def test_ordinary_message_has_no_configured_signals(self):
        response = self.client.post(
            "/api/analyse",
            json={"text": "Hi, our meeting is at 4 PM. Bring your project notes."},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["risk_score"], 0)

    def test_history_returns_scan(self):
        self.client.post("/api/analyse", json={"text": "share your OTP"})
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)


if __name__ == "__main__":
    unittest.main()
