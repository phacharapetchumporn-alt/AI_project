"""
Standalone Model Evaluator & F1-Score Calculator for TSL-51 Sign Language Model.
Evaluates PyTorch Bi-LSTM with Attention model on test dataset (Default 80/20 split).
Outputs Macro F1, Weighted F1, Per-Class F1, Confusion Matrix, and JSON/Text reports.
"""

import os
import sys
import json
import argparse
import pickle
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    f1_score,
    accuracy_score,
    precision_score,
    recall_score
)
import matplotlib
matplotlib.use('Agg')
<<<<<<< HEAD
import matplotlib.pyplot as plt
import seaborn as sns
=======
import warnings
warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

SEQUENCE_LENGTH = 30
INPUT_SIZE      = 126
HIDDEN_SIZE     = 192
NUM_LAYERS      = 3
DROPOUT         = 0.3


<<<<<<< HEAD
class TemporalAttention(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.attn = nn.Linear(hidden_size, 1)

    def forward(self, lstm_out):
        scores = self.attn(lstm_out)
        weights = torch.softmax(scores, dim=1)
        context = (lstm_out * weights).sum(dim=1)
        return context, weights


class BiLSTMAttentionModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size, hidden_size, num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.attention = TemporalAttention(hidden_size * 2)
        self.norm      = nn.LayerNorm(hidden_size * 2)
        self.dropout   = nn.Dropout(dropout)
        self.fc1       = nn.Linear(hidden_size * 2, 128)
        self.bn1       = nn.BatchNorm1d(128)
        self.fc2       = nn.Linear(128, 64)
        self.fc3       = nn.Linear(64, num_classes)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        context, _  = self.attention(lstm_out)
        context     = self.norm(context)
        out         = self.dropout(context)
        out         = F.relu(self.bn1(self.fc1(out)))
        out         = self.dropout(out)
        out         = F.relu(self.fc2(out))
        return self.fc3(out)
=======
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=100, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TransformerEncoderModel(nn.Module):
    def __init__(self, input_size=126, d_model=128, nhead=4, num_layers=3, dim_feedforward=256, num_classes=58, dropout=0.2):
        super().__init__()
        self.input_proj = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_len=SEQUENCE_LENGTH, dropout=dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
            activation='gelu'
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.norm = nn.LayerNorm(d_model)
        self.attn_pool = nn.Linear(d_model, 1)
        self.classifier = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.BatchNorm1d(128),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        h = self.input_proj(x)
        h = self.pos_encoder(h)
        h = self.transformer_encoder(h)
        h = self.norm(h)
        weights = torch.softmax(self.attn_pool(h), dim=1)
        pooled = (h * weights).sum(dim=1)
        return self.classifier(pooled)
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9


class EvalDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def evaluate(data_dir, model_path, scaler_path, label_enc_path, output_dir, test_size=0.20, random_state=42):
    print("=" * 70)
    print("  TSL-51 Sign Language Model - F1-Score & Accuracy Evaluation")
    print(f"  Model Path:       {model_path}")
    print(f"  Scaler Path:      {scaler_path}")
    print(f"  LabelEnc Path:    {label_enc_path}")
    print(f"  Data Directory:   {data_dir}")
    print(f"  Test Ratio:       {test_size * 100:.1f}% (Train {(1 - test_size) * 100:.1f}%)")
    print("=" * 70)

    # 1. Load Preprocessing Artifacts
    if not os.path.exists(label_enc_path):
        print(f"[ERROR] ไม่พบไฟล์ Label Encoder: {label_enc_path}")
        sys.exit(1)
    with open(label_enc_path, 'rb') as f:
        label_encoder = pickle.load(f)
    classes = label_encoder.classes_
    num_classes = len(classes)
    print(f"[+] โหลด Label Encoder สำเร็จ: {num_classes} คลาสคำศัพท์")

    if not os.path.exists(scaler_path):
        print(f"[ERROR] ไม่พบไฟล์ Scaler: {scaler_path}")
        sys.exit(1)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    mean, std = scaler['mean'], scaler['std']
    print("[+] โหลด Scaler สำเร็จ (Normalization Mean/Std)")

    # 2. Check Data
    if not os.path.exists(data_dir):
        print(f"\n[ERROR] ไม่พบโฟลเดอร์ Dataset: {data_dir}")
        print("  กรุณาระบุตำแหน่งโฟลเดอร์ sequences ผ่านอาร์กิวเมนต์ --data-dir <path>")
        sys.exit(1)

    folders = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    X, y = [], []
    for folder in folders:
        label = folder.strip()
        folder_path = os.path.join(data_dir, folder)
        npy_files = [f for f in os.listdir(folder_path) if f.endswith('.npy')]
        for fname in npy_files:
            data = np.load(os.path.join(folder_path, fname))
            if data.shape == (SEQUENCE_LENGTH, INPUT_SIZE):
                X.append(data)
                y.append(label)

    if len(X) == 0:
        print(f"[ERROR] ไม่พบไฟล์ .npy ที่มี shape ({SEQUENCE_LENGTH}, {INPUT_SIZE}) ใน {data_dir}")
        sys.exit(1)

    X = np.array(X, dtype=np.float32)
    print(f"[+] โหลดข้อมูลสำเร็จ: ทั้งหมด {len(X)} ตัวอย่าง จาก {len(folders)} โฟลเดอร์")

    # 3. Normalize & Encode
    X_norm = (X - mean) / std
    y_encoded = label_encoder.transform(y)

    counts = np.bincount(y_encoded)
    can_stratify = bool(counts.min() >= 2)

    _, X_test, _, y_test = train_test_split(
        X_norm, y_encoded, test_size=test_size, random_state=random_state,
        stratify=y_encoded if can_stratify else None
    )
    print(f"[*] ชุดทดสอบ (Test Set {test_size*100:.0f}%): {len(X_test)} ตัวอย่าง")

    # 4. Load Model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[*] Inference Device: {'GPU (CUDA)' if torch.cuda.is_available() else 'CPU'}")

<<<<<<< HEAD
    model = BiLSTMAttentionModel(
        input_size=INPUT_SIZE,
        hidden_size=HIDDEN_SIZE,
        num_layers=NUM_LAYERS,
=======
    model = TransformerEncoderModel(
        input_size=INPUT_SIZE,
        d_model=128,
        nhead=4,
        num_layers=3,
        dim_feedforward=256,
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        num_classes=num_classes,
        dropout=DROPOUT
    ).to(device)

    if not os.path.exists(model_path):
        print(f"[ERROR] ไม่พบไฟล์โมเดล: {model_path}")
        sys.exit(1)

    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print("[+] โหลด Weights โมเดลสำเร็จ")

    # 5. Predict on Test Set
    test_loader = DataLoader(EvalDataset(X_test, y_test), batch_size=32, shuffle=False)
    all_preds, all_labels = [], []
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.numpy())

    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)

    # 6. Compute Metrics
    acc = accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
    weighted_f1 = f1_score(all_labels, all_preds, average='weighted', zero_division=0)
    micro_f1 = f1_score(all_labels, all_preds, average='micro', zero_division=0)
    macro_p = precision_score(all_labels, all_preds, average='macro', zero_division=0)
    macro_r = recall_score(all_labels, all_preds, average='macro', zero_division=0)

    print("\n" + "=" * 70)
    print("  ผลลัพธ์การประเมิน (EVALUATION METRICS RESULT)")
    print("=" * 70)
    print(f"  Accuracy:         {acc * 100:.2f}%")
    print(f"  Macro F1-Score:   {macro_f1:.4f}  (เกณฑ์เฉลี่ยทุกคลาสเท่าเทียม)")
    print(f"  Weighted F1-Score:{weighted_f1:.4f}  (ถ่วงน้ำหนักตามจำนวนข้อมูลจริง)")
    print(f"  Micro F1-Score:   {micro_f1:.4f}")
    print(f"  Macro Precision:  {macro_p:.4f}")
    print(f"  Macro Recall:     {macro_r:.4f}")
    print("=" * 70)

    report_str = classification_report(all_labels, all_preds, target_names=classes, zero_division=0)
    print("\n📊 Classification Report (รายคลาสคำศัพท์):")
    print(report_str)

    # 7. Export Outputs
    os.makedirs(output_dir, exist_ok=True)
    txt_path = os.path.join(output_dir, "evaluation_report.txt")
    json_path = os.path.join(output_dir, "evaluation_report.json")
    cm_path = os.path.join(output_dir, "confusion_matrix.png")

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("TSL-51 Sign Language Model Evaluation Report\n")
        f.write("=" * 70 + "\n")
        f.write(f"Split: Test {test_size*100:.1f}% ({len(X_test)} samples) / Train {(1-test_size)*100:.1f}%\n")
        f.write(f"Accuracy:         {acc * 100:.2f}%\n")
        f.write(f"Macro F1-Score:   {macro_f1:.4f}\n")
        f.write(f"Weighted F1-Score:{weighted_f1:.4f}\n")
        f.write(f"Micro F1-Score:   {micro_f1:.4f}\n")
        f.write(f"Macro Precision:  {macro_p:.4f}\n")
        f.write(f"Macro Recall:     {macro_r:.4f}\n")
        f.write("=" * 70 + "\n\n")
        f.write("Detailed Classification Report:\n")
        f.write(report_str)
    print(f"\n✅ บันทึกรายงาน Text: {txt_path}")

    report_dict = classification_report(all_labels, all_preds, target_names=classes, output_dict=True, zero_division=0)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "test_size": test_size,
            "test_samples": len(X_test),
            "accuracy": float(acc),
            "macro_f1": float(macro_f1),
            "weighted_f1": float(weighted_f1),
            "micro_f1": float(micro_f1),
            "macro_precision": float(macro_p),
            "macro_recall": float(macro_r),
            "detailed": report_dict
        }, f, indent=2, ensure_ascii=False)
    print(f"✅ บันทึกรายงาน JSON: {json_path}")

    try:
        cm = confusion_matrix(all_labels, all_preds)
        fig, ax = plt.subplots(figsize=(max(10, num_classes // 3), max(8, num_classes // 3)))
<<<<<<< HEAD
        sns.heatmap(cm, annot=False, cmap="Blues", fmt="d", cbar=True, ax=ax)
=======
        if HAS_SEABORN:
            sns.heatmap(cm, annot=False, cmap="Blues", fmt="d", cbar=True, ax=ax)
        else:
            cax = ax.matshow(cm, cmap="Blues")
            fig.colorbar(cax)
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        ax.set_title(f"Confusion Matrix (Test Acc: {acc*100:.2f}% | Macro F1: {macro_f1:.3f})")
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        plt.tight_layout()
        plt.savefig(cm_path, dpi=200)
        plt.close()
        print(f"✅ บันทึกภาพ Confusion Matrix: {cm_path}")
    except Exception as e:
        print(f"⚠️ ข้ามการวาด Confusion Matrix: {e}")

    print("\n🎉 การประเมินผลเสร็จสิ้นเรียบร้อย!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate TSL-51 Model and Calculate F1-Score")
    parser.add_argument("--data-dir", default=os.path.join(BASE_DIR, "sequences"), help="Path to sequences directory")
    parser.add_argument("--model-path", default=os.path.join(ROOT_DIR, "action_model.pth"), help="Path to action_model.pth")
    parser.add_argument("--scaler-path", default=os.path.join(ROOT_DIR, "scaler.pkl"), help="Path to scaler.pkl")
    parser.add_argument("--label-enc-path", default=os.path.join(ROOT_DIR, "label_encoder.pkl"), help="Path to label_encoder.pkl")
    parser.add_argument("--output-dir", default=ROOT_DIR, help="Directory to save report files")
    parser.add_argument("--test-size", type=float, default=0.20, help="Test set ratio (default: 0.20 for 80/20)")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed for train/test split")

    args = parser.parse_args()
    evaluate(
        data_dir=args.data_dir,
        model_path=args.model_path,
        scaler_path=args.scaler_path,
        label_enc_path=args.label_enc_path,
        output_dir=args.output_dir,
        test_size=args.test_size,
        random_state=args.random_state
    )
<<<<<<< HEAD
=======



>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
