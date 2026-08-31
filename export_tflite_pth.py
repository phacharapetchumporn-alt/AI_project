import torch
import torch.nn as nn
import onnx
from onnx2tf import convert

# ==========================================
# 1. โครงสร้าง Class โมเดล (6 Classes)
# ==========================================
class SignLanguageModel(nn.Module):
    def __init__(self, input_size=126, hidden_size=128, num_layers=2, num_classes=6):
        super(SignLanguageModel, self).__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True
        )
        self.fc1 = nn.Linear(hidden_size * 2, 64)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(64, num_classes)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc1(out[:, -1, :])
        out = self.relu(out)
        out = self.fc2(out)
        return out

# ==========================================
# 2. โหลด Weight และ Export
# ==========================================
device = torch.device("cpu")
model = SignLanguageModel(num_classes=6)

model.load_state_dict(torch.load("action_model.pth", map_location=device))
model.eval()

# Dummy Input (Batch=1, Frames=30, Landmarks=126)
dummy_input = torch.randn(1, 30, 126)

# Step 1: Export เป็น ONNX (เปลี่ยน opset_version เป็น 18 ตามที่ PyTorch แนะนำ)
onnx_path = "action_model.onnx"
torch.onnx.export(
    model,
    dummy_input,
    onnx_path,
    input_names=["input"],
    output_names=["output"],
    opset_version=18  # 🟢 แก้เป็น 18 ป้องกันพอร์ทล้มเหลว
)
print("=== Step 1: Export ONNX สำเร็จ! ===")

# Step 2: แปลง ONNX เป็น TFLite (ปรับ Syntax ของ onnx2tf ใหม่)
convert(
    input_onnx_file_path=onnx_path,      # 🟢 ปรับชื่อ Parameter ตามเวอร์ชันใหม่
    output_folder_path="tflite_output",
    copy_onnx_input_output_names_to_tflite=True,
    non_verbose=True
)
print("=== Step 2: Export TFLite สำเร็จ! ไฟล์อยู่ในโฟลเดอร์ tflite_output ===")