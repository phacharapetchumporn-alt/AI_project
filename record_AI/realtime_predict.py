import sys
import os
import cv2
import numpy as np
import pickle
import time
import base64
import threading
from collections import deque
from PIL import Image, ImageDraw, ImageFont

# Protect Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Protobuf / TensorFlow compatibility fix for Python 3.12
try:
    import google.protobuf.runtime_version
except ImportError:
    try:
        import types
        import google.protobuf
        rv = types.ModuleType("google.protobuf.runtime_version")
        rv.Domain = type("Domain", (), {"PUBLIC": 1, "INTERNAL": 2})
        rv.ValidateProtobufRuntimeVersion = lambda *args, **kwargs: None
        sys.modules["google.protobuf.runtime_version"] = rv
        setattr(google.protobuf, "runtime_version", rv)
    except Exception:
        pass

import torch
import torch.nn as nn
import torch.nn.functional as F
import mediapipe as mp

try:
    import mediapipe.python.solutions as mp_solutions
    mp.solutions = mp_solutions
except Exception:
    pass

def find_asset_path(filename: str) -> str:
    """Find file in current directory, script directory, record_AI, or parent directory."""
    candidates = [
        filename,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "record_AI", filename),
        os.path.join(os.getcwd(), "record_AI", filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", filename),
    ]
    for p in candidates:
        if os.path.exists(p):
            return os.path.abspath(p)
    return filename

# =========================
# Thai Text Renderer
# =========================
_thai_font_cache = {}

def get_thai_font(size: int):
    if size not in _thai_font_cache:
        font_candidates = [
            "C:/Windows/Fonts/tahoma.ttf",
            "C:/Windows/Fonts/browa.ttf",
            "C:/Windows/Fonts/angsana.ttf",
            "C:/Windows/Fonts/cordia.ttf",
            "tahoma.ttf",
            "THSarabunNew.ttf",
            "arial.ttf",
            "/usr/share/fonts/truetype/tlwg/TlwgTypo.ttf"
        ]
        for font_name in font_candidates:
            try:
                _thai_font_cache[size] = ImageFont.truetype(font_name, size)
                break
            except OSError:
                continue
        else:
            _thai_font_cache[size] = ImageFont.load_default()
    return _thai_font_cache[size]

def draw_thai_text(img, text, position, font_size=30, color=(255, 255, 255)):
    try:
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        font = get_thai_font(font_size)
        draw.text(position, text, font=font, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    except Exception:
        cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_size / 35, color, 2)
        return img

