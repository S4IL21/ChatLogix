import os
from flask import Flask, request, render_template, session, redirect, url_for, jsonify
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret")
ANALYZER = os.environ.get("ANALYZER_URL", "https://wachatanalyzer.onrender.com")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    f = request.files.get('file')
    if not f:
        return "No file uploaded", 400
    filename = secure_filename(f.filename)
    files = {'file': (filename, f.stream, f.mimetype)}
    resp = requests.post(f"{ANALYZER}/upload", files=files)
    try:
        resp.raise_for_status()
    except requests.HTTPError:
        return f"Analyzer error: {resp.text}", resp.status_code
    data = resp.json()
    session['main_data'] = data
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    if 'main_data' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')


def ensure_main_data():
    if 'main_data' not in session:
        return None, (jsonify({'error': 'No analyzed data in session; upload first'}), 400)
    return session['main_data'], None


def call_analyzer(path, json_body=None, files=None, alternatives=None):
    """Call analyzer endpoint and return (ok, response or (status, text)).
    If alternatives provided (list of paths), try them on non-200/404.
    """
    url = f"{ANALYZER}/{path.lstrip('/') }"
    try:
        if files:
            resp = requests.post(url, files=files)
        else:
            resp = requests.post(url, json=json_body)
    except requests.RequestException as exc:
        return False, (500, str(exc))

    if resp.status_code == 200:
        try:
            return True, resp.json()
        except ValueError:
            return False, (resp.status_code, 'Invalid JSON from analyzer')

    # try alternatives if provided
    if alternatives:
        for alt in alternatives:
            ok, result = call_analyzer(alt, json_body=json_body, files=files, alternatives=None)
            if ok:
                return True, result

    return False, (resp.status_code, resp.text)


@app.route('/api/members', methods=['GET'])
def api_members():
    data, err = ensure_main_data()
    if err:
        return err
    ok, result = call_analyzer('group-members', json_body=data)
    if not ok:
        status, msg = result
        return jsonify({'error': 'analyzer error', 'detail': msg}), status
    return jsonify(result)


@app.route('/api/fetch-stats', methods=['POST'])
def api_fetch_stats():
    payload = request.get_json() or {}
    username = payload.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400
    data, err = ensure_main_data()
    if err:
        return err
    body = {'data': data, 'username': username}
    ok, result = call_analyzer('fetch-stats', json_body=body)
    if not ok:
        status, msg = result
        return jsonify({'error': 'analyzer error', 'detail': msg}), status
    return jsonify(result)


@app.route('/api/overall-activity', methods=['POST'])
def api_overall_activity():
    payload = request.get_json() or {}
    username = payload.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400
    data, err = ensure_main_data()
    if err:
        return err
    body = {'data': data, 'username': username}
    ok, result = call_analyzer('overall-activity', json_body=body)
    if not ok:
        status, msg = result
        return jsonify({'error': 'analyzer error', 'detail': msg}), status
    return jsonify(result)


@app.route('/api/top-active-members', methods=['GET'])
def api_top_active_members():
    data, err = ensure_main_data()
    if err:
        return err
    ok, result = call_analyzer('top-active-members', json_body=data)
    if not ok:
        status, msg = result
        return jsonify({'error': 'analyzer error', 'detail': msg}), status
    return jsonify(result)


@app.route('/api/upload', methods=['POST'])
def api_upload():
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'file required'}), 400
    filename = secure_filename(f.filename)
    files = {'file': (filename, f.stream, f.mimetype)}
    ok, result = call_analyzer('upload', files=files)
    if not ok:
        status, msg = result
        return jsonify({'error': 'analyzer upload failed', 'detail': msg}), status
    # Save returned JSON in session
    session['main_data'] = result
    return jsonify({'status': 'ok', 'data': result})


@app.route('/api/<string:action>', methods=['GET', 'POST'])
def api_generic(action):
    """Generic proxied endpoints that map common analyzer routes. This provides
    many endpoints without adding them all manually.
    For 'fetch-stats', 'overall-activity', 'monthly-activity', 'weekly-activity', 'daily-activity',
    the request should include JSON body with 'username'. For list-like endpoints, session data will be sent directly.
    """
    data, err = ensure_main_data()
    if err:
        return err

    username = None
    if request.method == 'POST':
        payload = request.get_json() or {}
        username = payload.get('username')

    # endpoints that expect {'data': <json>, 'username': <str>}
    expects_username = {
        'fetch-stats', 'overall-activity', 'monthly-activity', 'weekly-activity', 'daily-activity', 'most-emoji-shared', 'most-shared-emojis'
    }

    if action in expects_username:
        if not username:
            return jsonify({'error': 'username required'}), 400
        body = {'data': data, 'username': username}
        # support ambiguous endpoint naming for emoji route
        alternatives = None
        if action == 'most-emoji-shared':
            alternatives = ['most-shared-emojis']
        ok, result = call_analyzer(action, json_body=body, alternatives=alternatives)
    else:
        # simple endpoints expect the main JSON as the body
        ok, result = call_analyzer(action, json_body=data)

    if not ok:
        status, msg = result
        return jsonify({'error': 'analyzer error', 'detail': msg}), status
    return jsonify(result)


@app.route('/api/session-data', methods=['GET'])
def api_session_data():
    """Debug helper: return current analyzed JSON in session (if any)."""
    data = session.get('main_data')
    if not data:
        return jsonify({'error': 'no data in session'}), 404
    return jsonify({'data': data})


@app.route('/api/clear-session', methods=['POST'])
def api_clear_session():
    session.pop('main_data', None)
    return jsonify({'status': 'cleared'})


# Generic proxy if needed
@app.route('/api/proxy', methods=['POST'])
def api_proxy():
    payload = request.get_json() or {}
    endpoint = payload.get('endpoint')
    body = payload.get('body', {})
    if not endpoint:
        return jsonify({'error': 'endpoint required'}), 400
    # attach main_data when body expects data
    if isinstance(body, dict) and 'data' in body and not body['data']:
        body['data'] = session.get('main_data')
    url = f"{ANALYZER}/{endpoint.lstrip('/') }"
    resp = requests.post(url, json=body)
    return jsonify(resp.json())


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
