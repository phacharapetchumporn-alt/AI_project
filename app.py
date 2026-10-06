"""
SignSubs - Flask Backend Server with SQLite Authentication
Includes user registration, secure password hashing, login sessions,
and endpoints for SignSubs real-time translation & video feed.
Supports HTTPS (self-signed cert) for mobile camera access via getUserMedia.
"""

import os
import sys
import sqlite3
import datetime
import ipaddress
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response  # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore

try:
    from inference_engine import InferenceEngine
    engine = InferenceEngine()
    print("[AI] Initialized InferenceEngine")
except Exception as e:
    print(f"[AI] Error loading InferenceEngine: {e}")
    engine = None

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'signsubs_super_secret_key_2026_dev')

DB_PATH = os.path.join(os.path.dirname(__file__), 'signsubs.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Insert a default demo user if table is empty
        cursor.execute('SELECT COUNT(*) as count FROM users')
        row = cursor.fetchone()
        if row['count'] == 0:
            demo_hash = generate_password_hash('123456')
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                ('admin', 'admin@signsubs.ai', demo_hash)
            )
        conn.commit()

# Initialize DB on startup
init_db()

# -----------------------------------------------------------------------------
# Web Page Routes
# -----------------------------------------------------------------------------

@app.route('/')
def index():
    template_name = 'index.html' if os.path.exists(os.path.join(app.template_folder, 'index.html')) else 'index (1).html'
    return render_template(template_name)

@app.route('/index.html')
def index_html():
    return index()

@app.route('/api/server-info', methods=['GET'])
def api_server_info():
    lan_ip = get_lan_ip()
    port = request.environ.get('SERVER_PORT', 5000)
    is_ssl = request.is_secure or request.scheme == 'https'
    return jsonify({
        'lan_ip': lan_ip,
        'port': port,
        'is_ssl': is_ssl,
        'https_url': f"https://{lan_ip}:{port}",
        'http_url': f"http://{lan_ip}:{port}",
        'current_origin': request.host_url.rstrip('/')
    })

# -----------------------------------------------------------------------------
# Authentication API Endpoints
# -----------------------------------------------------------------------------

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not username or len(username) < 3:
        return jsonify({'success': False, 'message': 'ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร'}), 400

    if not email or '@' not in email:
        return jsonify({'success': False, 'message': 'รูปแบบอีเมลไม่ถูกต้อง'}), 400

    if not password or len(password) < 6:
        return jsonify({'success': False, 'message': 'รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร'}), 400

    password_hash = generate_password_hash(password)

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            user_id = cursor.lastrowid
            conn.commit()

        # Automatically log in the user
        session['user_id'] = user_id
        session['username'] = username

        return jsonify({
            'success': True,
            'message': 'สร้างบัญชีสำเร็จ',
            'user': {'id': user_id, 'username': username, 'email': email}
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรืออีเมลนี้ถูกใช้งานแล้ว'}), 409
    except Exception as e:
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'}), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    identifier = data.get('username', '').strip()
    password = data.get('password', '')

    if not identifier or not password:
        return jsonify({'success': False, 'message': 'กรุณากรอกชื่อผู้ใช้และรหัสผ่าน'}), 400

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?)',
            (identifier, identifier)
        )
        user = cursor.fetchone()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({
            'success': True,
            'message': 'เข้าสู่ระบบสำเร็จ',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    else:
        return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'}), 401


@app.route('/api/me', methods=['GET'])
def api_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'authenticated': False}), 200

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

    if user:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        })
    return jsonify({'authenticated': False}), 200


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'ออกจากระบบแล้ว'})


# -----------------------------------------------------------------------------
# Sign Language Prediction & Control Endpoints (Compatible with app.js)
# -----------------------------------------------------------------------------

current_prediction = {
    'prediction': 'พร้อมตรวจจับ',
    'confidence': '99.0%',
    'sentence': ''
}

@app.route('/api/prediction', methods=['GET'])
def get_prediction():
    return jsonify(current_prediction)


@app.route('/api/control', methods=['POST'])
def control_action():
    data = request.get_json() or {}
    action = data.get('action')

    if action == 'clear':
        current_prediction['sentence'] = ''
        current_prediction['prediction'] = 'ล้างประโยคแล้ว'
        current_prediction['confidence'] = '0.0%'
    elif action == 'backspace':
        words = current_prediction['sentence'].strip().split(' ')
        if words and words[0] != '':
            words.pop()
            current_prediction['sentence'] = ' '.join(words)
        current_prediction['prediction'] = 'ลบคำล่าสุดแล้ว'
        current_prediction['confidence'] = '0.0%'

    return jsonify(current_prediction)


