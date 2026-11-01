"""
TSL-51 Converter: Converts Thai Sign Language Landmark CSVs to SignSubs (30, 126) .npy sequences.
Extracts 126 features:
- Left hand: 21 landmarks * 3 (x, y, z) = 63
- Right hand: 21 landmarks * 3 (x, y, z) = 63
"""

import os
import sys
import glob
import zipfile
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# Ensure UTF-8 stdout on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TSL51_DIR = os.environ.get("TSL51_DIR", r"C:\TSL-51")
OUT_SEQUENCES_DIR = os.path.join(BASE_DIR, "sequences")
SEQUENCE_LENGTH = 30
INPUT_SIZE = 126

# Build exact 126 column order matching realtime_predict.py
HAND_COLUMNS = []
for i in range(21):
    for axis in ['x', 'y', 'z']:
        HAND_COLUMNS.append(f"lh_{axis}{i}")
for i in range(21):
    for axis in ['x', 'y', 'z']:
        HAND_COLUMNS.append(f"rh_{axis}{i}")


def resample_sequence(data: np.ndarray, target_len=30) -> np.ndarray:
    """Resamples a (T, 126) sequence to (target_len, 126) via linear interpolation."""
    T, F = data.shape
    if T == target_len:
        return data.astype(np.float32)
    if T <= 1:
        if T == 1:
            return np.repeat(data, target_len, axis=0).astype(np.float32)
        return np.zeros((target_len, F), dtype=np.float32)
    
    x_old = np.linspace(0.0, 1.0, T)
    x_new = np.linspace(0.0, 1.0, target_len)
    f = interp1d(x_old, data, axis=0, kind='linear', fill_value='extrapolate')
    return f(x_new).astype(np.float32)


def process_csv_file(csv_path: str) -> np.ndarray:
    """Reads CSV, extracts 126 hand coordinates, fills NaNs with 0, and resamples to 30 frames."""
    try:
        df = pd.read_csv(csv_path, usecols=lambda c: c in HAND_COLUMNS)
        # Reorder to match HAND_COLUMNS exactly, fill missing cols with 0
        for col in HAND_COLUMNS:
            if col not in df.columns:
                df[col] = 0.0
        df = df[HAND_COLUMNS]
        df = df.fillna(0.0)
        data = df.to_numpy(dtype=np.float32)
        return resample_sequence(data, SEQUENCE_LENGTH)
    except Exception as e:
        print(f"  [!] Error processing {os.path.basename(csv_path)}: {e}")
        return None


def convert_dataset():
    print("=" * 65)
    print("  TSL-51 to SignSubs Dataset Converter")
    print(f"  Source: {TSL51_DIR}")
    print(f"  Target: {OUT_SEQUENCES_DIR}")
    print("=" * 65)

    os.makedirs(OUT_SEQUENCES_DIR, exist_ok=True)

    # 1. Load User Sign Metadata
    meta_path = os.path.join(TSL51_DIR, "metadata", "user_sign_metadata.csv")
    label_lookup = {}
    if os.path.exists(meta_path):
        meta_df = pd.read_csv(meta_path)
        for _, row in meta_df.iterrows():
            clean_word = str(row.get('sign_clean', '')).strip()
            if not clean_word or clean_word.lower() == 'nan':
                clean_word = 'null_act'
            # Map video_id and filename
            vid_id = str(row.get('video_id', '')).strip()
            fname = str(row.get('file_name', '')).replace('.mp4', '').strip()
            if vid_id:
                label_lookup[vid_id] = clean_word
            if fname:
                label_lookup[fname] = clean_word
        print(f"[*] Loaded metadata with {len(label_lookup)} entries from user_sign_metadata.csv")
    else:
        print("[!] Warning: user_sign_metadata.csv not found, will infer labels from filenames")

    # 2. Gather user_sign CSVs
    user_sign_dir = os.path.join(TSL51_DIR, "landmarks", "user_sign")
    csv_files = glob.glob(os.path.join(user_sign_dir, "*.csv"))
    print(f"[*] Found {len(csv_files)} landmark CSV files in user_sign")

    stats = {}
    converted_count = 0

    for idx, fpath in enumerate(csv_files):
        base_name = os.path.splitext(os.path.basename(fpath))[0]
        # Infer label
        if base_name in label_lookup:
            label = label_lookup[base_name]
        elif base_name.startswith("null_"):
            label = "null_act"
        else:
            # Fallback to prefix before _var
            parts = base_name.split("_var_")
            label = parts[0] if len(parts) > 1 else base_name.split("_")[0]

        seq = process_csv_file(fpath)
        if seq is None or seq.shape != (SEQUENCE_LENGTH, INPUT_SIZE):
            continue

        label_dir = os.path.join(OUT_SEQUENCES_DIR, label)
        os.makedirs(label_dir, exist_ok=True)

        out_fname = f"sample_{idx:04d}.npy"
        np.save(os.path.join(label_dir, out_fname), seq)
        stats[label] = stats.get(label, 0) + 1
        converted_count += 1

        if (idx + 1) % 100 == 0 or idx == len(csv_files) - 1:
            print(f"  Processed {idx + 1}/{len(csv_files)} samples...")

    print("-" * 65)
    print(f"[+] Total samples converted: {converted_count}")
    print(f"[+] Total classes created: {len(stats)}")
    print("Top classes sample count:")
    for lbl, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"    - {lbl}: {count} samples")
    print("=" * 65)


if __name__ == "__main__":
    convert_dataset()
