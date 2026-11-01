import os
import sys
import json
import shutil
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
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure UTF-8 printing on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

# =========================
# 1. ตั้งค่าไฮเปอร์พารามิเตอร์
# =========================
DATA_PATH       = os.path.join(BASE_DIR, "sequences")
SEQUENCE_LENGTH = 30
INPUT_SIZE      = 126       # 21 landmarks * 3 coords * 2 hands
HIDDEN_SIZE     = 192
NUM_LAYERS      = 3
EPOCHS          = 80
BATCH_SIZE      = 32
LEARNING_RATE   = 0.001
DROPOUT         = 0.3
PATIENCE        = 15        # Early Stopping patience
NOISE_STD       = 0.005     # Data Augmentation: gaussian noise std
WEIGHT_DECAY    = 1e-4      # L2 regularization

SAVE_PATH       = os.path.join(ROOT_DIR, "action_model.pth")
BEST_MODEL_PATH = os.path.join(ROOT_DIR, "action_model.pth")
SCALER_PATH     = os.path.join(ROOT_DIR, "scaler.pkl")
LABEL_ENC_PATH  = os.path.join(ROOT_DIR, "label_encoder.pkl")
REPORT_TXT_PATH = os.path.join(ROOT_DIR, "evaluation_report.txt")
REPORT_JSON_PATH= os.path.join(ROOT_DIR, "evaluation_report.json")
CONFUSION_PATH  = os.path.join(ROOT_DIR, "confusion_matrix.png")

# =========================
# 2. โหลดข้อมูล .npy ทั้งหมด
# =========================
print("=" * 65)
<<<<<<< HEAD
print("  TSL-51 Sign Language Model Training (PyTorch Bi-LSTM)")
=======
print("  TSL-51 Sign Language Model Training (PyTorch Transformer Encoder)")
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
print(f"  Data Path: {DATA_PATH}")
print(f"  Output Model: {SAVE_PATH}")
print("=" * 65)

X, y = [], []
if not os.path.exists(DATA_PATH):
    print(f"\n[ERROR] ไม่พบโฟลเดอร์ข้อมูล: {DATA_PATH}")
    print("  กรุณารัน convert_tsl51.py หรือจัดเตรียมข้อมูล .npy ก่อนเริ่มเทรน")
    sys.exit(1)

folders = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]

label_map = {}
for folder in folders:
    label = folder.strip()
    folder_path = os.path.join(DATA_PATH, folder)
    npy_files = [f for f in os.listdir(folder_path) if f.endswith('.npy')]
    label_map.setdefault(label, []).append((folder_path, npy_files))

print(f"\n[*] พบคำศัพท์ทั้งหมด {len(label_map)} คำ:")
for lbl, folders_data in sorted(label_map.items()):
    count = sum(len(files) for _, files in folders_data)
    print(f"  [{lbl}] → {count} samples")

for label, folders_data in label_map.items():
    for folder_path, npy_files in folders_data:
        for fname in npy_files:
            data = np.load(os.path.join(folder_path, fname))
            if data.shape == (SEQUENCE_LENGTH, INPUT_SIZE):
                X.append(data)
                y.append(label)
            else:
                print(f"  ⚠️  ข้าม {fname}: shape={data.shape} (คาดหวัง ({SEQUENCE_LENGTH}, {INPUT_SIZE}))")

if len(X) == 0:
    print("\n[ERROR] ไม่พบข้อมูล .npy ที่ถูกต้อง กรุณา convert_tsl51.py ก่อน")
    sys.exit(1)

X = np.array(X, dtype=np.float32)
print(f"\n[+] ข้อมูลทั้งหมด: {X.shape}  →  {X.shape[0]} samples")

# =========================
# 3. Normalize (Per-Feature Standardization)
# =========================
X_flat = X.reshape(-1, INPUT_SIZE)
mean = X_flat.mean(axis=0)
std  = X_flat.std(axis=0) + 1e-8   # กันหาร 0
X_norm = (X - mean) / std

# บันทึก scaler
with open(SCALER_PATH, 'wb') as f:
    pickle.dump({'mean': mean, 'std': std}, f)
print(f"✅ บันทึก scaler.pkl ที่: {SCALER_PATH}")

# =========================
# 4. Label Encoding & Split (Train 80% / Test 20%)
# =========================
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
num_classes = len(label_encoder.classes_)

with open(LABEL_ENC_PATH, 'wb') as f:
    pickle.dump(label_encoder, f)
print(f"✅ บันทึก label_encoder.pkl ({num_classes} classes) ที่: {LABEL_ENC_PATH}")

