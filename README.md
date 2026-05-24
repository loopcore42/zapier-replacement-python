# Loop Core — Free Zapier Replacement

Replace your Zapier subscription with a Python script that does the same thing for $0.

## What this does

Listens for events from any app (Typeform, Stripe, your own form) and:
- Sends a Slack message
- Sends an email alert
- Logs everything to a file

## Setup (5 minutes)

**1. Install dependencies**
```bash
pip install flask requests python-dotenv
```

**2. Configure your credentials**
```bash
cp .env.example .env
# Edit .env with your Slack webhook URL and email credentials
```

**3. Run the server**
```bash
python automate.py
```

**4. Expose to the internet (free with ngrok)**
```bash
ngrok http 5000
# Copy the https URL — use it as your webhook endpoint
```

## Trigger endpoints

| URL | Use for |
|-----|---------|
| `POST /trigger/new-lead` | Contact form submissions |
| `POST /trigger/new-payment` | Stripe payments |
| `POST /trigger/new-signup` | App/newsletter signups |
| `POST /trigger/custom` | Anything else |
| `GET /ping` | Health check |

## Test it without any external apps

```bash
curl -X POST http://localhost:5000/trigger/new-lead \
  -H "Content-Type: application/json" \
  -d '{"name": "Jane Smith", "email": "jane@example.com", "message": "I need a quote"}'
```

## Deploy for free (so it runs 24/7)

- **Railway.app** — free tier, deploy in 2 clicks
- **Render.com** — free tier, always-on
- **Oracle Cloud** — free forever VM

---
From the Loop Core YouTube channel. Subscribe for 3 free scripts every week.
