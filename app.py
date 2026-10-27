import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "scamshield.db"

app = Flask(__name__)

RULES = [
    (
        "urgent",
        15,
        r"\b(urgent|immediately|act now|expires today|within \d+ hours?)\b",
        "Creates urgency or pressures you to act quickly.",
    ),
    (
        "otp",
        25,
        r"\b(otp|one[- ]time password|verification code)\b",
        "Mentions an OTP or verification code. Never share these with anyone.",
    ),
    (
        "password",
        25,
        r"\b(password|passcode|login credentials|pin number|upi pin)\b",
        "Requests or references sensitive login/payment credentials.",
    ),
    (
        "money",
        15,
        r"\b(pay now|send money|transfer money|processing fee|registration fee|pay a fee)\b",
        "Requests a payment or fee.",
    ),
    (
        "prize",
        20,
        r"\b(you (have )?won|winner|lottery|claim your prize|free gift)\b",
        "Promises a prize or reward that may be used as bait.",
    ),
    (
        "threat",
        20,
        r"\b(account (?:(?:will be|is|has been) )?(?:blocked|suspended)|legal action|police case|will be arrested)\b",
        "Uses threats or account warnings to pressure you.",
    ),
    (
        "remote_access",
        25,
        r"\b(install anydesk|teamviewer|remote access|screen sharing app)\b",
        "Encourages remote access to your device.",
    ),
    (
        "short_link",
        10,
        r"\b(bit\.ly|tinyurl\.com|t\.co|cutt\.ly|rb\.gy)\b",
        "Contains a URL-shortening service that hides the final destination.",
    ),
    (
        "personal_info",
        15,
        r"\b(aadhaar|pan card|bank details|card number|cvv)\b",
        "Mentions sensitive identity or financial information.",
    ),
    (
        "suspicious_domain",
        20,
        r"https?://[^\s/]*\b(?:login|verify|secure|update|claim|kyc)[-_.][^\s/]*",
        "URL contains wording commonly used to imitate account or verification pages.",
    ),
]


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_text TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def analyse_text(text):
    cleaned = (text or "").strip()
    if not cleaned:
        return {
            "risk_score": 0,
            "risk_level": "Unknown",
            "signals": [],
            "recommendations": ["Paste a message or URL to analyse."],
            "disclaimer": "This tool uses simple rules. It cannot confirm whether something is a scam.",
        }

    signals = []
    score = 0
    for key, points, pattern, explanation in RULES:
        if re.search(pattern, cleaned, flags=re.IGNORECASE):
            signals.append({"key": key, "points": points, "explanation": explanation})
            score += points

    urls = re.findall(r"https?://[^\s]+", cleaned, flags=re.IGNORECASE)
    for raw_url in urls:
        candidate = raw_url.rstrip(".,);}>")
        while candidate.endswith("]") and candidate.count("]") > candidate.count("["):
            candidate = candidate[:-1]
        try:
            parsed = urlparse(candidate)
            host = (parsed.hostname or "").lower()
            if not host or any(char.isspace() for char in host):
                raise ValueError("URL must include a valid hostname.")
            # urlparse defers invalid and out-of-range port errors until access.
            parsed.port
            if parsed.scheme.lower() == "http":
                signals.append(
                    {
                        "key": "http",
                        "points": 10,
                        "explanation": "URL uses HTTP rather than HTTPS; avoid entering sensitive information.",
                    }
                )
                score += 10
            if host.count("-") >= 2 or re.search(r"\d{4,}", host):
                signals.append(
                    {
                        "key": "domain_shape",
                        "points": 10,
                        "explanation": "The domain has an unusual pattern. Verify it independently.",
                    }
                )
                score += 10
        except ValueError:
            signals.append(
                {
                    "key": "malformed_url",
                    "points": 10,
                    "explanation": "The URL could not be parsed normally. Do not open it until verified.",
                }
            )
            score += 10

    score = min(score, 100)
    if score >= 50:
        level = "High"
    elif score >= 25:
        level = "Medium"
    elif score > 0:
        level = "Low"
    else:
        level = "No obvious signals"

    recommendations = []
    if signals:
        recommendations.extend(
            [
                "Do not share OTPs, passwords, UPI PINs, CVVs, or recovery codes.",
                "Do not pay or click links because a message creates urgency.",
                "Verify the sender using an official website or phone number you find independently.",
            ]
        )
    else:
        recommendations.append(
            "No configured warning patterns were detected. This does not mean the message is safe."
        )
    recommendations.append(
        "If you suspect cyber fraud in India, visit https://cybercrime.gov.in or call 1930 for financial cyber fraud."
    )

    result = {
        "risk_score": score,
        "risk_level": level,
        "signals": signals,
        "recommendations": recommendations,
        "disclaimer": "Heuristic screening only—not an AI model, probability, or guarantee. Scams can evade these rules and legitimate messages can trigger them.",
    }

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO scans (input_text, risk_score, risk_level) VALUES (?, ?, ?)",
            (cleaned[:500], score, level),
        )
    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/analyse")
def api_analyse():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Please send a JSON object with a text field."}), 400
    text = data.get("text", "")
    if not isinstance(text, str):
        return jsonify({"error": "The text field must be a string."}), 400
    if not text.strip():
        return jsonify({"error": "Please enter a message or URL."}), 400
    if len(text) > 5000:
        return jsonify({"error": "Please limit your input to 5,000 characters."}), 400
    return jsonify(analyse_text(text))


@app.get("/api/history")
def api_history():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, input_text, risk_score, risk_level, created_at FROM scans ORDER BY id DESC LIMIT 10"
        ).fetchall()
    return jsonify([dict(row) for row in rows])


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


init_db()

if __name__ == "__main__":
    app.run(debug=True)