@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    data = request.get_json(silent=True) or {}
    b64_str = data.get('image')
    
    if not b64_str or engine is None:
        return jsonify({'success': False, 'message': 'No image or engine not loaded'})
        
    try:
        label, confidence = engine.process_base64_image(b64_str)
        if label:
            # Simple voting could be implemented here or on client side
            # For simplicity we just take the confident prediction
            if label != current_prediction.get('last_confirmed', ''):
                sentence = current_prediction.get('sentence', '')
                words = sentence.split(' ') if sentence else []
                words.append(label)
                if len(words) > 7:
                    words = words[-7:]
                current_prediction['sentence'] = ' '.join(words).strip()
                current_prediction['last_confirmed'] = label
                
            current_prediction['prediction'] = label
            current_prediction['confidence'] = f"{confidence*100:.1f}%"
            
        return jsonify({'success': True, 'prediction': current_prediction.get('prediction', '')})
    except Exception as e:
        print("Error processing frame:", e)
        return jsonify({'success': False, 'error': str(e)})


@app.route('/video_feed')
def video_feed():
    # Return placeholder 204 or streaming generator
    return Response(b'', status=204)


import sys
import socket

def get_lan_ip():
    """Detect local LAN IP for mobile access"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def generate_self_signed_cert(cert_path='cert.pem', key_path='key.pem', lan_ip='127.0.0.1'):
    """Generate a self-signed SSL certificate for HTTPS mobile camera access."""
    try:
        # pyrefly: ignore [missing-import]
        from cryptography import x509  # type: ignore
        # pyrefly: ignore [missing-import]
        from cryptography.x509.oid import NameOID  # type: ignore
        # pyrefly: ignore [missing-import]
        from cryptography.hazmat.primitives import hashes, serialization  # type: ignore
        # pyrefly: ignore [missing-import]
        from cryptography.hazmat.primitives.asymmetric import rsa  # type: ignore

        # Check if existing cert is still valid (skip regeneration)
        if os.path.exists(cert_path) and os.path.exists(key_path):
            try:
                with open(cert_path, 'rb') as f:
                    existing = x509.load_pem_x509_certificate(f.read())
                # Re-generate if expiring within 7 days
                if existing.not_valid_after_utc > datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7):
                    print("[SSL] Using existing certificate.")
                    return cert_path, key_path
            except Exception:
                pass  # Regenerate if cert is corrupt

        print("[SSL] Generating new self-signed certificate...")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"SignSubs Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"SignSubs Dev"),
        ])

        # SAN: include both localhost and the LAN IP so the cert is valid for both
        san_list = [
            x509.DNSName(u"localhost"),
            x509.IPAddress(ipaddress.IPv4Address(u"127.0.0.1")),
        ]
        try:
            san_list.append(x509.IPAddress(ipaddress.IPv4Address(lan_ip)))
        except Exception:
            pass

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
            .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName(san_list), critical=False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

        with open(key_path, 'wb') as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))
        with open(cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        print(f"[SSL] Certificate saved: {cert_path}, {key_path}")
        return cert_path, key_path

    except ImportError:
        print("[SSL] cryptography package not found, falling back to 'adhoc' SSL.")
        return 'adhoc'
    except Exception as e:
        print(f"[SSL] Certificate generation failed: {e}, falling back to 'adhoc'.")
        return 'adhoc'


if __name__ == '__main__':
    # Always start with HTTPS for mobile camera support
    # Use --no-ssl flag to disable if needed for debugging
    use_ssl = '--no-ssl' not in sys.argv
    lan_ip = get_lan_ip()
    protocol = 'https' if use_ssl else 'http'

    if use_ssl:
        result = generate_self_signed_cert('cert.pem', 'key.pem', lan_ip)
        if result == 'adhoc':
            ssl_context = 'adhoc'
        else:
            ssl_context = result  # tuple (cert_path, key_path)
    else:
        ssl_context = None

    print("=" * 65)
    print("   SignSubs Server - Ready for PC & Mobile Camera")
    print("=" * 65)
    print(f"[*] PC Access (Local):        {protocol}://localhost:5000")
    print(f"[*] Mobile Access (Wi-Fi):    {protocol}://{lan_ip}:5000")
    print("-" * 65)
    if use_ssl:
        print("[!] HTTPS is ACTIVE — Mobile camera is ENABLED!")
        print("    On mobile browser: tap 'Advanced' -> 'Proceed to site'")
        print("    (Self-signed cert warning is expected — tap to continue)")
    else:
        print("[i] Running HTTP only (camera disabled on mobile).")
        print("    Remove --no-ssl flag to enable mobile camera.")
    print("-" * 65)
    print("Default demo user: admin | Password: 123456")
    print("=" * 65)

    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=ssl_context)
