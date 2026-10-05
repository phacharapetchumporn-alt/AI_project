import os
import sys
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ป้องกัน UnicodeEncodeError บน Windows Terminal เมื่อพิมพ์ภาษาไทย
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# แก้ไขความเข้ากันได้ระหว่าง TensorFlow กับ Protobuf/MediaPipe บน Python 3.12
try:
    import google.protobuf.runtime_version
except ImportError:
    import types
    rv = types.ModuleType("google.protobuf.runtime_version")
    rv.Domain = type("Domain", (), {"PUBLIC": 1, "INTERNAL": 2})
    rv.ValidateProtobufRuntimeVersion = lambda *args, **kwargs: None
    sys.modules["google.protobuf.runtime_version"] = rv

# pyrefly: ignore [missing-import]
import mediapipe as mp
from tensorflow.keras.models import load_model

# =========================
# 1. โหลดโมเดลและไฟล์ป้ายกำกับคำศัพท์
# =========================
MODEL_PATH = "tsl_lstm_model.h5"
LABEL_JSON = "tsl_one_s_id_to_label.json"
SEQUENCE_LENGTH = 30  # ต้องเท่ากับตอนที่ใช้เทรนโมเดล
CONFIDENCE_THRESHOLD = 0.7  # ค่าความมั่นใจขั้นต่ำที่จะแสดงผล (70%)

# ฟังก์ชันวาดข้อความภาษาไทยลงบนภาพ OpenCV โดยใช้ PIL
def put_thai_text(img, text, pos, font_size=24, color=(0, 255, 120)):
    try:
        font_path = "C:/Windows/Fonts/tahoma.ttf"
        font = ImageFont.truetype(font_path, font_size) if os.path.exists(font_path) else ImageFont.load_default()
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text(pos, text, font=font, fill=(color[2], color[1], color[0]))
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except Exception:
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, font_size / 30, color, 2)
        return img

print("กำลังโหลดโมเดลและข้อมูลคำศัพท์...")
model = None
if os.path.exists(MODEL_PATH):
    try:
        model = load_model(MODEL_PATH)
        print(f"✅ โหลดโมเดล '{MODEL_PATH}' สำเร็จ!")
    except Exception as e:
        print(f"⚠️ เกิดข้อผิดพลาดในการโหลดโมเดล: {e}")
else:
    print(f"⚠️ คำเตือน: ไม่พบไฟล์โมเดล '{MODEL_PATH}' ในโฟลเดอร์นี้")
    print("💡 ระบบจะเปิดโหมดพรีวิวกล้องและตรวจจับพิกัดมือ (เมื่อเทรนโมเดลเสร็จแล้วให้นำไฟล์ tsl_lstm_model.h5 มาวาง)")

id_to_label = {}
if os.path.exists(LABEL_JSON):
    with open(LABEL_JSON, "r", encoding="utf-8") as f:
        id_to_label = json.load(f)
    print(f"✅ โหลดสำเร็จ! พร้อมแปลคำศัพท์ทั้งหมด {len(id_to_label)} คำ")
else:
    print(f"⚠️ ไม่พบไฟล์ '{LABEL_JSON}'")

# =========================
# 2. ตั้งค่า MediaPipe Holistic (Pose + Hands รวม 150 ฟีเจอร์) และกล้อง Webcam
# =========================
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

