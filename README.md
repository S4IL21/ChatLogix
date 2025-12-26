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

Deploy to Vercel:
1. Push to a GitHub repo
2. Import the repo to Vercel and set env var `SECRET_KEY`
3. Vercel will build using `api/index.py` as entrypoint

Notes:
- Tailwind is included via CDN for simplicity; for production you can integrate a Tailwind build-step.
- The app proxies requests to the public WhatsApp Chat Analyzer API.