# Check minimum samples per class for stratification
counts = np.bincount(y_encoded)
can_stratify = bool(counts.min() >= 2)

# สัดส่วน Train 80% / Test 20%
X_train, X_test, y_train, y_test = train_test_split(
    X_norm, y_encoded, test_size=0.20, random_state=42,
    stratify=y_encoded if can_stratify else None
)
train_pct = (len(X_train) / len(X_norm)) * 100
test_pct = (len(X_test) / len(X_norm)) * 100
print(f"[*] Train set: {len(X_train)} samples ({train_pct:.1f}%) | Test set: {len(X_test)} samples ({test_pct:.1f}%)")

# =========================
# 5. Dataset & DataLoader
# =========================
class SignLanguageDataset(Dataset):
    def __init__(self, X, y, augment=False):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        self.augment = augment

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx]
        if self.augment:
            noise = torch.randn_like(x) * NOISE_STD
            x = x + noise
        return x, self.y[idx]


train_dataset = SignLanguageDataset(X_train, y_train, augment=True)
test_dataset  = SignLanguageDataset(X_test,  y_test,  augment=False)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
test_loader  = DataLoader(test_dataset,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

# =========================
<<<<<<< HEAD
# 6. Attention Layer
# =========================
class TemporalAttention(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.attn = nn.Linear(hidden_size, 1)

    def forward(self, lstm_out):
        scores = self.attn(lstm_out)
        weights = torch.softmax(scores, dim=1)
        context = (lstm_out * weights).sum(dim=1)
        return context, weights


# =========================
# 7. BiLSTM + Attention Model
# =========================
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
# 6. Positional Encoding & Transformer Encoder Model
# =========================
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=100, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-np.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x):
        # x: (batch_size, seq_len, d_model)
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
        # x: (batch, seq_len, input_size)
        h = self.input_proj(x)
        h = self.pos_encoder(h)
        h = self.transformer_encoder(h)
        h = self.norm(h)
        
        # Attention Pooling over sequence length
        weights = torch.softmax(self.attn_pool(h), dim=1) # (batch, seq_len, 1)
        pooled = (h * weights).sum(dim=1)                 # (batch, d_model)
        return self.classifier(pooled)
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"[*] Training Device: {'GPU (CUDA)' if torch.cuda.is_available() else 'CPU'}")

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

criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=5, min_lr=1e-5
)

# =========================
# 8. Training Loop
# =========================
best_val_loss = float('inf')
patience_count = 0
history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}

print(f"\n🚀 เริ่มต้นเทรนโมเดล {EPOCHS} Epochs...")
for epoch in range(EPOCHS):
    model.train()
    total_train_loss, correct_train, total_train = 0.0, 0, 0
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
        optimizer.step()

        total_train_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        correct_train += (preds == labels).sum().item()
        total_train += labels.size(0)

    avg_train_loss = total_train_loss / total_train
    train_acc = (correct_train / total_train) * 100

    model.eval()
    total_val_loss, correct_val, total_val = 0.0, 0, 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            total_val_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            correct_val += (preds == labels).sum().item()
            total_val += labels.size(0)

    avg_val_loss = total_val_loss / total_val
    val_acc = (correct_val / total_val) * 100
    scheduler.step(avg_val_loss)

    history["train_loss"].append(avg_train_loss)
    history["val_loss"].append(avg_val_loss)
    history["train_acc"].append(train_acc)
    history["val_acc"].append(val_acc)

    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        patience_count = 0
        torch.save(model.state_dict(), BEST_MODEL_PATH)
        best_marker = " ★ BEST"
    else:
        patience_count += 1
        best_marker = ""

    if (epoch + 1) % 5 == 0 or epoch == 0 or best_marker != "":
        lr = optimizer.param_groups[0]['lr']
        print(f"Epoch [{epoch+1:2d}/{EPOCHS}]  "
              f"Loss: {avg_train_loss:.4f}  Acc: {train_acc:.1f}%  |  "
              f"Val Loss: {avg_val_loss:.4f}  Val Acc: {val_acc:.1f}%  "
              f"LR: {lr:.6f}{best_marker}")

    if patience_count >= PATIENCE:
        print(f"\n⏹️ Early Stopping ที่ Epoch {epoch + 1} (val_loss ไม่ดีขึ้นมา {PATIENCE} รอบ)")
        break

# =========================
# 9. Evaluate Best Model & F1-Scores
# =========================
print(f"\n--- โหลดโมเดลดีที่สุด: {BEST_MODEL_PATH} ---")
model.load_state_dict(torch.load(BEST_MODEL_PATH, map_location=device))
model.eval()

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

