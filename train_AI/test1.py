import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# โหลดไฟล์ dataset
with open("tsl_one_s_dataset.json", "r", encoding="utf-8") as f:
  dataset_info = json.load(f)

# ตรวจสอบประเภทข้อมูลว่าเป็น List หรือ Dict
print("ประเภทข้อมูล:", type(dataset_info))

if isinstance(dataset_info, dict):
  print("Keys:", dataset_info.keys())
elif isinstance(dataset_info, list):
  print(f"ข้อมูลเป็น List มีทั้งหมด {len(dataset_info)} รายการ")
  if len(dataset_info) > 0:
    print("ตัวอย่างข้อมูลชิ้นแรก (Index 0):", dataset_info[0])