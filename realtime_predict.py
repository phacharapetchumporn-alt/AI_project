import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import mediapipe as mp
import pickle
import time
import os
from collections import deque
from PIL import Image, ImageDraw, ImageFont

# =========================
# Thai Text Renderer
# =========================
_thai_font_cache = {}

def get_thai_font(size: int):
    if size not in _thai_font_cache:
        for font_name in ["tahoma.ttf", "THSarabunNew.ttf", "arial.ttf"]:
            try:
                _thai_font_cache[size] = ImageFont.truetype(font_name, size)
                break
            except OSError:
                continue
        else:
            _thai_font_cache[size] = ImageFont.load_default()
    return _thai_font_cache[size]


def draw_thai_text(img, text, position, font_size=30, color=(255, 255, 255)):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    font = get_thai_font(font_size)
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# =========================
# Attention Layer (ต้องตรงกับ train_model.py)
# =========================
class TemporalAttention(nn.Module):
    def __init__(self, hidden_size):
        super().__init__()
        self.attn = nn.Linear(hidden_size, 1)

    def forward(self, lstm_out):
        scores  = self.attn(lstm_out)
        weights = torch.softmax(scores, dim=1)
        context = (lstm_out * weights).sum(dim=1)
        return context, weights


class BiLSTMAttentionModel(nn.Module):
    def __init__(self, input_size=126, hidden_size=192, num_layers=3, num_classes=10, dropout=0.3):
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
        out         = self.fc3(out)
        return out


# =========================
# 1. โหลด Label Encoder, Scaler และ Model
# =========================
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

actions     = label_encoder.classes_
num_classes = len(actions)

# โหลด Scaler (ถ้ามี)
scaler = None
if os.path.exists('scaler.pkl'):
    with open('scaler.pkl', 'rb') as f:
        scaler = pickle.load(f)
    print("✅ โหลด scaler.pkl สำเร็จ")
else:
    print("⚠️  ไม่พบ scaler.pkl (จะใช้ข้อมูลดิบ)")

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# โหลด Best Model ก่อน, ถ้าไม่มีค่อยใช้ปกติ
model_path = 'action_model_best.pth' if os.path.exists('action_model_best.pth') else 'action_model.pth'
print(f"📦 โหลดโมเดล: {model_path}")

model = BiLSTMAttentionModel(num_classes=num_classes)
model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
model.to(device)
model.eval()

print(f"✅ พร้อม Predict {num_classes} classes: {list(actions)}")
print("กด [C] = ล้างประโยค | [Backspace] = ลบคำล่าสุด | [Q] = ออก\n")

# =========================
# 2. MediaPipe Setup
# =========================
mp_holistic    = mp.solutions.holistic
mp_drawing     = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Pose arm connections เส้นแขน
_POSE_ARM_CONNS = [
    (mp_holistic.PoseLandmark.LEFT_SHOULDER,  mp_holistic.PoseLandmark.LEFT_ELBOW),
    (mp_holistic.PoseLandmark.LEFT_ELBOW,     mp_holistic.PoseLandmark.LEFT_WRIST),
    (mp_holistic.PoseLandmark.RIGHT_SHOULDER, mp_holistic.PoseLandmark.RIGHT_ELBOW),
    (mp_holistic.PoseLandmark.RIGHT_ELBOW,    mp_holistic.PoseLandmark.RIGHT_WRIST),
    (mp_holistic.PoseLandmark.LEFT_SHOULDER,  mp_holistic.PoseLandmark.RIGHT_SHOULDER),
]

holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)


def draw_arm_skeleton(frame, pose_landmarks):
    """วาดเส้น skeleton แขนทั้งสองข้าง (ไหล่ → ข้อศอก → ข้อมือ)"""
    if pose_landmarks is None:
        return
    h, w = frame.shape[:2]
    lm = pose_landmarks.landmark

    for start_idx, end_idx in _POSE_ARM_CONNS:
        p1, p2 = lm[start_idx], lm[end_idx]
        if p1.visibility < 0.4 or p2.visibility < 0.4:
            continue
        x1, y1 = int(p1.x * w), int(p1.y * h)
        x2, y2 = int(p2.x * w), int(p2.y * h)
        cv2.line(frame, (x1, y1), (x2, y2), (0, 210, 180), 3, cv2.LINE_AA)

    arm_joints = [
        mp_holistic.PoseLandmark.LEFT_SHOULDER,
        mp_holistic.PoseLandmark.LEFT_ELBOW,
        mp_holistic.PoseLandmark.LEFT_WRIST,
        mp_holistic.PoseLandmark.RIGHT_SHOULDER,
        mp_holistic.PoseLandmark.RIGHT_ELBOW,
        mp_holistic.PoseLandmark.RIGHT_WRIST,
    ]
    for idx in arm_joints:
        p = lm[idx]
        if p.visibility < 0.4:
            continue
        x, y = int(p.x * w), int(p.y * h)
        cv2.circle(frame, (x, y), 7, (0, 230, 200), -1, cv2.LINE_AA)
        cv2.circle(frame, (x, y), 7, (255, 255, 255), 1, cv2.LINE_AA)

