import os
# pyrefly: ignore [missing-import]
import cv2  # type: ignore
# pyrefly: ignore [missing-import]
import numpy as np  # type: ignore
# pyrefly: ignore [missing-import]
import torch  # type: ignore
# pyrefly: ignore [missing-import]
import torch.nn as nn  # type: ignore
# pyrefly: ignore [missing-import]
import torch.nn.functional as F  # type: ignore
# pyrefly: ignore [missing-import]
import mediapipe as mp  # type: ignore
try:
    # pyrefly: ignore [missing-import]
    import mediapipe.python.solutions as mp_solutions  # type: ignore
    mp.solutions = mp_solutions
except Exception:
    pass
import pickle
import base64
from collections import deque
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Protect Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Protobuf/TensorFlow compatibility fix for Python 3.12
try:
    import google.protobuf.runtime_version
except ImportError:
    import types
    rv = types.ModuleType("google.protobuf.runtime_version")
    rv.Domain = type("Domain", (), {"PUBLIC": 1, "INTERNAL": 2})
    rv.ValidateProtobufRuntimeVersion = lambda *args, **kwargs: None
    sys.modules["google.protobuf.runtime_version"] = rv

import mediapipe as mp
import tensorflow as tf
from tensorflow.keras.models import load_model

def get_thai_font(size=24):
    font_candidates = [
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/browa.ttf",
        "C:/Windows/Fonts/angsana.ttf",
        "C:/Windows/Fonts/cordia.ttf",
        "/usr/share/fonts/truetype/tlwg/TlwgTypo.ttf"
    ]
    for p in font_candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()

def put_thai_text(img, text, pos, font_size=24, color=(0, 255, 120)):
    try:
        font = get_thai_font(font_size)
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        draw.text(pos, text, font=font, fill=(color[2], color[1], color[0]))
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except Exception:
        cv2.putText(img, text, pos, cv2.FONT_HERSHEY_SIMPLEX, font_size / 30, color, 2)
        return img


