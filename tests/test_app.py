import json
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

    def test_non_object_json_rejected(self):
        for payload in (["urgent"], "urgent", 123, True, None):
            with self.subTest(payload=payload):
                response = self.client.post(
                    "/api/analyse",
                    data=json.dumps(payload),
                    content_type="application/json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json)

    def test_non_string_text_rejected(self):
        for text in (None, 123, True, ["OTP"], {"message": "OTP"}):
            with self.subTest(text=text):
                response = self.client.post("/api/analyse", json={"text": text})
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.json)

    def test_missing_or_malformed_json_rejected(self):
        for body in ("", "{", "{}"):
            with self.subTest(body=body):
                response = self.client.post(
                    "/api/analyse", data=body, content_type="application/json"
                )
                self.assertEqual(response.status_code, 400)

    def test_input_length_limit(self):
        response = self.client.post("/api/analyse", json={"text": "a" * 5000})
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/analyse", json={"text": "a" * 5001})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(self.client.get("/api/history").json), 1)

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

    def test_account_threat_variants_detected(self):
        for text in (
            "Your account blocked",
            "Your account will be blocked today",
            "Your account is suspended",
            "Your account has been suspended",
        ):
            with self.subTest(text=text):
                result = scam_app.analyse_text(text)
                self.assertIn("threat", [signal["key"] for signal in result["signals"]])

    def test_malformed_urls_detected(self):
        for text in (
            "https:///login",
            "https://example.com:invalid",
            "https://example.com:99999",
            "https://[invalid]",
        ):
            with self.subTest(text=text):
                result = scam_app.analyse_text(text)
                self.assertIn(
                    "malformed_url", [signal["key"] for signal in result["signals"]]
                )

    def test_ipv6_url_not_marked_malformed(self):
        for text in ("https://[::1]", "[https://[::1]]"):
            with self.subTest(text=text):
                result = scam_app.analyse_text(text)
                self.assertNotIn(
                    "malformed_url", [signal["key"] for signal in result["signals"]]
                )

    def test_history_returns_scan(self):
        self.client.post("/api/analyse", json={"text": "share your OTP"})
        response = self.client.get("/api/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)


if __name__ == "__main__":
    unittest.main()
