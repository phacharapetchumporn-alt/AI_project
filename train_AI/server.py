import cv2
import json
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ป้องกันปัญหา Unicode และความเข้ากันได้ระหว่าง TensorFlow กับ Protobuf/MediaPipe บน Python 3.12
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import google.protobuf.runtime_version
except ImportError:
    import types
    rv = types.ModuleType("google.protobuf.runtime_version")
    rv.Domain = type("Domain", (), {"PUBLIC": 1, "INTERNAL": 2})
    rv.ValidateProtobufRuntimeVersion = lambda *args, **kwargs: None
    sys.modules["google.protobuf.runtime_version"] = rv

import mediapipe as mp
from tensorflow.keras.models import load_model
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SignSubs Translation Camera Server")

# อนุญาตให้ Frontend เรียกใช้งาน API ได้
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ค้นหาพาธของโมเดลและ JSON ป้ายกำกับคำศัพท์
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "tsl_lstm_model.h5") if os.path.exists(os.path.join(BASE_DIR, "tsl_lstm_model.h5")) else "tsl_lstm_model.h5"
LABEL_JSON = os.path.join(BASE_DIR, "tsl_one_s_id_to_label.json") if os.path.exists(os.path.join(BASE_DIR, "tsl_one_s_id_to_label.json")) else "tsl_one_s_id_to_label.json"

SEQUENCE_LENGTH = 30
CONFIDENCE_THRESHOLD = 0.7

model = None
if os.path.exists(MODEL_PATH):
    try:
        model = load_model(MODEL_PATH)
        print(f"✅ [server.py] โหลดโมเดล '{MODEL_PATH}' สำเร็จ!")
    except Exception as e:
        print(f"⚠️ [server.py] โหลดโมเดลไม่สำเร็จ: {e}")
else:
    print(f"⚠️ [server.py] ไม่พบไฟล์โมเดล '{MODEL_PATH}'")

id_to_label = {}
if os.path.exists(LABEL_JSON):
    try:
        with open(LABEL_JSON, "r", encoding="utf-8") as f:
            id_to_label = json.load(f)
        print(f"✅ [server.py] โหลดคำศัพท์สำเร็จ {len(id_to_label)} คำ")
    except Exception as e:
        print(f"⚠️ [server.py] โหลดไฟล์คำศัพท์ไม่สำเร็จ: {e}")
else:
    print(f"⚠️ [server.py] ไม่พบไฟล์ป้ายกำกับคำศัพท์ '{LABEL_JSON}'")

mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

holistic = mp_holistic.Holistic(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# สถานะล่าสุดสำหรับส่งให้หน้า Dashboard
latest_info = {
    "current_prediction": "กำลังรอท่าทาง...",
    "confidence_score": 0.0,
    "is_detecting": False
}

cap = None

def get_camera():
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

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

def generate_frames():
    global latest_info
    camera = get_camera()
    sequence = []
    current_prediction = "กำลังรอท่าทาง..."
    confidence_score = 0.0

    if not camera.isOpened():
        err_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        err_frame = put_thai_text(err_frame, "⚠️ ไม่สามารถเปิดกล้อง Webcam ได้ (กำลังลองใหม่...)", (40, 240), font_size=22, color=(0, 100, 255))
        _, buffer = cv2.imencode('.jpg', err_frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        return

    try:
        while True:
            success, frame = camera.read()
            if not success:
                import time
                time.sleep(0.04)
                continue

            display_frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = holistic.process(rgb)
            rgb.flags.writeable = True

            # ดึงฟีเจอร์ Pose และ Hands (150 Features)
            pose_features = [lm.x for lm in results.pose_landmarks.landmark] + [lm.y for lm in results.pose_landmarks.landmark] if results.pose_landmarks else [0.0] * 66
            left_hand = [lm.x for lm in results.left_hand_landmarks.landmark] + [lm.y for lm in results.left_hand_landmarks.landmark] if results.left_hand_landmarks else [0.0] * 42
            right_hand = [lm.x for lm in results.right_hand_landmarks.landmark] + [lm.y for lm in results.right_hand_landmarks.landmark] if results.right_hand_landmarks else [0.0] * 42

            # วาดโครงร่างลงเฟรม
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(display_frame, results.pose_landmarks, mp_holistic.POSE_CONNECTIONS)
            if results.left_hand_landmarks:
                mp_drawing.draw_landmarks(display_frame, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
            if results.right_hand_landmarks:
                mp_drawing.draw_landmarks(display_frame, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)

            has_hands = bool(results.left_hand_landmarks or results.right_hand_landmarks)
            latest_info["is_detecting"] = has_hands

            frame_features = pose_features + left_hand + right_hand
            sequence.append(frame_features)
            if len(sequence) > SEQUENCE_LENGTH:
                sequence.pop(0)

            if len(sequence) == SEQUENCE_LENGTH and model is not None:
                input_data = np.expand_dims(np.array(sequence, dtype=np.float32), axis=0)
                res = model.predict(input_data, verbose=0)[0]
                best_match_idx = np.argmax(res)
                confidence_score = float(res[best_match_idx])
                if confidence_score > CONFIDENCE_THRESHOLD:
                    current_prediction = id_to_label.get(str(best_match_idx), f"ท่าทาง {best_match_idx}")
                else:
                    if not has_hands:
                        current_prediction = "กำลังรอท่าทาง..."

            latest_info["current_prediction"] = current_prediction
            latest_info["confidence_score"] = round(confidence_score * 100, 1)

            # ตกแต่ง UI บนภาพ
            display_frame = put_thai_text(display_frame, f"Sign: {current_prediction}", (15, 15), font_size=28)
            cv2.putText(display_frame, f"Conf: {confidence_score * 100:.1f}%", (15, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

            # แปลงภาพเป็น Byte เพื่อส่งสตรีม
            ret, buffer = cv2.imencode('.jpg', display_frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    except GeneratorExit:
        pass
    except Exception as e:
        print(f"Stream error: {e}")

@app.get("/")
def index():
    return {
        "message": "SignSubs Realtime Translation Camera Server is running",
        "video_feed": "/video_feed",
        "status": "/status"
    }

@app.get("/status")
def get_status():
    camera = get_camera()
    return JSONResponse({
        "status": "online",
        "current_prediction": latest_info["current_prediction"],
        "confidence_score": latest_info["confidence_score"],
        "is_detecting": latest_info["is_detecting"],
        "model_loaded": model is not None,
        "labels_count": len(id_to_label),
        "camera_active": camera.isOpened() if camera else False
    })

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("🚀 เริ่มต้นเซิร์ฟเวอร์ Translation Camera (server.py)")
    print("📡 Video Stream URL: http://127.0.0.1:8000/video_feed")
    print("📊 Status URL:       http://127.0.0.1:8000/status")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)