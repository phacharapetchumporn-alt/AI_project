import cv2
import numpy as np
import torch
import torch.nn as nn
import mediapipe as mp
import pickle
from PIL import Image, ImageDraw, ImageFont

# =========================
# ฟังก์ชันสำหรับวาดข้อความภาษาไทย
# =========================
def draw_thai_text(img, text, position, font_size=30, color=(0, 255, 0)):
    img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img_pil)
    
    try:
        font = ImageFont.truetype("tahoma.ttf", font_size)
    except:
        font = ImageFont.load_default()
        
    draw.text(position, text, font=font, fill=color)
    return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)


# =========================
# 1. โหลด Label Encoder & ตั้งค่าโมเดล
# =========================
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)

actions = label_encoder.classes_
num_classes = len(actions)

class BiLSTMModel(nn.Module):
    def __init__(self, input_size=126, hidden_size=128, num_layers=2, num_classes=num_classes):
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
        out, _ = self.lstm(x)
        out = self.fc1(out[:, -1, :])
        out = self.relu(out)
        out = self.fc2(out)
        return out

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = BiLSTMModel(num_classes=num_classes)
model.load_state_dict(torch.load('action_model.pth', map_location=device))
model.to(device)
model.eval()

# =========================
# 2. ตั้งค่า MediaPipe & Variables
# =========================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

sequence = []
sentence = []
predictions = []
threshold = 0.90  # 🟢 [จุดแก้ที่ 1] ปรับความมั่นใจขั้นต่ำขึ้นเป็น 90%

cap = cv2.VideoCapture(0)

print("=== เริ่มการทำนายเรียลไทม์ ===")
print("กด C = ล้างประโยค | กด Backspace = ลบคำล่าสุด | กด Q = ออก")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    display_frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    left_hand = [0.0] * 63
    right_hand = [0.0] * 63

    if results.multi_hand_landmarks and results.multi_handedness:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            mp_drawing.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            landmarks = []
            for lm in hand_landmarks.landmark:
                landmarks.extend([lm.x, lm.y, lm.z])

            hand_label = results.multi_handedness[i].classification[0].label
            if hand_label == "Left":
                left_hand = landmarks
            elif hand_label == "Right":
                right_hand = landmarks

    keypoints = left_hand + right_hand
    sequence.append(keypoints)
    sequence = sequence[-30:]

    # วาดแถบพื้นหลังประโยคด้านล่าง
    cv2.rectangle(display_frame, (0, 420), (640, 480), (245, 117, 16), -1)

    # 🟢 [จุดแก้ที่ 2] เช็กว่ามีการยกมือขึ้นมาหรือไม่ (ถ้าไม่ยกมือ ค่าพิกัดจะเป็น 0 ทั้งหมด)
    has_hand = (np.sum(left_hand) != 0) or (np.sum(right_hand) != 0)

    # ทำนายเมื่อครบ 30 เฟรม และมีการชูมืออยู่หน้ากล้องเท่านั้น
    if len(sequence) == 30 and has_hand:
        input_data = torch.tensor([sequence], dtype=torch.float32).to(device)
        
        with torch.no_grad():
            res = model(input_data)
            probabilities = torch.softmax(res, dim=1).cpu().numpy()[0]
            best_class_idx = np.argmax(probabilities)
            confidence = probabilities[best_class_idx]

        if confidence > threshold:
            predictions.append(best_class_idx)
            
            # ต้องมั่นใจติดๆ กันมากกว่าเดิม (12 เฟรม)
            if len(predictions) >= 12 and len(set(predictions[-12:])) == 1:
                predicted_label = actions[best_class_idx]
                
                if len(sentence) > 0:
                    if predicted_label != sentence[-1]:
                        sentence.append(predicted_label)
                else:
                    sentence.append(predicted_label)

        if len(sentence) > 5:
            sentence = sentence[-5:]

        pred_text = f"Pred: {actions[best_class_idx]} ({confidence*100:.1f}%)"
        display_frame = draw_thai_text(display_frame, pred_text, (20, 20), font_size=28, color=(0, 255, 0))
    else:
        # 🟢 [จุดแก้ที่ 3] ถ้าไม่ได้ชูมือ ให้เคลียร์บัฟเฟอร์ทำนายชั่วคราว
        predictions = []

    full_sentence = ' '.join(sentence)
    display_frame = draw_thai_text(display_frame, full_sentence, (15, 430), font_size=32, color=(255, 255, 255))

    cv2.imshow('Sign Language Real-time Translation', display_frame)

    # 🟢 [จุดแก้ที่ 4] รองรับปุ่มควบคุมข้อความ
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):  # ล้างข้อความทั้งหมด
        sentence = []
    elif key == 8:  # กด Backspace เพื่อลบคำล่าสุด
        if len(sentence) > 0:
            sentence.pop()

cap.release()
cv2.destroyAllWindows()