# =========================
# 3. State Variables
# =========================
SEQUENCE_LEN      = 30
THRESHOLD         = 0.88      # ความมั่นใจขั้นต่ำ
VOTE_WINDOW       = 15        # หน้าต่าง Voting (เฟรม)
CONFIRM_VOTES     = 10        # ต้องชนะโหวตกี่เฟรมถึงยืนยัน

sequence          = deque(maxlen=SEQUENCE_LEN)
vote_buffer       = deque(maxlen=VOTE_WINDOW)
sentence          = []
last_confirmed    = None
no_hand_frames    = 0
NO_HAND_RESET     = 20        # เฟรมที่ไม่มีมือก่อน reset vote_buffer

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

prev_time = time.time()
current_pred_text = ""
current_confidence = 0.0

# =========================
# 4. UI Helpers
# =========================
def draw_confidence_bar(frame, x, y, w, h, confidence, label):
    """วาด Confidence Bar"""
    bg_color   = (40, 40, 40)
    fill_color = (0, int(200 * confidence), int(100 * (1 - confidence)))

    cv2.rectangle(frame, (x, y), (x + w, y + h), bg_color, -1)
    cv2.rectangle(frame, (x, y), (x + int(w * confidence), y + h), fill_color, -1)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (100, 100, 100), 1)

    text = f"{label}: {confidence*100:.1f}%"
    cv2.putText(frame, text, (x + 4, y + h - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)


def draw_top_predictions(frame, probabilities, actions, top_k=3):
    """วาด Top-K predictions ด้านขวา"""
    h, w = frame.shape[:2]
    top_k = min(top_k, len(probabilities))
    top_indices = np.argsort(probabilities)[::-1][:top_k]
    bar_h = 20
    bar_w = 200
    x_start = w - bar_w - 10

    cv2.putText(frame, "Top Predictions:", (x_start, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    for rank, idx in enumerate(top_indices):
        conf  = probabilities[idx]
        label = actions[idx]
        y_pos = 80 + rank * (bar_h + 8)
        draw_confidence_bar(frame, x_start, y_pos, bar_w, bar_h, conf, label)


def draw_hud(frame, fps, has_hand, sentence, current_label, confidence, vote_count):
    """วาด HUD หลัก"""
    h, w = frame.shape[:2]

    # --- แถบบน ---
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 58), (15, 15, 25), -1)
    cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

    # FPS
    fps_color = (0, 200, 100) if fps >= 25 else (0, 140, 255)
    cv2.putText(frame, f"FPS: {fps:.0f}", (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, fps_color, 2)

    # Hand indicator
    if has_hand:
        cv2.circle(frame, (110, 15), 8, (0, 220, 80), -1)
        cv2.putText(frame, "HAND", (122, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 80), 1)
    else:
        cv2.circle(frame, (110, 15), 8, (0, 80, 200), -1)
        cv2.putText(frame, "NO HAND", (122, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 200), 1)

    # Vote progress
    if vote_count > 0:
        vote_ratio = min(vote_count / CONFIRM_VOTES, 1.0)
        bar_color  = (0, 220, 255) if vote_ratio < 1.0 else (0, 255, 80)
        cv2.rectangle(frame, (10, 36), (10 + int(200 * vote_ratio), 50), bar_color, -1)
        cv2.rectangle(frame, (10, 36), (210, 50), (80, 80, 80), 1)
        cv2.putText(frame, f"Confirming: {vote_count}/{CONFIRM_VOTES}",
                    (215, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    # Current prediction (ถ้ามี)
    if current_label and confidence >= THRESHOLD:
        pred_str = f"{current_label}  ({confidence*100:.0f}%)"
        cv2.putText(frame, pred_str, (w // 2 - 80, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 220, 255), 2)

    # --- แถบล่าง (Sentence) ---
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, h - 68), (w, h), (15, 15, 25), -1)
    cv2.addWeighted(overlay2, 0.85, frame, 0.15, 0, frame)

    cv2.putText(frame, "[C] Clear  [Backspace] Delete  [Q] Quit",
                (10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 100, 100), 1)

    return frame


# =========================
# 5. Main Loop
# =========================
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    curr_time = time.time()
    fps = 1.0 / max(curr_time - prev_time, 1e-6)
    prev_time = curr_time

    display_frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False
    results = holistic.process(rgb)
    rgb.flags.writeable = True

    left_hand  = [0.0] * 63
    right_hand = [0.0] * 63
    has_hand   = False

    # วาด arm skeleton ก่อน (เพื่อให้อยู่ใต้ hand landmarks)
    draw_arm_skeleton(display_frame, results.pose_landmarks)

    # วาด + ดึง Hand landmarks
    if results.left_hand_landmarks:
        has_hand = True
        mp_drawing.draw_landmarks(
            display_frame, results.left_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style()
        )
        lm_list = []
        for lm in results.left_hand_landmarks.landmark:
            lm_list.extend([lm.x, lm.y, lm.z])
        left_hand = lm_list

    if results.right_hand_landmarks:
        has_hand = True
        mp_drawing.draw_landmarks(
            display_frame, results.right_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style()
        )
        lm_list = []
        for lm in results.right_hand_landmarks.landmark:
            lm_list.extend([lm.x, lm.y, lm.z])
        right_hand = lm_list

    keypoints = np.array(left_hand + right_hand, dtype=np.float32)

    # Normalize ถ้ามี scaler
    if scaler is not None:
        keypoints = (keypoints - scaler['mean']) / scaler['std']

    sequence.append(keypoints.tolist())

    # ถ้าไม่มีมือนานพอ ให้ reset vote buffer
    if not has_hand:
        no_hand_frames += 1
        if no_hand_frames >= NO_HAND_RESET:
            vote_buffer.clear()
            current_pred_text  = ""
            current_confidence = 0.0
    else:
        no_hand_frames = 0

    current_label = ""
    probabilities = None
    vote_count    = 0

    # ทำนายเมื่อ sequence เต็ม 30 เฟรม และมีมือ
    if len(sequence) == SEQUENCE_LEN and has_hand:
        input_data = torch.tensor([list(sequence)], dtype=torch.float32).to(device)

        with torch.no_grad():
            output        = model(input_data)
            probabilities = torch.softmax(output, dim=1).cpu().numpy()[0]
            best_idx      = int(np.argmax(probabilities))
            confidence    = float(probabilities[best_idx])
            current_label = actions[best_idx]
            current_confidence = confidence

        if confidence >= THRESHOLD:
            vote_buffer.append(best_idx)

        # Weighted Voting — นับจำนวนครั้งที่ชนะในหน้าต่าง
        if len(vote_buffer) > 0:
            vote_count = sum(1 for v in vote_buffer if v == best_idx)

            if vote_count >= CONFIRM_VOTES:
                if current_label != last_confirmed:
                    sentence.append(current_label)
                    last_confirmed = current_label
                    vote_buffer.clear()
                    print(f"✅ Confirmed: [{current_label}]  (conf={confidence*100:.1f}%)")

        # Draw top predictions
        if probabilities is not None:
            draw_top_predictions(display_frame, probabilities, actions, top_k=3)

    # Sentence cap
    if len(sentence) > 7:
        sentence = sentence[-7:]

    # วาด HUD
    display_frame = draw_hud(
        display_frame, fps, has_hand, sentence,
        current_label, current_confidence, vote_count
    )

    # วาด Sentence
    full_sentence = " ".join(sentence)
    display_frame = draw_thai_text(
        display_frame, full_sentence,
        (10, display_frame.shape[0] - 28),
        font_size=30, color=(255, 220, 80)
    )

    cv2.imshow("Sign Language Real-time Translation", display_frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):
        sentence.clear()
        vote_buffer.clear()
        last_confirmed = None
        print("🗑️  ล้างประโยคแล้ว")
    elif key == 8:  # Backspace
        if sentence:
            removed = sentence.pop()
            last_confirmed = sentence[-1] if sentence else None
            print(f"⬅️  ลบ: [{removed}]")

cap.release()
cv2.destroyAllWindows()
print("\nปิดโปรแกรมเรียบร้อย")