import os
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import pickle

# =========================
# 1. ตั้งค่าไฮเปอร์พารามิเตอร์
# =========================
DATA_PATH = "sequences"
SEQUENCE_LENGTH = 30
INPUT_SIZE = 126  # (21 landmarks * 3 coords * 2 hands)
HIDDEN_SIZE = 128
NUM_LAYERS = 2
EPOCHS = 50
BATCH_SIZE = 16
LEARNING_RATE = 0.001

# =========================
# 2. โหลดข้อมูล .npy ทั้งหมด
# =========================
X, y = [], []
actions = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d))]

print(f"พบคำศัพท์ทั้งหมด {len(actions)} คำ: {actions}")

for label in actions:
    label_dir = os.path.join(DATA_PATH, label)
    for file_name in os.listdir(label_dir):
        if file_name.endswith('.npy'):
            res = np.load(os.path.join(label_dir, file_name))
            X.append(res)
            y.append(label)

X = np.array(X, dtype=np.float32)  # Shape: (Total_Samples, 30, 126)

# แปลง Label ตัวหนังสือเป็นตัวเลข
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(y)

# เซฟ LabelEncoder ไว้ใช้ตอน Real-time Inference
with open('label_encoder.pkl', 'wb') as f:
    pickle.dump(label_encoder, f)

# แบ่งข้อมูล Train / Test (80% / 20%)
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
)

# แปลงเป็น PyTorch Tensor Dataset
class SignLanguageDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X, dtype=torch.float32)
        self.y = torch.tensor(y, dtype=torch.long)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

train_dataset = SignLanguageDataset(X_train, y_train)
test_dataset = SignLanguageDataset(X_test, y_test)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

# =========================
# 3. สร้างโมเดล Bi-LSTM
# =========================
class BiLSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, num_classes):
        super(BiLSTMModel, self).__init__()
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True, 
            bidirectional=True,
            dropout=0.2 if num_layers > 1 else 0
        )
        self.fc1 = nn.Linear(hidden_size * 2, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, num_classes)
        
    def forward(self, x):
        # x shape: (batch_size, seq_len, input_size)
        out, _ = self.lstm(x)
        # เอา output จาก time-step สุดท้าย
        out = self.fc1(out[:, -1, :])
        out = self.relu(out)
        out = self.fc2(out)
        return out

num_classes = len(actions)
model = BiLSTMModel(INPUT_SIZE, HIDDEN_SIZE, NUM_LAYERS, num_classes)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

# =========================
# 4. ลูปเทรนโมเดล
# =========================
print("\n=== เริ่มการเทรนโมเดล ===")
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

for epoch in range(EPOCHS):
    model.train()
    train_loss = 0.0
    correct = 0
    total = 0
    
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item()
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()
        
    train_acc = 100 * correct / total
    
    # วัดผลกับ Test Set ทุกๆ 10 รอบ
    if (epoch + 1) % 10 == 0 or epoch == EPOCHS - 1:
        model.eval()
        test_correct = 0
        test_total = 0
        with torch.no_grad():
            for inputs, labels in test_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                test_total += labels.size(0)
                test_correct += (predicted == labels).sum().item()
                
        test_acc = 100 * test_correct / test_total
        print(f"Epoch [{epoch+1}/{EPOCHS}] - Loss: {train_loss/len(train_loader):.4f} | Train Acc: {train_acc:.2f}% | Test Acc: {test_acc:.2f}%")

# =========================
# 5. บันทึกน้ำหนักโมเดล (.pth)
# =========================
torch.save(model.state_dict(), 'action_model.pth')
print("\nบันทึกโมเดลสำเร็จในชื่อ 'action_model.pth'")