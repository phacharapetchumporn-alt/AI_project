import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# เช็กความพร้อมของไฟล์สำหรับเทรนโมเดล
dataset_filename = "tsl_one_s_dataset.json"
label_filename = "tsl_one_s_id_to_label.json"
pose_dir = "TSL-ONE-Pose"

print("🔍 กำลังตรวจสอบไฟล์และชุดข้อมูลในระบบ...")
print(f"  - ไฟล์ Dataset JSON: {'✅ พบ' if os.path.exists(dataset_filename) else '❌ ไม่พบ'}")
print(f"  - ไฟล์ Label JSON:   {'✅ พบ' if os.path.exists(label_filename) else '❌ ไม่พบ'}")
print(f"  - โฟลเดอร์ท่าทาง Pose: {'✅ พบ' if os.path.exists(pose_dir) else '❌ ไม่พบ'}")

if os.path.exists(pose_dir):
    npy_files = [f for f in os.listdir(pose_dir) if f.endswith(".npy")]
    print(f"  - จำนวนไฟล์ .npy ทั้งหมด: {len(npy_files)} ไฟล์")
    if len(npy_files) > 0:
        import numpy as np
        sample = np.load(os.path.join(pose_dir, npy_files[0]))
        print(f"  - ตัวอย่างรูปร่างข้อมูลไฟล์แรก ({npy_files[0]}): {sample.shape} (Frames x Features)")

if os.path.exists(dataset_filename) and os.path.exists(label_filename):
    with open(label_filename, "r", encoding="utf-8") as f:
        labels = json.load(f)
    print(f"\n✅ ข้อมูลพร้อมใช้งาน! ทั้งหมด {len(labels)} คำศัพท์")
    print("💡 สามารถสั่งรัน 'python train1.py' เพื่อเริ่มเทรนโมเดลได้ทันที")