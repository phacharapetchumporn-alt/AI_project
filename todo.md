# Project Task Roadmap: TSL-51 Thai Sign Language AI Model Integration

## Overview
- **Objective**: นำเข้าชุดข้อมูลภาษามือไทย TSL-51 (51 คำศัพท์ + 1 null_act) แปลงพิกัดมือ 126 Features เข้าสู่ระบบ ฝึกสอนโมเดล Bi-LSTM ใหม่ และเชื่อมต่อกับระบบเว็บ SignSubs
- **Dataset Source**: `Namonpas/thai-sign-language-tsl51` ใน `C:\TSL-51`
- **Target Files**: `record_AI/convert_tsl51.py`, `record_AI/train_model.py`, `action_model.pth`, `label_encoder.pkl`, `scaler.pkl`

---

## Phase 1: Dataset Acquisition & Cleanup in C:\TSL-51
- [x] Task 1.1: ลบไฟล์ขยะที่ค้าง/ไม่สมบูรณ์ (.incomplete, .lock) และไฟล์ที่ไม่จำเป็น (`landmarks/user_sentence/`) ใน `C:\TSL-51` เพื่อคืนพื้นที่ดิสก์
- [x] Task 1.2: ดาวน์โหลดไฟล์จำเป็นให้ครบสมบูรณ์ (`metadata/*`, `landmarks/user_sign/*` 638 ไฟล์)

## Phase 2: Data Preprocessing & Conversion Pipeline
- [x] Task 2.1: สร้างสคริปต์ `record_AI/convert_tsl51.py` สำหรับแปลงไฟล์ CSV จาก TSL-51 เป็น `.npy`
- [x] Task 2.2: ดึงข้อมูลพิกัดมือซ้าย 63 ค่า (`lh`) + มือขวา 63 ค่า (`rh`) รวม 126 ค่า เติม 0 ในเฟรมที่ไม่มีมือ
- [x] Task 2.3: ปรับจำนวนเฟรมของแต่ละ sample ให้เป็น 30 frames ด้วย Linear Interpolation
- [x] Task 2.4: แม็ปรหัสท่าทางเข้ากับชื่อคำศัพท์ภาษาไทยจริงจาก Metadata และบันทึกลง `record_AI/sequences/` (แปลงสำเร็จ 638 ตัวอย่าง 58 คำศัพท์)

## Phase 3: Model Architecture & Training
- [x] Task 3.1: ปรับแต่ง `record_AI/train_model.py` ให้รองรับ 58 classes (57 คำศัพท์ภาษาไทย + 1 ท่าพัก null_act)
- [x] Task 3.2: คำนวณค่า Mean/Std สากล และสร้าง `scaler.pkl` และ `label_encoder.pkl` ภาษาไทย
- [x] Task 3.3: ฝึกสอนโมเดล Bi-LSTM Attention (80 Epochs, Val Acc 96.9%, Train Acc 100%) และบันทึก `action_model.pth`

## Phase 4: Integration & Web Verification
- [x] Task 4.1: อัปเดตไฟล์โมเดลชุดใหม่ (`action_model.pth`, `label_encoder.pkl`, `scaler.pkl`) เข้าสู่ระบบ
- [x] Task 4.2: ทดสอบโหลด `InferenceEngine` ยืนยันการอ่าน 58 classes ภาษาไทย (Ready: True, BiLSTMAttentionModel)
- [ ] Task 4.3: ทดสอบการทำงานของ Web Server และ Real-time prediction ผ่านกล้อง