# Metrics calculation
test_accuracy = accuracy_score(all_labels, all_preds)
macro_precision = precision_score(all_labels, all_preds, average='macro', zero_division=0)
macro_recall = recall_score(all_labels, all_preds, average='macro', zero_division=0)
macro_f1 = f1_score(all_labels, all_preds, average='macro', zero_division=0)
weighted_f1 = f1_score(all_labels, all_preds, average='weighted', zero_division=0)
micro_f1 = f1_score(all_labels, all_preds, average='micro', zero_division=0)

print("\n" + "=" * 65)
print("  EVALUATION METRICS SUMMARY (Test Set: 20%)")
print("=" * 65)
print(f"  Test Accuracy:    {test_accuracy * 100:.2f}%")
print(f"  Macro Precision:  {macro_precision:.4f}")
print(f"  Macro Recall:     {macro_recall:.4f}")
print(f"  Macro F1-Score:   {macro_f1:.4f}  (ค่าเฉลี่ย F1 เท่ากันทุกคลาส)")
print(f"  Weighted F1-Score:{weighted_f1:.4f}  (ค่าเฉลี่ย F1 ถ่วงน้ำหนักตามจำนวนข้อมูล)")
print(f"  Micro F1-Score:   {micro_f1:.4f}")
print("=" * 65)

report_text = classification_report(
    all_labels, all_preds,
    target_names=label_encoder.classes_,
    zero_division=0
)
print("\n📊 Classification Report (รายละเอียดรายคำศัพท์):")
print(report_text)

# Save evaluation report to text file
with open(REPORT_TXT_PATH, "w", encoding="utf-8") as f:
    f.write("TSL-51 Sign Language Model Evaluation Report\n")
    f.write("=" * 65 + "\n")
    f.write(f"Split: Train 80% ({len(X_train)} samples) / Test 20% ({len(X_test)} samples)\n")
    f.write(f"Total Samples: {len(X_norm)} | Classes: {num_classes}\n")
    f.write("-" * 65 + "\n")
    f.write(f"Test Accuracy:     {test_accuracy * 100:.2f}%\n")
    f.write(f"Macro Precision:   {macro_precision:.4f}\n")
    f.write(f"Macro Recall:      {macro_recall:.4f}\n")
    f.write(f"Macro F1-Score:    {macro_f1:.4f}\n")
    f.write(f"Weighted F1-Score: {weighted_f1:.4f}\n")
    f.write(f"Micro F1-Score:    {micro_f1:.4f}\n")
    f.write("=" * 65 + "\n\n")
    f.write("Detailed Classification Report:\n")
    f.write(report_text)
print(f"✅ บันทึกรายงานสรุปที่: {REPORT_TXT_PATH}")

# Save metrics to JSON format for easy programmatic access
report_dict = classification_report(
    all_labels, all_preds,
    target_names=label_encoder.classes_,
    output_dict=True,
    zero_division=0
)
metrics_json = {
    "split": {"train_ratio": 0.80, "test_ratio": 0.20, "train_samples": len(X_train), "test_samples": len(X_test)},
    "accuracy": float(test_accuracy),
    "macro_f1": float(macro_f1),
    "weighted_f1": float(weighted_f1),
    "micro_f1": float(micro_f1),
    "macro_precision": float(macro_precision),
    "macro_recall": float(macro_recall),
    "detailed_report": report_dict
}
with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(metrics_json, f, indent=2, ensure_ascii=False)
print(f"✅ บันทึก JSON Metrics ที่: {REPORT_JSON_PATH}")

# Save Confusion Matrix Heatmap if possible
try:
    cm = confusion_matrix(all_labels, all_preds)
    fig, ax = plt.subplots(figsize=(max(10, num_classes // 3), max(8, num_classes // 3)))
    sns.heatmap(cm, annot=False, cmap="Blues", fmt="d", cbar=True, ax=ax)
    ax.set_title(f"Confusion Matrix (Test Set 20% | Acc: {test_accuracy*100:.1f}%)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    plt.tight_layout()
    plt.savefig(CONFUSION_PATH, dpi=200)
    plt.close()
    print(f"✅ บันทึก Confusion Matrix ภาพที่: {CONFUSION_PATH}")
except Exception as e:
    print(f"  ⚠️ ข้ามการบันทึกรูปภาพ Confusion Matrix: {e}")

print(f"\n🎉 Training และ Evaluation เสร็จสิ้นสมบูรณ์!")
print(f"✅ บันทึกโมเดลไว้ที่: {BEST_MODEL_PATH}")
<<<<<<< HEAD
=======


>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
