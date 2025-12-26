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


@app.route('/api/members', methods=['GET'])
def api_members():
    data, err = ensure_main_data()
    if err:
        return err
    resp = requests.post(f"{ANALYZER}/group-members", json=data)
    return jsonify(resp.json())


@app.route('/api/fetch-stats', methods=['POST'])
def api_fetch_stats():
    payload = request.get_json() or {}
    username = payload.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400
    data, err = ensure_main_data()
    if err:
        return err
    body = {
        'data': data,
        'username': username
    }
    resp = requests.post(f"{ANALYZER}/fetch-stats", json=body)
    return jsonify(resp.json())


@app.route('/api/overall-activity', methods=['POST'])
def api_overall_activity():
    payload = request.get_json() or {}
    username = payload.get('username')
    if not username:
        return jsonify({'error': 'username required'}), 400
    data, err = ensure_main_data()
    if err:
        return err
    body = {
        'data': data,
        'username': username
    }
    resp = requests.post(f"{ANALYZER}/overall-activity", json=body)
    return jsonify(resp.json())


@app.route('/api/top-active-members', methods=['GET'])
def api_top_active_members():
    data, err = ensure_main_data()
    if err:
        return err
    resp = requests.post(f"{ANALYZER}/top-active-members", json=data)
    return jsonify(resp.json())


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
