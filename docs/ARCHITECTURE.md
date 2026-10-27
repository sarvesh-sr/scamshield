# ScamShield — Technical Design

## Goal

Demonstrate an accessible first-pass educational tool for identifying common scam warning signs in user-provided text. It is not a forensic tool or a definitive fraud detector.

## Components

```text
+--------------------------+
| Browser UI               |
| HTML / CSS / JavaScript  |
+------------+-------------+
             | POST /api/analyse (JSON)
             v
+--------------------------+
| Flask application        |
| Input validation         |
| Rule-based analysis      |
| Recommendations          |
+------+-------------------+
       |                   |
       v                   v
+--------------+   +--------------------+
| SQLite       |   | JSON response      |
| local history|   | score + signals    |
+--------------+   +--------------------+
                           |
                           v
                  Browser renders result
```

## Analysis flow

1. Require a JSON object containing a nonblank text string of at most 5,000 characters; reject invalid or oversized inputs rather than silently truncating them. Trim accepted text before analysis.
2. Match text against a small, documented set of warning patterns.
3. If URLs are present, inspect simple structural indicators such as HTTP and unusual hostname shapes.
4. Sum configured points and cap the score at 100.
5. Map the score to a heuristic label: 0 = no obvious signals, 1–24 = low, 25–49 = medium, 50–100 = high.
6. Return signals, explanations, recommendations, and a disclaimer.

## Data storage

SQLite stores a truncated copy of each analysed input, the score, label, and timestamp for the local history feature. This is for demo convenience only. A production version should avoid storing submitted content by default, provide explicit consent and deletion controls, and define a retention policy.

## Limitations and next steps

- Rules can miss new scam tactics and can flag legitimate messages.
- A score is not a probability of fraud.
- URL checks do not fetch or open the URL.
- Future work could include evaluated classifiers, better URL reputation sources, accessibility testing, more Indian languages, and user testing with consent.
