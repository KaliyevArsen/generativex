# SponsoBot MVP

## What works
- Add lead (company/contact/channel/note)
- List leads + lead card
- AI generate email (subject + body)
- Send simulation (no real email): sets SENT_SIMULATED
- Dashboard: counts by status

## Setup
1) Create venv and install deps:
   pip install -r requirements.txt

2) Create .env:
   cp .env.example .env
   Fill TELEGRAM_TOKEN and OPENAI_API_KEY

3) Run:
   python src/main.py
# generativex