holistic = mp_holistic.Holistic(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

sequence = []
current_prediction = "กำลังรอท่าทาง..."
confidence_score = 0.0

print("\n🚀 เริ่มต้นระบบแปลภาษามือเรียลไทม์ (150 Features) แล้ว! กด [Q] เพื่อออก")

# =========================
# 3. ลูปประมวลผลภาพจากกล้องแบบเรียลไทม์
# =========================
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        print("ไม่สามารถเปิดกล้องได้")
        break

    # กลับด้านภาพเหมือนกระจก เพื่อความเป็นธรรมชาติในการใช้งาน
    display_frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False
    results = holistic.process(rgb)
    rgb.flags.writeable = True

    # 1. พิกัด Pose Landmarks (33 จุด * 2 ค่า [x, y] = 66 ค่า)
    pose_features = []
    if results.pose_landmarks:
        for lm in results.pose_landmarks.landmark:
            pose_features.extend([lm.x, lm.y])
    else:
        pose_features = [0.0] * 66

    # 2. พิกัด Left Hand Landmarks (21 จุด * 2 ค่า [x, y] = 42 ค่า)
    left_hand = []
    if results.left_hand_landmarks:
        for lm in results.left_hand_landmarks.landmark:
            left_hand.extend([lm.x, lm.y])
    else:
        left_hand = [0.0] * 42

    # 3. พิกัด Right Hand Landmarks (21 จุด * 2 ค่า [x, y] = 42 ค่า)
    right_hand = []
    if results.right_hand_landmarks:
        for lm in results.right_hand_landmarks.landmark:
            right_hand.extend([lm.x, lm.y])
    else:
        right_hand = [0.0] * 42

    # วาดโครงร่าง Pose และ Hands บนหน้าต่างกล้อง
    if results.pose_landmarks:
        mp_drawing.draw_landmarks(
            display_frame,
            results.pose_landmarks,
            mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style(),
        )
    if results.left_hand_landmarks:
        mp_drawing.draw_landmarks(
            display_frame,
            results.left_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style(),
        )
    if results.right_hand_landmarks:
        mp_drawing.draw_landmarks(
            display_frame,
            results.right_hand_landmarks,
            mp_holistic.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style(),
        )

    # รวมพิกัดทั้งหมดตามมาตรฐาน TSL-ONE-Pose:
    # 33 Pose + 21 Left Hand + 21 Right Hand = 75 จุด * 2 ค่า (x, y) = รวม 150 ฟีเจอร์ต่อเฟรม
    frame_features = pose_features + left_hand + right_hand
    sequence.append(frame_features)

    # รักษาความยาวของ Sequence ให้เท่ากับที่โมเดลต้องการ (ตัดเฟรมเก่าสุดออกเมื่อเกินกำหนด)
    if len(sequence) > SEQUENCE_LENGTH:
        sequence.pop(0)

    # เมื่อเก็บข้อมูลครบตามจำนวนเฟรม (30 เฟรม) ให้ส่งเข้าโมเดลทำนาย
    if len(sequence) == SEQUENCE_LENGTH:
        if model is not None:
            input_data = np.expand_dims(
                np.array(sequence, dtype=np.float32), axis=0
            )  # มิติจะเป็น (1, 30, 126)
            
            res = model.predict(input_data, verbose=0)[0]
            best_match_idx = np.argmax(res)
            confidence_score = float(res[best_match_idx])

            # ถ้าความมั่นใจเกินเกณฑ์ที่กำหนด ค่อยอัปเดตคำทำนาย
            if confidence_score > CONFIDENCE_THRESHOLD:
                label_key = str(best_match_idx)
                current_prediction = id_to_label.get(label_key, "ไม่พบคำศัพท์")
            else:
                current_prediction = "กำลังทำท่า..."
        else:
            # โหมดพรีวิวเมื่อยังไม่มีไฟล์โมเดล .h5
            current_prediction = "โหมดตรวจจับมือ (รอไฟล์โมเดล)"
            confidence_score = 1.0

    # =========================
    # 4. ตกแต่งหน้าจอแสดงผล (UI Overlay)
    # =========================
    h, w = display_frame.shape[:2]

    # วาดแถบพื้นหลังข้อความด้านบน
    cv2.rectangle(display_frame, (0, 0), (w, 80), (20, 20, 20), -1)

    # แสดงผลคำแปลภาษามือ (รองรับภาษาไทย)
    text_display = f"Sign: {current_prediction}"
    display_frame = put_thai_text(
        display_frame,
        text_display,
        (15, 15),
        font_size=28,
        color=(0, 255, 120),
    )

    # แสดงค่าความมั่นใจ (Confidence)
    conf_display = f"Confidence: {confidence_score * 100:.1f}%"
    cv2.putText(
        display_frame,
        conf_display,
        (15, 68),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (200, 200, 200),
        1,
    )

    # แสดงคำแนะนำการออก
    cv2.putText(
        display_frame,
        "Press [Q] to Quit",
        (w - 160, h - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (150, 150, 150),
        1,
    )

    # แสดงผลหน้าต่างกล้อง
    cv2.imshow("TSL Real-time Translation System", display_frame)

    # กด 'q' เพื่อออกจากโปรแกรม
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

holistic.close()
cap.release()
cv2.destroyAllWindows()
print("👋 ปิดโปรแกรมเรียบร้อยแล้วครับ")