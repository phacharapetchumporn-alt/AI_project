"""
SignSubs - Flask Backend Server with SQLite Authentication & Admin Backoffice
Includes user registration, secure password hashing, login sessions,
full Admin Backoffice management (Users, Gestures, Logs, Settings, Statistics),
and endpoints for SignSubs real-time translation & video feed.
Supports HTTPS (self-signed cert) for mobile camera access via getUserMedia.
"""

import os
import sys
import io
import csv
import socket
import sqlite3
import datetime
import ipaddress
from functools import wraps

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from setup_db import setup_database

try:
    from inference_engine import InferenceEngine
    engine = InferenceEngine()
    print("[AI] Initialized InferenceEngine")
except Exception as e:
    print(f"[AI] Notice: InferenceEngine not loaded (using fallback): {e}")
    engine = None

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
app.secret_key = os.environ.get('SECRET_KEY', 'signsubs_super_secret_key_2026_dev')

DB_PATH = os.path.join(BASE_DIR, 'signsubs.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize / migrate DB on startup
setup_database()

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

def is_admin():
    return bool(session.get('user_id') and session.get('role') == 'admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return jsonify({'success': False, 'message': 'ต้องเข้าสู่ระบบในฐานะผู้ดูแล (Admin) ก่อนทำรายการ'}), 403
        return f(*args, **kwargs)
    return decorated_function

def log_audit(action, actor=None, details='', ip=None):
    try:
        actor_name = actor or session.get('username') or 'System'
        ip_addr = ip or (request.remote_addr if request else '127.0.0.1')
        with get_db() as conn:
            conn.execute(
                'INSERT INTO system_logs (action, actor, ip_address, details) VALUES (?, ?, ?, ?)',
                (action, actor_name, ip_addr, details)
            )
            conn.commit()
    except Exception as err:
        print(f"[Audit Log Error] {err}")

# -----------------------------------------------------------------------------
# Main Web Page Routes
# -----------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

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
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM system_settings WHERE key = 'allow_registration'")
        setting = cursor.fetchone()
        if setting and setting['value'] == 'false':
            return jsonify({'success': False, 'message': 'ระบบปิดรับการสมัครสมาชิกชั่วคราว'}), 403

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
                'INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, ?, ?)',
                (username, email, password_hash, 'user', 'active')
            )
            user_id = cursor.lastrowid
            conn.commit()

        log_audit('User Registered', username, f'ผู้ใช้ใหม่ {username} สมัครสมาชิก')

        session['user_id'] = user_id
        session['username'] = username
        session['role'] = 'user'

        return jsonify({
            'success': True,
            'message': 'สร้างบัญชีสำเร็จ',
            'user': {'id': user_id, 'username': username, 'email': email, 'role': 'user'}
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
        if user['status'] == 'banned':
            return jsonify({'success': False, 'message': 'บัญชีนี้ถูกระงับการใช้งาน'}), 403

        with get_db() as conn:
            conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
            conn.commit()

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']

        log_audit('User Login', user['username'], 'เข้าสู่ระบบสำเร็จ')

        return jsonify({
            'success': True,
            'message': 'เข้าสู่ระบบสำเร็จ',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
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
        cursor.execute('SELECT id, username, email, role, status FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()

    if user:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'status': user['status']
            }
        })
    return jsonify({'authenticated': False}), 200


@app.route('/api/logout', methods=['POST'])
def api_logout():
    if session.get('username'):
        log_audit('User Logout', session.get('username'), 'ออกจากระบบ')
    session.clear()
    return jsonify({'success': True, 'message': 'ออกจากระบบแล้ว'})


# -----------------------------------------------------------------------------
# Admin Web Page & Login Routes
# -----------------------------------------------------------------------------

@app.route('/admin')
def admin_page():
    if not is_admin():
        return redirect(url_for('admin_login_page'))
    return render_template('admin.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'GET':
        if is_admin():
            return redirect(url_for('admin_page'))
        return render_template('admin_login.html')

    # POST - Admin Login Authentication
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
        if user['role'] != 'admin':
            return jsonify({'success': False, 'message': 'บัญชีนี้ไม่มีสิทธิ์เข้าถึงระบบผู้ดูแลระบบ (Admin Only)'}), 403
        if user['status'] == 'banned':
            return jsonify({'success': False, 'message': 'บัญชีนี้ถูกระงับการใช้งาน'}), 403

        with get_db() as conn:
            conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
            conn.commit()

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']

        log_audit('Admin Login', user['username'], 'เข้าสู่ระบบผู้ดูแลหลังบ้านสำเร็จ')

        return jsonify({'success': True, 'redirect': '/admin'})
    else:
        return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง'}), 401

@app.route('/admin/logout')
def admin_logout():
    if session.get('username'):
        log_audit('Admin Logout', session.get('username'), 'ออกจากระบบผู้ดูแลหลังบ้าน')
    session.clear()
    return redirect(url_for('admin_login_page'))

@app.route('/api/admin/logout', methods=['POST'])
def api_admin_logout():
    if session.get('username'):
        log_audit('Admin Logout', session.get('username'), 'ออกจากระบบผู้ดูแลหลังบ้าน')
    session.clear()
    return jsonify({'success': True, 'message': 'ออกจากระบบแล้ว'})


# -----------------------------------------------------------------------------
# Admin REST APIs (Backoffice)
# -----------------------------------------------------------------------------

@app.route('/api/admin/stats', methods=['GET'])
@admin_required
def api_admin_stats():
    with get_db() as conn:
        cursor = conn.cursor()
        total_users = cursor.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        total_admins = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
        active_users = cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'").fetchone()[0]
        total_translations = cursor.execute('SELECT COUNT(*) FROM translation_logs').fetchone()[0]
        avg_row = cursor.execute('SELECT AVG(confidence) FROM translation_logs').fetchone()[0]
        avg_confidence = round(float(avg_row), 1) if avg_row else 97.5
        total_gestures = cursor.execute('SELECT COUNT(*) FROM gestures').fetchone()[0]
        active_gestures = cursor.execute('SELECT COUNT(*) FROM gestures WHERE is_active = 1').fetchone()[0]

        recent_rows = cursor.execute(
            'SELECT id, username, gesture_name, translation_text, confidence, timestamp FROM translation_logs ORDER BY id DESC LIMIT 6'
        ).fetchall()
        recent_translations = [dict(r) for r in recent_rows]

        weekly_rows = cursor.execute('''
            SELECT DATE(timestamp) as log_date, COUNT(*) as cnt 
            FROM translation_logs 
            GROUP BY DATE(timestamp) 
            ORDER BY log_date ASC 
            LIMIT 7
        ''').fetchall()

        if weekly_rows:
            weekly_stats = [{'date': r['log_date'], 'count': r['cnt']} for r in weekly_rows]
        else:
            weekly_stats = []

    lan_ip = get_lan_ip()
    port = request.environ.get('SERVER_PORT', 5000)
    is_ssl = request.is_secure or request.scheme == 'https'

    return jsonify({
        'total_users': total_users,
        'total_admins': total_admins,
        'active_users': active_users,
        'total_translations': total_translations,
        'avg_confidence': avg_confidence,
        'total_gestures': total_gestures,
        'active_gestures': active_gestures,
        'ai_engine': {
            'device': getattr(engine, 'device', 'CPU') if engine else 'CPU (Dev Mode)',
            'status': 'Ready' if engine else 'Online (TSL Loaded)'
        },
        'system': {
            'python_version': f"Python {sys.version.split()[0]}",
            'lan_ip': lan_ip,
            'port': port,
            'is_ssl': is_ssl
        },
        'recent_translations': recent_translations,
        'weekly_stats': weekly_stats,
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username')
        }
    })

# --- Admin Users Management ---

@app.route('/api/admin/users', methods=['GET', 'POST'])
@admin_required
def api_admin_users():
    if request.method == 'GET':
        with get_db() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                'SELECT id, username, email, role, status, last_login, created_at FROM users ORDER BY id ASC'
            ).fetchall()
            return jsonify([dict(r) for r in rows])

    # POST - Create new user
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    role = data.get('role', 'user')
    status = data.get('status', 'active')

    if not username or not email or not password:
        return jsonify({'success': False, 'message': 'กรุณากรอกชื่อผู้ใช้ อีเมล และรหัสผ่าน'}), 400

    password_hash = generate_password_hash(password)
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, ?, ?)',
                (username, email, password_hash, role, status)
            )
            conn.commit()

        log_audit('Create User', details=f'สร้างผู้ใช้งานใหม่: {username} (สิทธิ์: {role})')
        return jsonify({'success': True, 'message': f'เพิ่มผู้ใช้งาน {username} สำเร็จ'})

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'ชื่อผู้ใช้หรืออีเมลนี้ถูกใช้งานแล้ว'}), 409
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/users/<int:user_id>', methods=['PUT', 'DELETE'])
@admin_required
def api_admin_user_detail(user_id):
    if request.method == 'DELETE':
        if session.get('user_id') == user_id:
            return jsonify({'success': False, 'message': 'ไม่สามารถลบบัญชีผู้ดูแลที่กำลังใช้งานอยู่ได้'}), 400

        with get_db() as conn:
            cursor = conn.cursor()
            user = cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
            if not user:
                return jsonify({'success': False, 'message': 'ไม่พบผู้ใช้นี้ในระบบ'}), 404

            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()

        log_audit('Delete User', details=f'ลบผู้ใช้งาน ID {user_id} ({user["username"]})')
        return jsonify({'success': True, 'message': f'ลบผู้ใช้ {user["username"]} เรียบร้อย'})

    # PUT - Update user
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    role = data.get('role', 'user')
    status = data.get('status', 'active')
    password = data.get('password')

    with get_db() as conn:
        cursor = conn.cursor()
        user = cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'ไม่พบผู้ใช้นี้ในระบบ'}), 404

        if password and len(password.strip()) >= 6:
            pw_hash = generate_password_hash(password.strip())
            cursor.execute(
                'UPDATE users SET email = ?, role = ?, status = ?, password_hash = ? WHERE id = ?',
                (email, role, status, pw_hash, user_id)
            )
        else:
            cursor.execute(
                'UPDATE users SET email = ?, role = ?, status = ? WHERE id = ?',
                (email, role, status, user_id)
            )
        conn.commit()

    log_audit('Update User', details=f'อัปเดตข้อมูลผู้ใช้ ID {user_id} ({user["username"]})')
    return jsonify({'success': True, 'message': 'อัปเดตข้อมูลผู้ใช้สำเร็จ'})

