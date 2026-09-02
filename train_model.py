import os
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import confusion_matrix, classification_report
import pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# =========================
# 1. ตั้งค่าไฮเปอร์พารามิเตอร์
# =========================
DATA_PATH       = "sequences"
SEQUENCE_LENGTH = 30
INPUT_SIZE      = 126       # 21 landmarks * 3 coords * 2 hands
HIDDEN_SIZE     = 192
NUM_LAYERS      = 3
EPOCHS          = 100
BATCH_SIZE      = 32
LEARNING_RATE   = 0.001
DROPOUT         = 0.3
PATIENCE        = 12        # Early Stopping patience
NOISE_STD       = 0.005     # Data Augmentation: gaussian noise std
WEIGHT_DECAY    = 1e-4      # L2 regularization

SAVE_PATH       = "action_model.pth"
BEST_MODEL_PATH = "action_model_best.pth"

# =========================
# 2. โหลดข้อมูล .npy ทั้งหมด
# =========================
print("=" * 55)
print("  Sign Language Model Training")
print("=" * 55)

X, y = [], []
folders = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]

# แยก Label จากชื่อโฟลเดอร์แบบ "label_YYYYMMDD_HHMMSS"
# รองรับทั้งชื่อที่มี timestamp และชื่อธรรมดา
def parse_label(folder_name: str) -> str:
    """ดึงชื่อ label จากชื่อโฟลเดอร์ เช่น '5_20260826_153744' → '5'"""
    parts = folder_name.split("_")
    # ถ้ามีส่วนท้ายเป็นตัวเลข 8 หลัก (date) ให้ตัดออก
    if len(parts) >= 3 and parts[-1].isdigit() and len(parts[-1]) == 6:
        label_parts = parts[:-2]  # ตัด timestamp ออก (date + time)
    else:
        label_parts = parts  # ใช้ทั้งชื่อ
    return "_".join(label_parts)

label_map = {}
for folder in folders:
    label = parse_label(folder)
    folder_path = os.path.join(DATA_PATH, folder)
    npy_files = [f for f in os.listdir(folder_path) if f.endswith('.npy')]
    label_map.setdefault(label, []).append((folder_path, npy_files))

print(f"\nพบคำศัพท์ทั้งหมด {len(label_map)} คำ:")
for lbl, folders_data in sorted(label_map.items()):
    count = sum(len(files) for _, files in folders_data)
    print(f"  [{lbl}] → {count} samples  (จาก {len(folders_data)} โฟลเดอร์)")

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
    print("\nERROR: ไม่พบข้อมูล .npy ที่ถูกต้อง กรุณา collect_data ก่อน")
    exit()

X = np.array(X, dtype=np.float32)
print(f"\nข้อมูลทั้งหมด: {X.shape}  →  {X.shape[0]} samples")

# =========================
# 3. Normalize (Per-Feature Standardization)
# =========================
# คำนวณ mean/std จากทุก frame และทุก sample
X_flat = X.reshape(-1, INPUT_SIZE)
mean = X_flat.mean(axis=0)
std  = X_flat.std(axis=0) + 1e-8   # กันหาร 0
X_norm = (X - mean) / std

# บันทึก scaler ไว้ใช้ใน realtime_predict
with open('scaler.pkl', 'wb') as f:
    pickle.dump({'mean': mean, 'std': std}, f)
print("✅ บันทึก scaler.pkl สำเร็จ")

# =========================
# 4. Label Encoding & Split
# =========================
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)
num_classes = len(label_encoder.classes_)

with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(label_encoder, f)
print(f"✅ บันทึก label_encoder.pkl ({num_classes} classes)")

X_train, X_test, y_train, y_test = train_test_split(
    X_norm, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)
print(f"Train: {len(X_train)}  |  Test: {len(X_test)}")

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
            # Gaussian Noise Augmentation
            noise = torch.randn_like(x) * NOISE_STD
            x = x + noise
        return x, self.y[idx]


train_dataset = SignLanguageDataset(X_train, y_train, augment=True)
test_dataset  = SignLanguageDataset(X_test,  y_test,  augment=False)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0, pin_memory=True)
test_loader  = DataLoader(test_dataset,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0, pin_memory=True)

# =========================
# 6. Attention Layer
# =========================
class TemporalAttention(nn.Module):
    """Self-attention ตาม time steps ของ LSTM output"""
    def __init__(self, hidden_size):
        super().__init__()
        self.attn = nn.Linear(hidden_size, 1)

    def forward(self, lstm_out):
        # lstm_out: (batch, seq_len, hidden)
        scores = self.attn(lstm_out)          # (batch, seq_len, 1)
        weights = torch.softmax(scores, dim=1) # normalize ตาม time axis
        context = (lstm_out * weights).sum(dim=1)  # weighted sum → (batch, hidden)
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
        # x: (batch, seq_len, input_size)
        lstm_out, _ = self.lstm(x)                    # (batch, seq, hidden*2)
        context, _  = self.attention(lstm_out)         # (batch, hidden*2)
        context     = self.norm(context)
        out         = self.dropout(context)
        out         = F.relu(self.bn1(self.fc1(out)))
        out         = self.dropout(out)
        out         = F.relu(self.fc2(out))
        out         = self.fc3(out)
        return out


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\n🖥️  Device: {device}")