class InferenceEngine:
    """
    Bridge connecting train_AI/realtime_translate.py to Web Interface.
    Uses:
      - MediaPipe Holistic (150 features: 33 Pose + 21 Left Hand + 21 Right Hand)
      - LSTM Model (tsl_lstm_model.h5)
      - Vocabulary Mapping (tsl_one_s_id_to_label.json)
    """

    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Locate model file
        model_paths = [
            os.path.join(base_dir, "train_AI", "tsl_lstm_model.h5"),
            os.path.join(base_dir, "tsl_lstm_model.h5"),
            "train_AI/tsl_lstm_model.h5",
            "tsl_lstm_model.h5"
        ]
        self.model_path = next((p for p in model_paths if os.path.exists(p)), None)

        # Locate label json
        label_paths = [
            os.path.join(base_dir, "train_AI", "tsl_one_s_id_to_label.json"),
            os.path.join(base_dir, "tsl_one_s_id_to_label.json"),
            "train_AI/tsl_one_s_id_to_label.json",
            "tsl_one_s_id_to_label.json"
        ]
        self.label_path = next((p for p in label_paths if os.path.exists(p)), None)

        self.model = None
        self.id_to_label = {}
        self.sequence_length = 30
        self.confidence_threshold = 0.70

        # Load Labels
        if self.label_path and os.path.exists(self.label_path):
            try:
                with open(self.label_path, "r", encoding="utf-8") as f:
                    self.id_to_label = json.load(f)
                print(f"[AI] Loaded {len(self.id_to_label)} labels from {self.label_path}")
            except Exception as e:
                print(f"[AI Error] Failed to load label json: {e}")

        # Load Keras LSTM Model
        if self.model_path and os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                print(f"[AI] Successfully loaded LSTM model from {self.model_path}")
                print(f"[AI] Input shape: {self.model.input_shape}, Output shape: {self.model.output_shape}")
            except Exception as e:
                print(f"[AI Error] Failed to load model: {e}")
        else:
            print(f"[AI Warning] Model file not found in paths: {model_paths}")

        # Initialize MediaPipe Holistic
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )

        # Sequence buffer for real-time translation (30 frames x 150 features)
        self.sequence = deque(maxlen=self.sequence_length)
        self.lock = threading.Lock()

        # Shared live state
        self.latest_prediction = "กำลังรอท่าทาง..."
        self.latest_confidence = 0.0
        self.raw_probabilities = {}

        # OpenCV Camera capture thread handle (for /video_feed)
        self.camera_cap = None
        self.is_streaming = False

    def reset_sequence(self):
        with self.lock:
            self.sequence.clear()
            self.latest_prediction = "กำลังรอท่าทาง..."
            self.latest_confidence = 0.0

    def extract_features(self, results):
        """
        Extracts 150 features exactly as in train_AI/realtime_translate.py:
          - 33 Pose landmarks (x, y) = 66
          - 21 Left hand landmarks (x, y) = 42
          - 21 Right hand landmarks (x, y) = 42
          Total = 150 floats
        """
        # 1. Pose landmarks (66)
        pose_features = []
        if results.pose_landmarks:
            for lm in results.pose_landmarks.landmark:
                pose_features.extend([float(lm.x), float(lm.y)])
        else:
            pose_features = [0.0] * 66

        # 2. Left hand landmarks (42)
        left_hand = []
        if results.left_hand_landmarks:
            for lm in results.left_hand_landmarks.landmark:
                left_hand.extend([float(lm.x), float(lm.y)])
        else:
            left_hand = [0.0] * 42

        # 3. Right hand landmarks (42)
        right_hand = []
        if results.right_hand_landmarks:
            for lm in results.right_hand_landmarks.landmark:
                right_hand.extend([float(lm.x), float(lm.y)])
        else:
            right_hand = [0.0] * 42

        frame_features = pose_features + left_hand + right_hand
        return frame_features

    def extract_landmarks_for_client(self, results):
        """
        Formats detected landmarks into lightweight structures for web canvas rendering.
        """
        data = {
            "pose": [],
            "leftHand": [],
            "rightHand": []
        }

        if results.pose_landmarks:
            for lm in results.pose_landmarks.landmark:
                data["pose"].append({"x": lm.x, "y": lm.y, "v": lm.visibility})

        if results.left_hand_landmarks:
            for lm in results.left_hand_landmarks.landmark:
                data["leftHand"].append({"x": lm.x, "y": lm.y})

        if results.right_hand_landmarks:
            for lm in results.right_hand_landmarks.landmark:
                data["rightHand"].append({"x": lm.x, "y": lm.y})

        return data

    def predict_from_features(self, frame_features):
        with self.lock:
            self.sequence.append(frame_features)
            
            if len(self.sequence) < self.sequence_length:
                return "กำลังสะสมเฟรม...", 0.0, False

            if self.model is None:
                return "โหมดตรวจจับมือ (รอไฟล์โมเดล)", 1.0, True

            input_data = np.expand_dims(np.array(self.sequence, dtype=np.float32), axis=0)
            res = self.model.predict(input_data, verbose=0)[0]
            best_idx = int(np.argmax(res))
            confidence = float(res[best_idx])

            self.latest_confidence = confidence

            if confidence >= self.confidence_threshold:
                label = self.id_to_label.get(str(best_idx), f"ท่าทาง {best_idx}")
                self.latest_prediction = label
                return label, confidence, True
            else:
                return "กำลังทำท่า...", confidence, False

    def process_cv2_frame(self, frame):
        """
        Process a single OpenCV BGR frame.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.holistic.process(rgb)
        rgb.flags.writeable = True

        features = self.extract_features(results)
        prediction, confidence, is_confirmed = self.predict_from_features(features)
        client_landmarks = self.extract_landmarks_for_client(results)

        return prediction, confidence, is_confirmed, client_landmarks, results

    def process_base64_image(self, b64_str):
        """
        Entry point for Web frontend /api/process_frame.
        Receives JPEG/PNG base64 data URL.
        """
        if not b64_str:
            return None, 0.0, None

        try:
            if ',' in b64_str:
                b64_str = b64_str.split(',')[1]
            img_bytes = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return None, 0.0, None

            prediction, confidence, is_confirmed, client_landmarks, _ = self.process_cv2_frame(frame)
            return prediction, confidence, client_landmarks
        except Exception as e:
            print(f"[AI Error] Frame decode failed: {e}")
            return None, 0.0, None

    def draw_annotations(self, display_frame, results, prediction, confidence):
        """
        Draw landmarks and overlay onto frame (exact replication of realtime_translate.py).
        """
        h, w = display_frame.shape[:2]

        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(
                display_frame,
                results.pose_landmarks,
                self.mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style(),
            )
        if results.left_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                display_frame,
                results.left_hand_landmarks,
                self.mp_holistic.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style(),
            )
        if results.right_hand_landmarks:
            self.mp_drawing.draw_landmarks(
                display_frame,
                results.right_hand_landmarks,
                self.mp_holistic.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style(),
            )

        # Background banner
        cv2.rectangle(display_frame, (0, 0), (w, 80), (20, 20, 20), -1)

        # Thai prediction text
        text_display = f"Sign: {prediction}"
        display_frame = put_thai_text(
            display_frame,
            text_display,
            (15, 12),
            font_size=26,
            color=(0, 255, 120),
        )

        # Confidence
        conf_display = f"Confidence: {confidence * 100:.1f}%"
        cv2.putText(
            display_frame,
            conf_display,
            (15, 68),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1,
        )

        return display_frame

    def generate_video_stream(self, camera_index=0):
        """
        MJPEG generator for /video_feed endpoint directly streaming the OpenCV camera.
        """
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not cap.isOpened():
            print(f"[AI Error] Unable to open camera {camera_index}")
            return

        try:
            while True:
                success, frame = cap.read()
                if not success:
                    time.sleep(0.05)
                    continue

                display_frame = cv2.flip(frame, 1)
                pred, conf, is_confirmed, client_lm, results = self.process_cv2_frame(display_frame)
                annotated = self.draw_annotations(display_frame, results, pred, conf)

                ret, jpeg = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
                if not ret:
                    continue

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                time.sleep(0.03)  # ~30 FPS
        finally:
            cap.release()
