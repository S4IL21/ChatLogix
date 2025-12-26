from app import app

# This file is the Vercel entrypoint. Vercel will use the WSGI `app`.


# Optional: simple health route
@app.route('/api/health')
def health():
    return {'status': 'ok'}
