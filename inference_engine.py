import os
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import mediapipe as mp
try:
    import mediapipe.python.solutions as mp_solutions
    mp.solutions = mp_solutions
except Exception:
    pass
import pickle
import base64
from collections import deque

class BiLSTMModel(nn.Module):
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

class InferenceEngine:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load encoders and model
        with open('label_encoder.pkl', 'rb') as f:
            self.label_encoder = pickle.load(f)
        self.actions = self.label_encoder.classes_
        num_classes = len(self.actions)
        
        self.scaler = None
        if os.path.exists('scaler.pkl'):
            with open('scaler.pkl', 'rb') as f:
                self.scaler = pickle.load(f)
                
        model_path = 'action_model_best.pth' if os.path.exists('action_model_best.pth') else 'action_model.pth'
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=True)
        
        self.use_scaler = False
        if 'norm.weight' in checkpoint or 'fc3.weight' in checkpoint:
            self.model = BiLSTMAttentionModel(num_classes=num_classes)
            self.use_scaler = (self.scaler is not None)
        else:
            self.model = BiLSTMModel(num_classes=num_classes)
            self.use_scaler = False
            
        self.model.load_state_dict(checkpoint)
        self.model.to(self.device)
        self.model.eval()
        
        # MediaPipe setup
        self.mp_holistic = None
        self.holistic = None
        try:
            if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'holistic'):
                self.mp_holistic = mp.solutions.holistic
            elif hasattr(mp, 'python') and hasattr(mp.python, 'solutions'):
                self.mp_holistic = mp.python.solutions.holistic
            else:
                try:
                    import mediapipe.python.solutions.holistic as mp_holistic
                    self.mp_holistic = mp_holistic
                except Exception:
                    from mediapipe.solutions import holistic as mp_holistic
                    self.mp_holistic = mp_holistic

            if self.mp_holistic:
                self.holistic = self.mp_holistic.Holistic(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
        except Exception as e:
            print(f"[AI Warning] MediaPipe holistic could not be loaded: {e}")

        # State
        self.SEQUENCE_LEN = 30
        self.THRESHOLD = 0.88
        self.sequence = deque(maxlen=self.SEQUENCE_LEN)
        
    def process_base64_image(self, b64_str):
        if not b64_str or self.holistic is None:
            return None, 0.0
            
        try:
            # Decode base64
            if ',' in b64_str:
                b64_str = b64_str.split(',')[1]
            img_data = base64.b64decode(b64_str)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                return None, 0.0
                
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = self.holistic.process(rgb)
        except Exception as e:
            print(f"Error processing image in engine: {e}")
            return None, 0.0
        
        left_hand = [0.0] * 63
        right_hand = [0.0] * 63
        has_hand = False
        
        if results.left_hand_landmarks:
            has_hand = True
            lm_list = []
            for lm in results.left_hand_landmarks.landmark:
                lm_list.extend([lm.x, lm.y, lm.z])
            left_hand = lm_list
            
        if results.right_hand_landmarks:
            has_hand = True
            lm_list = []
            for lm in results.right_hand_landmarks.landmark:
                lm_list.extend([lm.x, lm.y, lm.z])
            right_hand = lm_list
            
        if not has_hand:
            # Maybe clear sequence if no hand for long time?
            return None, 0.0
            
        keypoints = np.array(left_hand + right_hand, dtype=np.float32)
        
        if self.use_scaler and self.scaler is not None:
            keypoints = (keypoints - self.scaler['mean']) / self.scaler['std']
            
        self.sequence.append(keypoints.tolist())
        
        if len(self.sequence) == self.SEQUENCE_LEN:
            input_data = torch.tensor([list(self.sequence)], dtype=torch.float32).to(self.device)
            with torch.no_grad():
                output = self.model(input_data)
                probabilities = torch.softmax(output, dim=1).cpu().numpy()[0]
                best_idx = int(np.argmax(probabilities))
                confidence = float(probabilities[best_idx])
                current_label = self.actions[best_idx]
                
            if confidence >= self.THRESHOLD:
                # Return prediction
                return current_label, confidence
                
        return None, 0.0