model = BiLSTMAttentionModel(INPUT_SIZE, HIDDEN_SIZE, NUM_LAYERS, num_classes, DROPOUT)
model.to(device)

total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"📐 Model parameters: {total_params:,}")

criterion  = nn.CrossEntropyLoss(label_smoothing=0.05)
optimizer  = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
scheduler  = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=5, verbose=True
)

# =========================
# 8. Training Loop
# =========================
print(f"\n=== เริ่มการเทรนโมเดล (max {EPOCHS} epochs, early stop patience={PATIENCE}) ===\n")

history = {"train_loss": [], "train_acc": [], "val_loss": [], "val_acc": []}
best_val_loss  = float('inf')
patience_count = 0

for epoch in range(EPOCHS):
    # --- Train ---
    model.train()
    train_loss, correct, total = 0.0, 0, 0

    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        train_loss += loss.item()
        _, predicted = torch.max(outputs, 1)
        total   += labels.size(0)
        correct += (predicted == labels).sum().item()

    avg_train_loss = train_loss / len(train_loader)
    train_acc      = 100.0 * correct / total

    # --- Validation ---
    model.eval()
    val_loss, val_correct, val_total = 0.0, 0, 0

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss    = criterion(outputs, labels)
            val_loss += loss.item()
            _, predicted = torch.max(outputs, 1)
            val_total   += labels.size(0)
            val_correct += (predicted == labels).sum().item()

    avg_val_loss = val_loss / len(test_loader)
    val_acc      = 100.0 * val_correct / val_total

    scheduler.step(avg_val_loss)

    history["train_loss"].append(avg_train_loss)
    history["train_acc"].append(train_acc)
    history["val_loss"].append(avg_val_loss)
    history["val_acc"].append(val_acc)

    # Best Model Checkpoint
    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        patience_count = 0
        torch.save(model.state_dict(), BEST_MODEL_PATH)
        best_marker = " ★ BEST"
    else:
        patience_count += 1
        best_marker = ""

    if (epoch + 1) % 5 == 0 or epoch == 0:
        lr = optimizer.param_groups[0]['lr']
        print(f"Epoch [{epoch+1:3d}/{EPOCHS}]  "
              f"Loss: {avg_train_loss:.4f}  Acc: {train_acc:.1f}%  |  "
              f"Val Loss: {avg_val_loss:.4f}  Val Acc: {val_acc:.1f}%  "
              f"LR: {lr:.6f}{best_marker}")

    # Early Stopping
    if patience_count >= PATIENCE:
        print(f"\n⏹️  Early Stopping ที่ Epoch {epoch + 1} (val_loss ไม่ดีขึ้นมา {PATIENCE} รอบ)")
        break

# =========================
# 9. โหลด Best Model & Evaluate
# =========================
print(f"\n--- โหลด Best Model: {BEST_MODEL_PATH} ---")
model.load_state_dict(torch.load(BEST_MODEL_PATH, map_location=device))
model.eval()

all_preds, all_labels = [], []
with torch.no_grad():
    for inputs, labels in test_loader:
        inputs = inputs.to(device)
        outputs = model(inputs)
        _, predicted = torch.max(outputs, 1)
        all_preds.extend(predicted.cpu().numpy())
        all_labels.extend(labels.numpy())

print("\n📊 Classification Report:")
print(classification_report(all_labels, all_preds,
                             target_names=label_encoder.classes_,
                             zero_division=0))

# =========================
# 10. Confusion Matrix
# =========================
cm = confusion_matrix(all_labels, all_preds)
fig, ax = plt.subplots(figsize=(max(6, num_classes), max(5, num_classes - 1)))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_,
            ax=ax)
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("Confusion Matrix")
plt.tight_layout()
plt.savefig("confusion_matrix.png", dpi=120)
print("✅ บันทึก confusion_matrix.png สำเร็จ")

# =========================
# 11. Training Curves
# =========================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
epochs_ran = range(1, len(history["train_loss"]) + 1)

ax1.plot(epochs_ran, history["train_loss"], label="Train Loss")
ax1.plot(epochs_ran, history["val_loss"],   label="Val Loss")
ax1.set_title("Loss")
ax1.set_xlabel("Epoch")
ax1.legend()
ax1.grid(True, alpha=0.3)

ax2.plot(epochs_ran, history["train_acc"], label="Train Acc")
ax2.plot(epochs_ran, history["val_acc"],   label="Val Acc")
ax2.set_title("Accuracy (%)")
ax2.set_xlabel("Epoch")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("training_curves.png", dpi=120)
print("✅ บันทึก training_curves.png สำเร็จ")

# =========================
# 12. บันทึกโมเดลสุดท้าย (.pth)
# =========================
torch.save(model.state_dict(), SAVE_PATH)
print(f"\n✅ บันทึกโมเดลสุดท้ายที่: {SAVE_PATH}")
print(f"✅ บันทึก Best Model ที่: {BEST_MODEL_PATH}")
print(f"\n🎉 Training เสร็จสิ้น  |  Best Val Loss: {best_val_loss:.4f}")