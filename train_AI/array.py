import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# โหลดไฟล์แปลง ID เป็นชื่อคำศัพท์
with open("tsl_one_s_id_to_label.json", "r", encoding="utf-8") as f:
  id_to_label = json.load(f)

print("ตัวอย่างคำศัพท์คำแรก:", id_to_label.get("0"))

# โหลดไฟล์โครงสร้าง Dataset
with open("tsl_one_s_dataset.json", "r", encoding="utf-8") as f:
  dataset_info = json.load(f)

print("ข้อมูล Dataset โหลดสำเร็จเรียบร้อย!")