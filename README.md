# ScamShield

ScamShield is an educational MVP that flags common warning signs in suspicious messages and URLs. It uses transparent, rule-based heuristics—not a trained AI model—and does not establish whether a message is genuinely fraudulent.

## Features

- Flask backend and responsive browser UI
- Rule-based signals for urgency, OTP/password requests, payment requests, prizes, threats, remote access, URL shorteners, and suspicious URL patterns
- Risk indicator with explanations and safety recommendations
- English and Tamil awareness tips
- Sample inputs and recent local scan history
- SQLite database created automatically
- Basic automated tests

## Requirements

- Python 3.10 or newer
- pip

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

To run tests:

```bash
python -m unittest discover -s tests -v
```

## API

`POST /api/analyse`

Request:

```json
{"text": "URGENT! Your account will be blocked. Share your OTP."}
```

`GET /api/history` returns the latest 10 local demo scans. `GET /health` is a basic health check.

## Architecture

1. Browser sends pasted text to Flask at `/api/analyse`.
2. The analysis function applies transparent regular-expression rules and optional URL checks.
3. The server returns a heuristic score, risk label, detected signals, and safety advice.
4. A small SQLite database stores the latest local demo scan history.
5. The browser renders the response with text-safe DOM APIs.

See `docs/ARCHITECTURE.md`.

## Privacy and safety

- Do not paste real OTPs, passwords, bank details, or other sensitive information.
- This local demo stores up to 500 characters of each submitted input in `scamshield.db` to show history. Delete that file to clear local history.
- Do not expose this development server publicly without adding production security, privacy controls, and deployment hardening.
- The score is a heuristic, not a calibrated probability. A low score does not mean a message is safe. False positives and false negatives are possible.
- HTTPS does not guarantee a site is trustworthy.
- For suspected cybercrime in India, visit https://cybercrime.gov.in. The 1930 helpline is intended for financial cyber fraud reporting.

## Sample cases

See `data/sample_cases.json`. The examples are synthetic and for demonstration only.

## License

MIT — see `LICENSE`.
