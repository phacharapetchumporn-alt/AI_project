import os
import sqlite3
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'signsubs.db')

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'active',
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add missing columns if user table already existed
    cols = [col[1] for col in cursor.execute('PRAGMA table_info(users)').fetchall()]
    if 'role' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
    if 'status' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
    if 'last_login' not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")

    # Ensure admin user exists with role 'admin'
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    admin_user = cursor.fetchone()
    if not admin_user:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, 'admin', 'active')",
            ('admin', 'admin@signsubs.ai', generate_password_hash('123456'))
        )
    else:
        cursor.execute("UPDATE users SET role = 'admin' WHERE username = 'admin'")

    # Add sample demo member users if count <= 1
    cursor.execute("SELECT COUNT(*) as cnt FROM users")
    if cursor.fetchone()['cnt'] <= 1:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, 'user', 'active')",
            ('student1', 'student1@university.ac.th', generate_password_hash('123456'))
        )
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role, status) VALUES (?, ?, ?, 'user', 'active')",
            ('teacher_somchai', 'somchai@school.ac.th', generate_password_hash('123456'))
        )

    # 2. Gestures (Vocabulary) Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gestures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gesture_key TEXT UNIQUE NOT NULL,
            name_th TEXT NOT NULL,
            name_en TEXT NOT NULL,
            category TEXT DEFAULT 'ทั่วไป',
            description TEXT,
            difficulty TEXT DEFAULT 'ง่าย',
            is_active INTEGER DEFAULT 1,
            sample_count INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed initial gestures if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM gestures")
    if cursor.fetchone()['cnt'] == 0:
        initial_gestures = [
            ('1', 'หนึ่ง', 'One', 'ตัวเลข', 'ชูนิ้วชี้ขึ้นนิ้วเดียวเพื่อแสดงเลข 1', 'ง่าย', 1, 150),
            ('2', 'สอง', 'Two', 'ตัวเลข', 'ชูนิ้วชี้และนิ้วกลางขึ้นเพื่อแสดงเลข 2', 'ง่าย', 1, 145),
            ('3', 'สาม', 'Three', 'ตัวเลข', 'ชูนิ้วโป้ง นิ้วชี้ และนิ้วกลาง หรือสามนิ้ว', 'ง่าย', 1, 140),
            ('4', 'สี่', 'Four', 'ตัวเลข', 'ชู 4 นิ้วโดยงอนิ้วโป้งเข้าหาฝ่ามือ', 'ง่าย', 1, 138),
            ('5', 'ห้า', 'Five', 'ตัวเลข', 'กางทั้ง 5 นิ้วออกเพื่อแสดงเลข 5', 'ง่าย', 1, 155),
            ('6', 'หก', 'Six', 'ตัวเลข', 'งอนิ้วก้อย นิ้วโป้งสัมผัสนิ้วก้อย', 'ปานกลาง', 1, 120),
            ('7', 'เจ็ด', 'Seven', 'ตัวเลข', 'งอนิ้วนาง นิ้วโป้งสัมผัสนิ้วนาง', 'ปานกลาง', 1, 120),
            ('8', 'แปด', 'Eight', 'ตัวเลข', 'งอนิ้วกลาง นิ้วโป้งสัมผัสนิ้วกลาง', 'ปานกลาง', 1, 115),
            ('9', 'เก้า', 'Nine', 'ตัวเลข', 'งอนิ้วชี้เป็นตะขอ', 'ปานกลาง', 1, 110),
            ('10', 'สิบ', 'Ten', 'ตัวเลข', 'สลัดนิ้วโป้งหรือชูสองมือคว่ำ', 'ปานกลาง', 1, 125),
            ('hello', 'สวัสดี', 'Hello', 'การทักทาย', 'ยกมือขึ้นระดับคิ้วแล้วผายออกไปข้างหน้า', 'ง่าย', 1, 210),
            ('thankyou', 'ขอบคุณ', 'Thank you', 'การทักทาย', 'แตะปลายนิ้วที่คางแล้วผายมือออกข้างหน้า', 'ง่าย', 1, 195),
            ('yes', 'ใช่ / ตกลง', 'Yes', 'คำตอบรับ', 'กำปั้นขยับขึ้นลงคล้ายการพยักหน้า', 'ง่าย', 1, 160),
            ('no', 'ไม่ / ปฏิเสธ', 'No', 'คำตอบรับ', 'ส่ายนิ้วชี้หรือประกบนิ้วโป้งกับนิ้วชี้-กลาง', 'ง่าย', 1, 150),
            ('love', 'รัก', 'Love / I Love You', 'ความรู้สึก', 'ชูนิ้วโป้ง นิ้วชี้ และนิ้วก้อย (ILY sign)', 'ง่าย', 1, 230),
            ('help', 'ช่วยด้วย', 'Help', 'ฉุกเฉิน/ขอความช่วยเหลือ', 'วางกำปั้นบนฝ่ามืออีกข้างแล้วยกขึ้นพร้อมกัน', 'ยาก', 1, 105),
        ]
        cursor.executemany('''
            INSERT INTO gestures (gesture_key, name_th, name_en, category, description, difficulty, is_active, sample_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', initial_gestures)

    # 3. Translation logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT DEFAULT 'Guest',
            gesture_name TEXT NOT NULL,
            translation_text TEXT NOT NULL,
            confidence REAL DEFAULT 0.0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed sample translation logs if empty
    cursor.execute("SELECT COUNT(*) as cnt FROM translation_logs")
    if cursor.fetchone()['cnt'] == 0:
        sample_logs = [
            (1, 'admin', 'hello', 'สวัสดี', 98.5),
            (2, 'student1', '1', 'หนึ่ง', 96.2),
            (2, 'student1', '2', 'สอง', 97.4),
            (3, 'teacher_somchai', 'thankyou', 'ขอบคุณ', 99.1),
            (None, 'Guest', 'love', 'รัก', 95.8),
            (None, 'Guest', 'yes', 'ใช่ / ตกลง', 94.0),
            (2, 'student1', 'help', 'ช่วยด้วย', 91.5),
            (1, 'admin', '5', 'ห้า', 99.4),
        ]
        cursor.executemany('''
            INSERT INTO translation_logs (user_id, username, gesture_name, translation_text, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_logs)

    # 4. System Logs (Audit Trail)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            actor TEXT DEFAULT 'System',
            ip_address TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute("SELECT COUNT(*) as cnt FROM system_logs")
    if cursor.fetchone()['cnt'] == 0:
        sample_audit = [
            ('System Start', 'System', '127.0.0.1', 'เซิร์ฟเวอร์ SignSubs เริ่มทำงานและเชื่อมต่อฐานข้อมูล'),
            ('Admin Login', 'admin', '127.0.0.1', 'ผู้ดูแลระบบ admin เข้าสู่ระบบสำเร็จ'),
            ('Model Loaded', 'System', '127.0.0.1', 'โหลดโมเดล Bi-LSTM และ MediaPipe พร้อมใช้งาน'),
            ('User Registered', 'student1', '192.168.1.45', 'ผู้ใช้ใหม่ student1 ลงทะเบียนเข้าสู่ระบบ'),
        ]
        cursor.executemany('''
            INSERT INTO system_logs (action, actor, ip_address, details)
            VALUES (?, ?, ?, ?)
        ''', sample_audit)

    # 5. System Settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT
        )
    ''')

    default_settings = [
        ('site_name', 'SignSubs AI Backoffice', 'ชื่อระบบหลังบ้าน'),
        ('confidence_threshold', '75', 'เกณฑ์ความมั่นใจขั้นต่ำของ AI (เปอร์เซ็นต์)'),
        ('allow_registration', 'true', 'อนุญาตให้บุคคลทั่วไปสมัครสมาชิกใหม่ได้'),
        ('allow_guest_translation', 'true', 'อนุญาตให้ผู้เยี่ยมชมใช้งานกล้องแปลภาษามือได้'),
        ('maintenance_mode', 'false', 'เปิดโหมดปิดปรับปรุงระบบชั่วคราว'),
        ('announcement', 'ยินดีต้อนรับสู่ระบบ SignSubs อัปเดตโมเดล Bi-LSTM เวอร์ชั่นล่าสุดเรียบร้อยแล้ว', 'ข้อความประกาศบนหน้าเว็บ'),
    ]

    for k, v, d in default_settings:
        cursor.execute("INSERT OR IGNORE INTO system_settings (key, value, description) VALUES (?, ?, ?)", (k, v, d))

    conn.commit()
    conn.close()
    print("[DB] Database setup and migrations completed successfully.")

if __name__ == '__main__':
    setup_database()
