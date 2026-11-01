# Project Task Roadmap: Clean & Professional Project Organization

## Overview
- **Objective**: คัดแยกและลบไฟล์ที่ไม่เกี่ยวข้องกับระบบหน้าเว็บ (Web Application) จัดระเบียบโครงสร้างโฟลเดอร์ให้สวยงาม มีมาตรฐานแบบมืออาชีพ และป้องกันไฟล์ขยะไม่ให้เข้า Git
- **Target Scope**: ไฟล์และโฟลเดอร์ทั้งหมดใน `d:\project1.1`

---

## Phase 1: Analysis & File Audit
- [x] Task 1.1: ตรวจสอบความเชื่อมโยงของไฟล์ระบบเว็บ (`app.py`, `templates/`, `static/`, `inference_engine.py`, `setup_db.py`, `signsubs.db`, `cert.pem`, `key.pem`)
- [x] Task 1.2: ระบุไฟล์ขยะชั่วคราวและไฟล์ซ้ำซ้อน (`err.txt`, `test_import.py`, โมเดลซ้ำระหว่าง Root กับ `record_AI/`)
- [x] Task 1.3: ระบุไฟล์ชุดข้อมูลเทรนโมเดลที่ไม่เกี่ยวข้องกับหน้าเว็บ (`sequences/`, `tflite_output/`, `node_modules/`)

## Phase 2: Safe Cleanup (ลบไฟล์ส่วนเกินและไฟล์ขยะ)
- [x] Task 2.1: ลบไฟล์ชั่วคราว/ทดสอบเฉพาะกิจ (`err.txt`, `test_import.py`)
- [x] Task 2.2: ลบไฟล์ขยะ `node_modules/` (เนื่องจากหน้าเว็บใช้ CDN Supabase ทั้งหมดแล้ว)
- [x] Task 2.3: เคลียร์/จัดการชุดข้อมูลเทรน `sequences/` (ย้ายไป `record_AI/sequences/`) และไฟล์ส่งออกที่ไม่ใช้ `tflite_output/`

## Phase 3: Directory Structuring & Deduplication (จัดระเบียบโครงสร้าง)
- [x] Task 3.1: ขจัดไฟล์โมเดลซ้ำซ้อน ให้ระบบ Web และ AI ชี้ไปที่แหล่งเดียวที่ชัดเจน
- [x] Task 3.2: จัดหมวดหมู่โฟลเดอร์ AI/Data ให้เป็นระเบียบ เป็นสัดส่วนแยกจาก Web Application (`record_AI/` รวบรวม `collect_data.py`, `train_model.py`, `sequences/`)
- [x] Task 3.3: ตรวจสอบ Path การเรียกใช้งานใน `inference_engine.py` และ `realtime_predict.py` ให้ถูกต้อง ไม่แตกหัก

## Phase 4: Git Configuration & Hygiene
- [x] Task 4.1: ปรับปรุงไฟล์ `.gitignore` ให้ครอบคลุม `__pycache__/`, SSL certs, databases, และ temporary files
- [x] Task 4.2: ทำความสะอาด Git index จากไฟล์ที่ถูกละเว้น

## Phase 5: Verification & Quality Assurance
- [x] Task 5.1: ทดสอบ Import `app.py` และ `InferenceEngine` เพื่อยืนยันว่าโหลดโมเดลและรันได้ปกติ (ผ่านเรียบร้อยด้วย Python 3.12)
- [x] Task 5.2: ตรวจสอบการแสดงผลหน้าเว็บ `index.html`, `admin.html`, `admin_login.html` และ asset ต่างๆ (ครบถ้วนสมบูรณ์)
- [x] Task 5.3: สรุปโครงสร้างใหม่หลังจัดระเบียบเสร็จสมบูรณ์
