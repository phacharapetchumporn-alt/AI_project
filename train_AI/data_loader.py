import json
import os
import sys
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import os
import sys
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# =========================
# 1. กำหนดค่าเริ่มต้นและไฟล์ Dataset
# =========================
DATA_DIR = "TSL-ONE-Pose"
DATASET_JSON = "tsl_one_s_dataset.json"
LABEL_JSON = "tsl_one_s_id_to_label.json"
DEFAULT_SEQUENCE_LENGTH = 30  # จำนวนเฟรมมาตรฐานต่อ sequence


def get_label_mappings(label_json_path=LABEL_JSON):
    """โหลด Dictionary แมป ID <-> Label name"""
    with open(label_json_path, "r", encoding="utf-8") as f:
        id_to_label = json.load(f)
    gloss_to_id = {v.lower().strip(): int(k) for k, v in id_to_label.items()}
    return id_to_label, gloss_to_id


def pad_or_sample_sequence(seq, target_len=DEFAULT_SEQUENCE_LENGTH):
    """
    ปรับขนาดความยาวของ Sequence ให้เท่ากับ target_len:
    - ถ้าเฟรมมากกว่า: ใช้ Uniform Sampling กระจายเฟรมให้ทั่วทั้งคลิป
    - ถ้าน้อยกว่า: เติม 0 (Zero Padding) ที่ด้านท้าย
    """
    current_len = len(seq)
    if current_len == target_len:
        return seq.astype(np.float32)
    elif current_len > target_len:
        indices = np.linspace(0, current_len - 1, target_len, dtype=int)
        return seq[indices].astype(np.float32)
    else:
        pad_width = ((0, target_len - current_len), (0, 0))
        return np.pad(seq, pad_width, mode="constant").astype(np.float32)


def load_data(
    data_dir=DATA_DIR,
    dataset_json=DATASET_JSON,
    label_json=LABEL_JSON,
    split="all",
    target_length=DEFAULT_SEQUENCE_LENGTH,
    max_classes=None,
):
    """
    โหลดข้อมูลท่าทางจากโฟลเดอร์ TSL-ONE-Pose
    Args:
        split: 'all', 'train', 'val', หรือ 'test'
        target_length: จำนวนเฟรมต่อ Sequence (default: 30)
        max_classes: กำหนดจำนวนคลาสสูงสุดที่ต้องการโหลด (None คือโหลดครบทั้ง 184 คลาส)
    Returns:
        X (np.ndarray): รูปร่าง (N, target_length, 150)
        y (np.ndarray): รูปร่าง (N,)
        id_to_label (dict): ข้อมูล Label mapping
    """
    id_to_label, gloss_to_id = get_label_mappings(label_json)

    with open(dataset_json, "r", encoding="utf-8") as f:
        dataset_info = json.load(f)

    X = []
    y = []
    skipped_files = 0

    valid_splits = {"train", "val", "test"} if split == "all" else {split}

    print(f"🔄 กำลังโหลดข้อมูลจาก '{data_dir}' (Split: {split})...")

    # กรองคลาสตามจำนวน max_classes
    items_to_process = dataset_info[:max_classes] if max_classes else dataset_info

    for item in items_to_process:
        gloss = item.get("gloss", "").lower().strip()
        if gloss not in gloss_to_id:
            continue

        label_id = gloss_to_id[gloss]

        for inst in item.get("instances", []):
            inst_split = inst.get("split")
            if inst_split not in valid_splits:
                continue

            video_id = inst.get("video_id")
            npy_path = os.path.join(data_dir, f"{video_id}.npy")

            if os.path.exists(npy_path):
                try:
                    raw_seq = np.load(npy_path)  # shape: (T, 150)
                    processed_seq = pad_or_sample_sequence(raw_seq, target_length)
                    X.append(processed_seq)
                    y.append(label_id)
                except Exception as e:
                    skipped_files += 1
            else:
                skipped_files += 1

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int32)

    print(f"✅ โหลดสำเร็จ! จำนวนตัวอย่าง: {len(X)} รายการ (ข้าม {skipped_files} ไฟล์)")
    if len(X) > 0:
        print(f"📊 รูปร่าง Features (X): {X.shape}, Labels (y): {y.shape}")

    return X, y, id_to_label


def load_all_splits(target_length=DEFAULT_SEQUENCE_LENGTH, max_classes=None):
    """โหลดข้อมูลแยกเป็น Train, Validation และ Test ให้พร้อมใช้เทรนโมเดล"""
    X_train, y_train, id_to_label = load_data(split="train", target_length=target_length, max_classes=max_classes)
    X_val, y_val, _ = load_data(split="val", target_length=target_length, max_classes=max_classes)
    X_test, y_test, _ = load_data(split="test", target_length=target_length, max_classes=max_classes)

    return (X_train, y_train), (X_val, y_val), (X_test, y_test), id_to_label


if __name__ == "__main__":
    # ทดสอบโหลดข้อมูล
    X, y, id_to_label = load_data(split="train", target_length=30)
    print("ตัวอย่าง Label แรก:", id_to_label.get(str(y[0])))