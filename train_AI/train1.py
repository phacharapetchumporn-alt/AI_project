import os
import sys
import types
import json
import numpy as np

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ความเข้ากันได้ระหว่าง TensorFlow กับ Protobuf บน Python 3.12
try:
    import google.protobuf.runtime_version
except ImportError:
    rv = types.ModuleType("google.protobuf.runtime_version")
    rv.Domain = type("Domain", (), {"PUBLIC": 1, "INTERNAL": 2})
    rv.ValidateProtobufRuntimeVersion = lambda *args, **kwargs: None
    sys.modules["google.protobuf.runtime_version"] = rv

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Masking
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from data_loader import load_all_splits, DEFAULT_SEQUENCE_LENGTH

# =========================
# 1. การตั้งค่าการเทรน (Hyperparameters)
# =========================
MODEL_OUTPUT_PATH = "tsl_lstm_model.h5"
SEQUENCE_LENGTH = DEFAULT_SEQUENCE_LENGTH  # 30 เฟรม
NUM_FEATURES = 150  # 75 จุด Landmark * 2 (x, y)
NUM_CLASSES = 10    # 10 คำศัพท์ตัวเลข (One ถึง Ten)
BATCH_SIZE = 32
EPOCHS = 40

print("=" * 50)
print("🚀 เริ่มต้นระบบเทรนโมเดลภาษามือไทย (TSL-ONE LSTM)")
print("=" * 50)

# =========================
# 2. โหลดข้อมูล Train, Validation, Test
# =========================
(X_train, y_train), (X_val, y_val), (X_test, y_test), id_to_label = load_all_splits(
    target_length=SEQUENCE_LENGTH
)
NUM_CLASSES = len(id_to_label)  # จำนวนคำศัพท์ (10 คำ)

print(f"\n📦 สรุปจำนวนข้อมูล:")
print(f"   - ชุดฝึกสอน (Train): {len(X_train)} ตัวอย่าง")
print(f"   - ชุดตรวจสอบ (Val):   {len(X_val)} ตัวอย่าง")
print(f"   - ชุดทดสอบ (Test):    {len(X_test)} ตัวอย่าง")
print(f"   - จำนวนคำศัพท์:      {NUM_CLASSES} คำ\n")

# =========================
# 3. สร้างโครงสร้างโมเดล LSTM
# =========================
def create_tsl_model(seq_len=SEQUENCE_LENGTH, num_feat=NUM_FEATURES, num_cls=NUM_CLASSES):
    model = Sequential([
        # ข้ามเฟรมที่เป็น 0 (Zero Padding)
        Masking(mask_value=0.0, input_shape=(seq_len, num_feat)),
        
        # LSTM Layer 1
        LSTM(64, return_sequences=True),
        Dropout(0.3),
        
        # LSTM Layer 2
        LSTM(128, return_sequences=False),
        Dropout(0.3),
        
        # Dense Classification Layers
        Dense(64, activation="relu"),
        Dropout(0.2),
        Dense(num_cls, activation="softmax"),
    ])
    
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model

model = create_tsl_model()
model.summary()

# =========================
# 4. ตั้งค่า Callbacks & เริ่มเทรน
# =========================
callbacks = [
    EarlyStopping(
        monitor="val_loss",
        patience=10,
        restore_best_weights=True,
        verbose=1,
    ),
    ModelCheckpoint(
        MODEL_OUTPUT_PATH,
        monitor="val_accuracy",
        save_best_only=True,
        verbose=1,
    ),
    ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.5,
        patience=4,
        verbose=1,
    ),
]

print("\n🏋️ เริ่มต้นการเทรนโมเดล...")
history = model.fit(
    X_train,
    y_train,
    validation_data=(X_val, y_val),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=callbacks,
)

# =========================
# 5. ประเมินผลกับชุดข้อมูลทดสอบ (Test Set)
# =========================
print("\n📝 ประเมินผลโมเดลบนชุดข้อมูลทดสอบ (Test Set)...")
test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
print(f"🎯 Test Accuracy: {test_acc * 100:.2f}% | Test Loss: {test_loss:.4f}")

# บันทึกโมเดลเวอร์ชันสุดท้าย
model.save(MODEL_OUTPUT_PATH)
print(f"\n🎉 บันทึกโมเดลเรียบร้อยที่: {MODEL_OUTPUT_PATH}")
print(f"💡 สามารถรัน 'python realtime_translate.py' เพื่อเริ่มใช้งานกล้องแปลภาษามือได้ทันที!")