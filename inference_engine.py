"""
Inference Engine - Bridge connecting realtime_predict.py to Web Interface.
Powered by PyTorch Bi-LSTM Model, MediaPipe Holistic, and Voting Logic from realtime_predict.py.
"""
import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from realtime_predict import RealtimeSignTranslator, InferenceEngine

__all__ = ["InferenceEngine", "RealtimeSignTranslator"]
