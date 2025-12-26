# Chatlogix

Chatlogix is a mobile-first Flask application that uses the public WhatsApp Chat Analyzer API (https://wachatanalyzer.onrender.com) to process WhatsApp chat exports and visualize chat metrics.

Key points:
- Mobile-first UI using Tailwind (via CDN) for quick setup
- No local DB — processed results are kept in session
- Hosted on Vercel using the Python runtime

Quick start (local):

1. Create a virtualenv and install:
   python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
2. Run locally:
   $env:FLASK_APP='app.py'; python app.py
3. Open http://localhost:5000

API notes:
- The app exposes internal proxy endpoints under `/api/*` that call the public WhatsApp Chat Analyzer API.
- Use `/api/upload` (POST, multipart form with `file`) to upload a `.txt` file via AJAX and store the analyzed JSON in session.
- Use `/api/members` (GET) to get group members (proxies to external `/group-members`).
- Use `/api/fetch-stats` (POST, JSON {"username": "Overall Group"}) to get stats for a user.
- Use `/api/overall-activity` (POST, JSON {"username": "Overall Group"}) to get date-wise activity.
- Other endpoints are available via `/api/<endpoint>` (e.g. `/api/top-active-members`, `/api/monthly-activity`) and map to the analyzer endpoints.

Debug endpoints:
- `/api/session-data` (GET) — view currently stored analyzed JSON in session (dev only).
- `/api/clear-session` (POST) — clear session stored data.

Deploy to Vercel:
1. Push to a GitHub repo
2. Import the repo to Vercel and set env var `SECRET_KEY`
3. Vercel will build using `api/index.py` as entrypoint

Notes:
- Tailwind is included via CDN for simplicity; for production you can integrate a Tailwind build-step.
- The app proxies requests to the public WhatsApp Chat Analyzer API.