# =========================
# Model Architectures
# =========================
class BiLSTMModel(nn.Module):
    """โมเดล 2-Layer Bi-LSTM (โครงสร้างดั้งเดิมของ action_model.pth)"""
    def __init__(self, input_size=126, hidden_size=128, num_layers=2, num_classes=6, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0
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
    """โมเดล 3-Layer Bi-LSTM with Temporal Attention"""
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
# Pose Arm Connections
# =========================
mp_holistic = mp.solutions.holistic
mp_drawing  = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

_POSE_ARM_CONNS = [
    (mp_holistic.PoseLandmark.LEFT_SHOULDER,  mp_holistic.PoseLandmark.LEFT_ELBOW),
    (mp_holistic.PoseLandmark.LEFT_ELBOW,     mp_holistic.PoseLandmark.LEFT_WRIST),
    (mp_holistic.PoseLandmark.RIGHT_SHOULDER, mp_holistic.PoseLandmark.RIGHT_ELBOW),
    (mp_holistic.PoseLandmark.RIGHT_ELBOW,    mp_holistic.PoseLandmark.RIGHT_WRIST),
    (mp_holistic.PoseLandmark.LEFT_SHOULDER,  mp_holistic.PoseLandmark.RIGHT_SHOULDER),
]

def draw_arm_skeleton(frame, pose_landmarks):
    """วาดเส้น skeleton แขนทั้งสองข้าง (ไหล่ -> ข้อศอก -> ข้อมือ)"""
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

# =============================================================================
# RealtimeSignTranslator (Translation Engine for Camera & Web)
# =============================================================================
class RealtimeSignTranslator:
    """
    Sign language translation engine powered by PyTorch Bi-LSTM and MediaPipe.
    Used for web API frame processing and OpenCV live camera feeds.
    """
    def __init__(self, model_file=None, label_encoder_file=None, scaler_file=None):
        self.lock = threading.Lock()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.device_str = 'GPU (CUDA)' if torch.cuda.is_available() else 'CPU (PyTorch)'
        self.sequence_len  = 30
        self.threshold     = 0.88
        self.vote_window   = 15
        self.confirm_votes = 10
        self.no_hand_reset = 20
        self.sequence      = deque(maxlen=self.sequence_len)
        self.vote_buffer   = deque(maxlen=self.vote_window)
        self.sentence      = []
        self.last_confirmed = None
        self.no_hand_frames = 0
        self.latest_prediction = "พร้อมตรวจจับ"
        self.latest_confidence = 0.0
        self.latest_probabilities = []
        self.is_ready = False
        le_path = label_encoder_file or find_asset_path('label_encoder.pkl')
        if os.path.exists(le_path):
            with open(le_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            self.actions = [str(a) for a in self.label_encoder.classes_]
            print(f"[AI] Loaded label encoder from {le_path}: {self.actions}")
        else:
            self.label_encoder = None
            self.actions = ['1', '2', '3', '4', '5', 'Blank']
            print(f"[AI Warning] Label encoder not found at {le_path}, using default classes: {self.actions}")
        self.num_classes = len(self.actions)
        sc_path = scaler_file or find_asset_path('scaler.pkl')
        self.scaler = None
        self.use_scaler = False
        if os.path.exists(sc_path):
            try:
                with open(sc_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print(f"[AI] Loaded scaler from {sc_path}")
            except Exception as e:
                print(f"[AI Warning] Could not load scaler: {e}")
        best_p = find_asset_path('action_model_best.pth')
        std_p  = find_asset_path('action_model.pth')
        model_path = model_file or (best_p if os.path.exists(best_p) else std_p)
        self.model = None
        if os.path.exists(model_path):
            try:
                checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
                if 'norm.weight' in checkpoint or 'fc3.weight' in checkpoint:
                    print("[AI] Architecture: BiLSTMAttentionModel")
                    self.model = BiLSTMAttentionModel(num_classes=self.num_classes)
                    self.use_scaler = (self.scaler is not None)
                else:
                    print("[AI] Architecture: BiLSTMModel")
                    self.model = BiLSTMModel(num_classes=self.num_classes)
                    self.use_scaler = False
                self.model.load_state_dict(checkpoint)
                self.model.to(self.device)
                self.model.eval()
                self.is_ready = True
                print(f"[AI] Successfully loaded PyTorch model from {model_path} on {self.device_str}")
            except Exception as err:
                print(f"[AI Error] Failed to load model weights: {err}")
        else:
            print(f"[AI Warning] Model file not found at: {model_path}")
        self.holistic = mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )
    def reset_sequence(self):
        """Reset sequence and predictions (compat with inference_engine)."""
        with self.lock:
            self.sequence.clear()
            self.vote_buffer.clear()
            self.latest_prediction = "พร้อมตรวจจับ"
            self.latest_confidence = 0.0
    def extract_features(self, results):
        """
        Extracts 126 features (Left Hand 63 + Right Hand 63: 21 landmarks * 3 coords).
        """
        left_hand = [0.0] * 63
        right_hand = [0.0] * 63
        has_hand = False
        if results.left_hand_landmarks:
            has_hand = True
            lm_list = []
            for lm in results.left_hand_landmarks.landmark:
                lm_list.extend([float(lm.x), float(lm.y), float(lm.z)])
            left_hand = lm_list
        if results.right_hand_landmarks:
            has_hand = True
            lm_list = []
            for lm in results.right_hand_landmarks.landmark:
                lm_list.extend([float(lm.x), float(lm.y), float(lm.z)])
            right_hand = lm_list
        keypoints = np.array(left_hand + right_hand, dtype=np.float32)
        if self.use_scaler and self.scaler is not None:
            keypoints = (keypoints - self.scaler['mean']) / self.scaler['std']
        return keypoints, has_hand
    def extract_landmarks_for_client(self, results):
        """
        Formats detected landmarks for web canvas rendering (Pose + Hands).
        """
        data = {"pose": [], "leftHand": [], "rightHand": []}
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
    def process_cv2_frame(self, frame):
        """
        Processes a single BGR frame.
        Returns: (prediction, confidence, is_confirmed, client_landmarks, results, vote_count, probabilities)
        """
        with self.lock:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = self.holistic.process(rgb)
            rgb.flags.writeable = True
            keypoints, has_hand = self.extract_features(results)
            self.sequence.append(keypoints.tolist())
            if not has_hand:
                self.no_hand_frames += 1
                if self.no_hand_frames >= self.no_hand_reset:
                    self.vote_buffer.clear()
            else:
                self.no_hand_frames = 0
            current_label = ""
            confidence = 0.0
            is_confirmed = False
            probabilities = None
            vote_count = 0
            if len(self.sequence) == self.sequence_len and has_hand and self.model is not None:
                input_tensor = torch.tensor([list(self.sequence)], dtype=torch.float32).to(self.device)
                with torch.no_grad():
                    output = self.model(input_tensor)
                    probs = torch.softmax(output, dim=1).cpu().numpy()[0]
                    probabilities = probs
                    best_idx = int(np.argmax(probs))
                    confidence = float(probs[best_idx])
                    current_label = self.actions[best_idx] if best_idx < len(self.actions) else f"T{best_idx}"
                    self.latest_probabilities = probs.tolist()
                self.latest_prediction = current_label
                self.latest_confidence = confidence
                if confidence >= self.threshold:
                    self.vote_buffer.append(best_idx)
                if len(self.vote_buffer) > 0:
                    vote_count = sum(1 for v in self.vote_buffer if v == best_idx)
                    if vote_count >= self.confirm_votes:
                        if current_label != self.last_confirmed:
                            if current_label != 'Blank':
                                self.sentence.append(current_label)
                                if len(self.sentence) > 7:
                                    self.sentence = self.sentence[-7:]
                                is_confirmed = True
                            self.last_confirmed = current_label
                            self.vote_buffer.clear()
            elif not has_hand:
                if self.no_hand_frames > 5:
                    current_label = "กำลังรอสัญญาณมือ..."
                    confidence = 0.0
            client_landmarks = self.extract_landmarks_for_client(results)
            return (
                self.latest_prediction if has_hand else "กำลังรอสัญญาณมือ...",
                self.latest_confidence,
                is_confirmed,
                client_landmarks,
                results,
                vote_count,
                probabilities
            )
    def process_base64_image(self, b64_str: str):
        """
        Receives base64 data URL from frontend /api/process_frame.
        Returns: (prediction, confidence, client_landmarks)
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
            display_frame = cv2.flip(frame, 1)
            pred, conf, is_confirmed, client_lm, _, _, _ = self.process_cv2_frame(display_frame)
            return pred, conf, client_lm
        except Exception as err:
            print(f"[AI Error] Base64 frame decode error: {err}")
            return None, 0.0, None
    def draw_hud(self, frame, fps, has_hand, vote_count, current_label, confidence):
        """Draw HUD overlay with status, vote progress bar, and sentence bar."""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 58), (15, 15, 25), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
        fps_color = (0, 200, 100) if fps >= 25 else (0, 140, 255)
        cv2.putText(frame, f"FPS: {fps:.0f}", (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.65, fps_color, 2)
        if has_hand:
            cv2.circle(frame, (110, 15), 8, (0, 220, 80), -1)
            cv2.putText(frame, "HAND", (122, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 80), 1)
        else:
            cv2.circle(frame, (110, 15), 8, (0, 80, 200), -1)
            cv2.putText(frame, "NO HAND", (122, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 200), 1)
        if vote_count > 0:
            vote_ratio = min(vote_count / self.confirm_votes, 1.0)
            bar_color = (0, 220, 255) if vote_ratio < 1.0 else (0, 255, 80)
            cv2.rectangle(frame, (10, 36), (10 + int(200 * vote_ratio), 50), bar_color, -1)
            cv2.rectangle(frame, (10, 36), (210, 50), (80, 80, 80), 1)
            cv2.putText(frame, f"Confirming: {vote_count}/{self.confirm_votes}", (215, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
        if current_label and confidence >= self.threshold:
            pred_str = f"{current_label} ({confidence*100:.0f}%)"
            cv2.putText(frame, pred_str, (w // 2 - 80, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 220, 255), 2)
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (0, h - 68), (w, h), (15, 15, 25), -1)
        cv2.addWeighted(overlay2, 0.85, frame, 0.15, 0, frame)
        cv2.putText(frame, "[C] Clear  [Backspace] Delete  [Q] Quit", (10, h - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 100, 100), 1)
        return frame
    def draw_top_predictions(self, frame, probabilities, top_k=3):
        """Draw Top-K prediction bars on the right side."""
        if probabilities is None or len(probabilities) == 0:
            return
        h, w = frame.shape[:2]
        top_k = min(top_k, len(probabilities))
        top_indices = np.argsort(probabilities)[::-1][:top_k]
        bar_h = 20
        bar_w = 200
        x_start = w - bar_w - 10
        cv2.putText(frame, "Top Predictions:", (x_start, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        for rank, idx in enumerate(top_indices):
            conf = float(probabilities[idx])
            label = self.actions[idx] if idx < len(self.actions) else str(idx)
            y_pos = 80 + rank * (bar_h + 8)
            bg_color = (40, 40, 40)
            fill_color = (0, int(200 * conf), int(100 * (1 - conf)))
            cv2.rectangle(frame, (x_start, y_pos), (x_start + bar_w, y_pos + bar_h), bg_color, -1)
            cv2.rectangle(frame, (x_start, y_pos), (x_start + int(bar_w * conf), y_pos + bar_h), fill_color, -1)
            cv2.rectangle(frame, (x_start, y_pos), (x_start + bar_w, y_pos + bar_h), (100, 100, 100), 1)
            text = f"{label}: {conf*100:.1f}%"
            cv2.putText(frame, text, (x_start + 4, y_pos + bar_h - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)
    def draw_annotations(self, display_frame, results, prediction, confidence, vote_count=0, probabilities=None):
        """Draws arm skeleton, hand landmarks, HUD and prediction bars."""
        draw_arm_skeleton(display_frame, results.pose_landmarks)
        has_hand = False
        if results.left_hand_landmarks:
            has_hand = True
            mp_drawing.draw_landmarks(
                display_frame, results.left_hand_landmarks,
                mp_holistic.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
        if results.right_hand_landmarks:
            has_hand = True
            mp_drawing.draw_landmarks(
                display_frame, results.right_hand_landmarks,
                mp_holistic.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )
        if probabilities is not None:
            self.draw_top_predictions(display_frame, probabilities, top_k=3)
        return self.draw_hud(display_frame, 30.0, has_hand, vote_count, prediction, confidence)
    def generate_video_stream(self, camera_index=0):
        """
        MJPEG generator for /video_feed endpoint streaming OpenCV camera.
        """
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            print(f"[AI Error] Unable to open camera {camera_index}")
            return
        prev_time = time.time()
        try:
            while True:
                success, frame = cap.read()
                if not success:
                    time.sleep(0.04)
                    continue
                curr_time = time.time()
                fps = 1.0 / max(curr_time - prev_time, 1e-6)
                prev_time = curr_time
                display_frame = cv2.flip(frame, 1)
                pred, conf, is_confirmed, client_lm, results, vote_count, probs = self.process_cv2_frame(display_frame)
                annotated = self.draw_annotations(display_frame, results, pred, conf, vote_count, probs)
                ret, jpeg = cv2.imencode('.jpg', annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                if not ret:
                    continue
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                time.sleep(0.03)
        finally:
            cap.release()
    def clear_sentence(self):
        with self.lock:
            self.sentence.clear()
            self.vote_buffer.clear()
            self.last_confirmed = None
            self.latest_prediction = "ล้างประโยคแล้ว"
            self.latest_confidence = 0.0
    def backspace_sentence(self):
        with self.lock:
            if self.sentence:
                self.sentence.pop()
                self.last_confirmed = self.sentence[-1] if self.sentence else None
            self.vote_buffer.clear()
            self.latest_prediction = "ลบคำล่าสุดแล้ว"
            self.latest_confidence = 0.0
    def get_state(self):
        with self.lock:
            return {
                'prediction': self.latest_prediction,
                'confidence': f"{self.latest_confidence * 100:.1f}%",
                'sentence': ' '.join(self.sentence),
                'last_confirmed': self.last_confirmed or '',
                'actions': self.actions,
                'device': self.device_str,
                'is_ready': self.is_ready
            }
    def run_standalone(self):
        """Standalone OpenCV GUI Window"""
        window_name = "Sign Language Real-time Translation"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        prev_time = time.time()
        print("\n🚀 เริ่มระบบแปลภาษามือเรียลไทม์ (PyTorch Bi-LSTM)")
        print(f"📦 จำนวนคำศัพท์: {len(self.actions)} classes {self.actions}")
        print("⌨️  คีย์ลัด: [C] ล้างประโยค | [Backspace] ลบคำล่าสุด | [Q] ออก\n")
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
            curr_time = time.time()
            fps = 1.0 / max(curr_time - prev_time, 1e-6)
            prev_time = curr_time
            display_frame = cv2.flip(frame, 1)
            pred, conf, is_confirmed, client_lm, results, vote_count, probs = self.process_cv2_frame(display_frame)
            annotated = self.draw_annotations(display_frame, results, pred, conf, vote_count, probs)
            cv2.imshow(window_name, annotated)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.clear_sentence()
                print("🗑️  ล้างประโยคแล้ว")
            elif key == 8:
                self.backspace_sentence()
                print(f"⬅️  ลบคำล่าสุด: ประโยคปัจจุบัน = {' '.join(self.sentence)}")
        cap.release()
        cv2.destroyAllWindows()
        print("\n👋 ปิดโปรแกรมเรียบร้อย")

# Alias for compatibility with inference_engine
InferenceEngine = RealtimeSignTranslator

# =============================================================================
# Standalone execution
# =============================================================================
if __name__ == '__main__':
    translator = RealtimeSignTranslator()
    translator.run_standalone()