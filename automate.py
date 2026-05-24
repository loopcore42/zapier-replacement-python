"""
Loop Core — Zapier Replacement Automation
github.com/loopcore42

Listens for incoming webhooks (from Typeform, Stripe, Gmail, etc.)
and routes them to any action you define: Slack, email, spreadsheet, 
another API, or all three.

Zero cost. Runs anywhere Python runs.

Setup:
    pip install flask requests python-dotenv

Run:
    python automate.py

Expose to the internet (free):
    ngrok http 5000
"""

import os
import json
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


# ─────────────────────────────────────────────
# CONFIGURE YOUR ACTIONS HERE
# Copy .env.example to .env and fill in values
# ─────────────────────────────────────────────

SLACK_WEBHOOK_URL  = os.getenv("SLACK_WEBHOOK_URL")   # From api.slack.com/apps
NOTIFY_EMAIL       = os.getenv("NOTIFY_EMAIL")         # Where to send alerts
SMTP_USER          = os.getenv("SMTP_USER")            # Your Gmail address
SMTP_PASS          = os.getenv("SMTP_PASS")            # Gmail app password
LOG_FILE           = os.getenv("LOG_FILE", "events.log")


# ─────────────────────────────────────────────
# ACTION 1 — Send a Slack message
# ─────────────────────────────────────────────

def notify_slack(message: str, emoji: str = ":zap:") -> bool:
    """Post a message to your Slack channel via webhook."""
    if not SLACK_WEBHOOK_URL:
        print("[slack] No webhook URL set — skipping.")
        return False

    payload = {"text": f"{emoji} *Loop Core Alert*\n{message}"}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=5)

    if response.status_code == 200:
        print(f"[slack] Sent: {message}")
        return True
    else:
        print(f"[slack] Failed: {response.status_code} — {response.text}")
        return False


# ─────────────────────────────────────────────
# ACTION 2 — Send an email notification
# ─────────────────────────────────────────────

def notify_email(subject: str, body: str) -> bool:
    """Send an email alert via Gmail SMTP."""
    if not all([NOTIFY_EMAIL, SMTP_USER, SMTP_PASS]):
        print("[email] Credentials not set — skipping.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = NOTIFY_EMAIL
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, NOTIFY_EMAIL, msg.as_string())
        print(f"[email] Sent to {NOTIFY_EMAIL}: {subject}")
        return True
    except Exception as e:
        print(f"[email] Failed: {e}")
        return False


# ─────────────────────────────────────────────
# ACTION 3 — Log every event to a file
# ─────────────────────────────────────────────

def log_event(trigger: str, data: dict) -> None:
    """Append event details to a local log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] trigger={trigger} data={json.dumps(data)}\n"

    with open(LOG_FILE, "a") as f:
        f.write(entry)
    print(f"[log] {entry.strip()}")


# ─────────────────────────────────────────────
# TRIGGER ROUTES — one URL per event source
# Add as many as you need below
# ─────────────────────────────────────────────

@app.route("/trigger/new-lead", methods=["POST"])
def trigger_new_lead():
    """
    Fires when a new lead submits your contact form.
    Point Typeform / Tally / your own form to this URL.

    Expected JSON body:
        { "name": "Jane Smith", "email": "jane@example.com", "message": "..." }
    """
    data = request.get_json(silent=True) or {}

    name    = data.get("name", "Unknown")
    email   = data.get("email", "No email")
    message = data.get("message", "No message")

    # Run all three actions in sequence
    notify_slack(
        f"New lead from *{name}* ({email})\n>{message}",
        emoji=":raising_hand:"
    )
    notify_email(
        subject=f"New lead: {name}",
        body=f"Name:    {name}\nEmail:   {email}\nMessage: {message}"
    )
    log_event("new-lead", data)

    return jsonify({"status": "ok", "trigger": "new-lead"}), 200


@app.route("/trigger/new-payment", methods=["POST"])
def trigger_new_payment():
    """
    Fires on a new Stripe payment.
    In Stripe Dashboard → Webhooks → add this endpoint.

    Handles the charge.succeeded event.
    """
    data    = request.get_json(silent=True) or {}
    event   = data.get("type", "unknown")

    if event != "charge.succeeded":
        return jsonify({"status": "ignored", "event": event}), 200

    charge  = data.get("data", {}).get("object", {})
    amount  = charge.get("amount", 0) / 100          # Stripe sends cents
    currency = charge.get("currency", "usd").upper()
    customer = charge.get("billing_details", {}).get("name", "Unknown customer")

    notify_slack(
        f"Payment received from *{customer}*: {currency} {amount:.2f}",
        emoji=":money_with_wings:"
    )
    notify_email(
        subject=f"Payment received: {currency} {amount:.2f}",
        body=f"Customer: {customer}\nAmount:   {currency} {amount:.2f}\nEvent:    {event}"
    )
    log_event("new-payment", {"customer": customer, "amount": amount, "currency": currency})

    return jsonify({"status": "ok", "trigger": "new-payment"}), 200


@app.route("/trigger/new-signup", methods=["POST"])
def trigger_new_signup():
    """
    Generic signup trigger — use for newsletter, app signup,
    or anything that sends a POST with user details.
    """
    data  = request.get_json(silent=True) or {}
    email = data.get("email", "Unknown")
    plan  = data.get("plan", "free")

    notify_slack(
        f"New signup: *{email}* on the _{plan}_ plan",
        emoji=":tada:"
    )
    log_event("new-signup", data)

    return jsonify({"status": "ok", "trigger": "new-signup"}), 200


@app.route("/trigger/custom", methods=["POST"])
def trigger_custom():
    """
    Catch-all trigger for anything else.
    POST any JSON to /trigger/custom and it gets
    logged + sent to Slack automatically.
    """
    data = request.get_json(silent=True) or {}

    notify_slack(f"Custom trigger fired:\n```{json.dumps(data, indent=2)}```")
    log_event("custom", data)

    return jsonify({"status": "ok", "trigger": "custom"}), 200


# ─────────────────────────────────────────────
# HEALTH CHECK — confirm server is running
# ─────────────────────────────────────────────

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "Loop Core is running", "timestamp": datetime.now().isoformat()}), 200


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  Loop Core Automation Server")
    print("  Running on http://localhost:5000")
    print("  Expose publicly: ngrok http 5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