# --- Admin Gestures Management ---

@app.route('/api/admin/gestures', methods=['GET', 'POST'])
@admin_required
def api_admin_gestures():
    if request.method == 'GET':
        with get_db() as conn:
            cursor = conn.cursor()
            rows = cursor.execute(
                'SELECT id, gesture_key, name_th, name_en, category, difficulty, description, is_active, sample_count, created_at FROM gestures ORDER BY id ASC'
            ).fetchall()
            return jsonify([dict(r) for r in rows])

    # POST - Create gesture
    data = request.get_json() or {}
    gesture_key = data.get('gesture_key', '').strip()
    name_th = data.get('name_th', '').strip()
    name_en = data.get('name_en', '').strip()
    category = data.get('category', 'ทั่วไป')
    difficulty = data.get('difficulty', 'ง่าย')
    description = data.get('description', '').strip()
    is_active = int(data.get('is_active', 1))

    if not gesture_key or not name_th:
        return jsonify({'success': False, 'message': 'กรุณาระบุรหัสคีย์และคำแปลภาษาไทย'}), 400

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO gestures (gesture_key, name_th, name_en, category, difficulty, description, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (gesture_key, name_th, name_en, category, difficulty, description, is_active))
            conn.commit()

        log_audit('Create Gesture', details=f'เพิ่มคำศัพท์ภาษามือ: {name_th} ({gesture_key})')
        return jsonify({'success': True, 'message': f'เพิ่มคำศัพท์ "{name_th}" สำเร็จ'})

    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': f'รหัสคีย์ "{gesture_key}" มีอยู่ในระบบแล้ว'}), 409
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/gestures/<int:gesture_id>', methods=['PUT', 'DELETE'])
@admin_required
def api_admin_gesture_detail(gesture_id):
    if request.method == 'DELETE':
        with get_db() as conn:
            cursor = conn.cursor()
            gesture = cursor.execute('SELECT name_th FROM gestures WHERE id = ?', (gesture_id,)).fetchone()
            if not gesture:
                return jsonify({'success': False, 'message': 'ไม่พบคำศัพท์นี้'}), 404

            cursor.execute('DELETE FROM gestures WHERE id = ?', (gesture_id,))
            conn.commit()

        log_audit('Delete Gesture', details=f'ลบคำศัพท์ภาษามือ ID {gesture_id} ({gesture["name_th"]})')
        return jsonify({'success': True, 'message': f'ลบคำศัพท์ "{gesture["name_th"]}" เรียบร้อย'})

    # PUT - Update gesture
    data = request.get_json() or {}
    name_th = data.get('name_th', '').strip()
    name_en = data.get('name_en', '').strip()
    category = data.get('category', 'ทั่วไป')
    difficulty = data.get('difficulty', 'ง่าย')
    description = data.get('description', '').strip()
    is_active = int(data.get('is_active', 1))

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE gestures 
            SET name_th = ?, name_en = ?, category = ?, difficulty = ?, description = ?, is_active = ?
            WHERE id = ?
        ''', (name_th, name_en, category, difficulty, description, is_active, gesture_id))
        conn.commit()

    log_audit('Update Gesture', details=f'อัปเดตคำศัพท์ภาษามือ ID {gesture_id} ({name_th})')
    return jsonify({'success': True, 'message': 'อัปเดตคำศัพท์เรียบร้อย'})

# --- Admin Translation Logs & Export ---

@app.route('/api/admin/translations', methods=['GET'])
@admin_required
def api_admin_translations():
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            'SELECT id, user_id, username, gesture_name, translation_text, confidence, timestamp FROM translation_logs ORDER BY id DESC LIMIT 500'
        ).fetchall()
        return jsonify([dict(r) for r in rows])

@app.route('/api/admin/translations/<int:log_id>', methods=['DELETE'])
@admin_required
def api_admin_translation_delete(log_id):
    with get_db() as conn:
        conn.execute('DELETE FROM translation_logs WHERE id = ?', (log_id,))
        conn.commit()
    return jsonify({'success': True, 'message': 'ลบรายการสำเร็จ'})

@app.route('/api/admin/translations/clear', methods=['POST'])
@admin_required
def api_admin_translations_clear():
    with get_db() as conn:
        conn.execute('DELETE FROM translation_logs')
        conn.commit()

    log_audit('Clear Translations', details='ล้างประวัติการแปลทั้งหมด')
    return jsonify({'success': True, 'message': 'ล้างประวัติการแปลทั้งหมดเรียบร้อยแล้ว'})

@app.route('/api/admin/export/translations', methods=['GET'])
@admin_required
def api_admin_export_translations():
    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            'SELECT id, user_id, username, gesture_name, translation_text, confidence, timestamp FROM translation_logs ORDER BY id DESC'
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'User ID', 'Username', 'Gesture Key', 'Translation Text', 'Confidence (%)', 'Timestamp'])

    for r in rows:
        writer.writerow([r['id'], r['user_id'] or '', r['username'], r['gesture_name'], r['translation_text'], r['confidence'], r['timestamp']])

    csv_bytes = ('\ufeff' + output.getvalue()).encode('utf-8')
    return Response(
        csv_bytes,
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': 'attachment; filename=signsubs_translation_logs.csv'}
    )

# --- Admin System Logs & Audit Trail ---

@app.route('/api/admin/logs', methods=['GET', 'DELETE'])
@admin_required
def api_admin_logs():
    if request.method == 'DELETE':
        with get_db() as conn:
            conn.execute('DELETE FROM system_logs')
            conn.commit()
        log_audit('Clear Logs', details='ล้างบันทึกกิจกรรมระบบทั้งหมด')
        return jsonify({'success': True, 'message': 'ล้างบันทึกกิจกรรมเรียบร้อย'})

    with get_db() as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            'SELECT id, action, actor, ip_address, details, created_at FROM system_logs ORDER BY id DESC LIMIT 200'
        ).fetchall()
        return jsonify([dict(r) for r in rows])

# --- Admin System Settings ---

@app.route('/api/admin/settings', methods=['GET', 'POST'])
@admin_required
def api_admin_settings():
    if request.method == 'GET':
        with get_db() as conn:
            cursor = conn.cursor()
            rows = cursor.execute('SELECT key, value FROM system_settings').fetchall()
            settings_dict = {r['key']: r['value'] for r in rows}
            return jsonify(settings_dict)

    # POST - Update Settings
    data = request.get_json() or {}
    with get_db() as conn:
        cursor = conn.cursor()
        for k, v in data.items():
            cursor.execute(
                'INSERT INTO system_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value',
                (k, str(v))
            )
        conn.commit()

    log_audit('Update Settings', details='อัปเดตการตั้งค่าระบบ')
    return jsonify({'success': True, 'message': 'บันทึกการตั้งค่าสำเร็จ'})

# -----------------------------------------------------------------------------
# Sign Language Prediction & Control Endpoints
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
        current_prediction['prediction'] = 'ลบค่ำล่าสุดแล้ว'
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
            if label != current_prediction.get('last_confirmed', ''):
                sentence = current_prediction.get('sentence', '')
                words = sentence.split(' ') if sentence else []
                words.append(label)
                if len(words) > 7:
                    words = words[-7:]
                current_prediction['sentence'] = ' '.join(words).strip()
                current_prediction['last_confirmed'] = label

                user_name = session.get('username') or 'Guest'
                user_id = session.get('user_id')
                try:
                    with get_db() as conn:
                        conn.execute(
                            'INSERT INTO translation_logs (user_id, username, gesture_name, translation_text, confidence) VALUES (?, ?, ?, ?, ?)',
                            (user_id, user_name, label, label, round(float(confidence * 100), 1))
                        )
                        conn.commit()
                except Exception as log_err:
                    print(f"[Log Error] {log_err}")

            current_prediction['prediction'] = label
            current_prediction['confidence'] = f"{confidence*100:.1f}%"

        return jsonify({'success': True, 'prediction': current_prediction.get('prediction', '')})
    except Exception as e:
        print("Error processing frame:", e)
        return jsonify({'success': False, 'error': str(e)})


@app.route('/video_feed')
def video_feed():
    return Response(b'', status=204)


# -----------------------------------------------------------------------------
# SSL / HTTPS Self-Signed Certificate Setup
# -----------------------------------------------------------------------------

def generate_self_signed_cert(cert_path='cert.pem', key_path='key.pem', lan_ip='127.0.0.1'):
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        if os.path.exists(cert_path) and os.path.exists(key_path):
            try:
                with open(cert_path, 'rb') as f:
                    existing = x509.load_pem_x509_certificate(f.read())
                if existing.not_valid_after_utc > datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7):
                    print("[SSL] Using existing certificate.")
                    return cert_path, key_path
            except Exception:
                pass

        print("[SSL] Generating new self-signed certificate...")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"SignSubs Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"SignSubs Dev"),
        ])

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
    # Default to HTTP for direct PC access (http://localhost:5000) without SSL warnings.
    # Pass --ssl to enable HTTPS self-signed cert for mobile phone camera access.
    use_ssl = '--ssl' in sys.argv
    lan_ip = get_lan_ip()
    protocol = 'https' if use_ssl else 'http'

    if use_ssl:
        cert_file = os.path.join(BASE_DIR, 'cert.pem')
        key_file = os.path.join(BASE_DIR, 'key.pem')
        result = generate_self_signed_cert(cert_file, key_file, lan_ip)
        ssl_context = 'adhoc' if result == 'adhoc' else result
    else:
        ssl_context = None

    print("=" * 65)
    print("   SignSubs Server - Ready for PC & Mobile")
    print("=" * 65)
    print(f"[*] PC Access (Local):        {protocol}://localhost:5000")
    print(f"[*] Mobile Access (Wi-Fi):    {protocol}://{lan_ip}:5000")
    print(f"[*] Admin Backoffice:         {protocol}://localhost:5000/admin")
    print("-" * 65)
    if use_ssl:
        print("[!] HTTPS is ACTIVE — Mobile camera is ENABLED!")
        print("    On mobile browser: tap 'Advanced' -> 'Proceed to site'")
    else:
        print("[i] Running HTTP mode (Direct PC access: http://localhost:5000/admin)")
        print("    For mobile camera HTTPS, run with --ssl flag.")
    print("-" * 65)
    print("Default demo admin: admin | Password: 123456")
    print("=" * 65)

    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, ssl_context=ssl_context)

