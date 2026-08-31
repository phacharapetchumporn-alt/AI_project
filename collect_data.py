import cv2
import mediapipe as mp
import numpy as np
import os
import time
import datetime

# =========================
# ตั้งค่า
# =========================
LABEL = "5"            # เปลี่ยนชื่อคำตามต้องการ
SEQUENCE_LENGTH = 30
NUMBER_OF_SEQUENCES = 100
DATA_PATH = "sequences"
DELAY_BETWEEN_RECORD = 1.5

# 🟢 สร้างชื่อโฟลเดอร์ใหม่ด้วย Timestamp ทุกครั้งที่รัน (เช่น "sequences/วัน_20260826_153744")
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
folder_name = f"{LABEL}_{timestamp}"
label_path = os.path.join(DATA_PATH, folder_name)

os.makedirs(label_path, exist_ok=True)
sequence_count = 0  # โฟลเดอร์ใหม่เริ่มนับที่ 0 เสมอ

# =========================
# MediaPipe & Camera Setup
# =========================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

cap = cv2.VideoCapture(0)
is_recording_mode = False

print(f"=== โหมดเก็บข้อมูล: [{LABEL}] ===")
print(f"บันทึกเข้าโฟลเดอร์ใหม่: {label_path}")
print("กด S เพื่อเริ่มอัดอัตโนมัติ | กด S อีกครั้งเพื่อหยุด | กด Q เพื่อออก")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    display_frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(display_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    status_text = "AUTO RECORDING..." if is_recording_mode else "READY (Press S to Start)"
    status_color = (0, 0, 255) if is_recording_mode else (0, 255, 0)
    
    cv2.putText(display_frame, f"Label: {LABEL}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(display_frame, f"Samples: {sequence_count}/{NUMBER_OF_SEQUENCES}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(display_frame, f"Status: {status_text}", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

    cv2.imshow("Sign Language Data Collector", display_frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        is_recording_mode = not is_recording_mode
        print("\n>>> เริ่มโหมดอัดต่อเนื่อง! <<<" if is_recording_mode else "\n>>> หยุดโหมดอัดชั่วคราว <<<")

    if key == ord("q"):
        break

    if is_recording_mode:
        if sequence_count >= NUMBER_OF_SEQUENCES:
            print(f"\nคำว่า '{LABEL}' เก็บครบ {NUMBER_OF_SEQUENCES} samples แล้ว!")
            is_recording_mode = False
            continue

        # 1. พักระหว่างรอบ
        start_delay = time.time()
        cancelled = False
        while time.time() - start_delay < DELAY_BETWEEN_RECORD:
            ret, cd_frame = cap.read()
            if not ret: 
                break
            cd_frame = cv2.flip(cd_frame, 1)
            time_left = round(DELAY_BETWEEN_RECORD - (time.time() - start_delay), 1)
            cv2.putText(cd_frame, f"Get Ready: {time_left}s", (180, 250), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 165, 255), 3)
            cv2.putText(cd_frame, f"Sample: {sequence_count + 1}/{NUMBER_OF_SEQUENCES}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Sign Language Data Collector", cd_frame)
            
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q") or k == ord("s"):
                is_recording_mode = False
                cancelled = True
                break

        if cancelled: 
            continue

        # 2. เก็บข้อมูล 30 เฟรม
        sequence = []
        for frame_number in range(SEQUENCE_LENGTH):
            ret, rec_frame = cap.read()
            if not ret: 
                break
            rec_frame_flipped = cv2.flip(rec_frame, 1)
            rec_rgb = cv2.cvtColor(rec_frame_flipped, cv2.COLOR_BGR2RGB)
            rec_results = hands.process(rec_rgb)

            left_hand = [0.0] * 63
            right_hand = [0.0] * 63

            if rec_results.multi_hand_landmarks and rec_results.multi_handedness:
                for i, hand_landmarks in enumerate(rec_results.multi_hand_landmarks):
                    landmarks = []
                    for lm in hand_landmarks.landmark:
                        landmarks.extend([lm.x, lm.y, lm.z])
                    
                    hand_label = rec_results.multi_handedness[i].classification[0].label
                    if hand_label == "Left": 
                        left_hand = landmarks
                    elif hand_label == "Right": 
                        right_hand = landmarks
                    
                    mp_drawing.draw_landmarks(rec_frame_flipped, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            sequence.append(left_hand + right_hand)
            cv2.putText(rec_frame_flipped, f"RECORDING {sequence_count + 1}/{NUMBER_OF_SEQUENCES} - Frame: {frame_number + 1}/{SEQUENCE_LENGTH}", 
                        (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imshow("Sign Language Data Collector", rec_frame_flipped)
            cv2.waitKey(1)

        # 3. บันทึกไฟล์ลงโฟลเดอร์ใหม่
        if len(sequence) == SEQUENCE_LENGTH:
            filename = os.path.join(label_path, f"{sequence_count}.npy")
            np.save(filename, np.array(sequence))
            sequence_count += 1
            print(f"บันทึกสำเร็จ [{sequence_count}/{NUMBER_OF_SEQUENCES}]: {filename}")

cap.release()
cv2.destroyAllWindows()