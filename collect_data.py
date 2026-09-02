import cv2
import mediapipe as mp
import numpy as np
import os
import time
import datetime

# =========================
# ตั้งค่าพื้นฐาน
# =========================
SEQUENCE_LENGTH = 30        # จำนวนเฟรมต่อ 1 sample
NUMBER_OF_SEQUENCES = 100   # จำนวน sample ที่ต้องการต่อคำ
DATA_PATH = "sequences"
DELAY_BETWEEN_RECORD = 1.5  # วินาทีพักระหว่างรอบ
REQUIRE_HAND = True         # True = ต้องตรวจพบมือก่อนจึงบันทึก

# =========================
# กรอก Label ตอน Runtime
# =========================
print("=" * 50)
print("   Sign Language Data Collector")
print("=" * 50)
LABEL = input("กรอก Label (คำศัพท์) ที่ต้องการเก็บข้อมูล: ").strip()
if not LABEL:
    print("ERROR: กรุณากรอก Label ก่อน")
    exit()

# สร้างชื่อโฟลเดอร์ใหม่ด้วย Timestamp ทุกครั้งที่รัน
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
folder_name = f"{LABEL}_{timestamp}"
label_path = os.path.join(DATA_PATH, folder_name)
os.makedirs(label_path, exist_ok=True)

sequence_count = 0
bad_frames_skipped = 0

print(f"\n✅ โฟลเดอร์บันทึก: {label_path}")
print("กด [S] = เริ่ม/หยุดอัดอัตโนมัติ | กด [Q] = ออก\n")

# =========================
# MediaPipe & Camera Setup
# =========================
mp_holistic    = mp.solutions.holistic
mp_drawing     = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose        = mp.solutions.pose

# Pose landmark indices ที่เกี่ยวกับแขน
POSE_ARM_CONNECTIONS = [
    (mp_holistic.PoseLandmark.LEFT_SHOULDER,  mp_holistic.PoseLandmark.LEFT_ELBOW),
    (mp_holistic.PoseLandmark.LEFT_ELBOW,     mp_holistic.PoseLandmark.LEFT_WRIST),
    (mp_holistic.PoseLandmark.RIGHT_SHOULDER, mp_holistic.PoseLandmark.RIGHT_ELBOW),
    (mp_holistic.PoseLandmark.RIGHT_ELBOW,    mp_holistic.PoseLandmark.RIGHT_WRIST),
    # ไหล่ซ้าย-ขวา
    (mp_holistic.PoseLandmark.LEFT_SHOULDER,  mp_holistic.PoseLandmark.RIGHT_SHOULDER),
]

holistic = mp_holistic.Holistic(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

is_recording_mode = False
prev_time = time.time()


def draw_arm_skeleton(frame, pose_landmarks):
    """วาด skeleton แขนทั้งสองข้าง (ไหล่ → ข้อศอก → ข้อมือ)"""
    if pose_landmarks is None:
        return
    h, w = frame.shape[:2]
    lm = pose_landmarks.landmark

    for start_idx, end_idx in POSE_ARM_CONNECTIONS:
        p1 = lm[start_idx]
        p2 = lm[end_idx]
        # ข้ามถ้า visibility ต่ำ
        if p1.visibility < 0.4 or p2.visibility < 0.4:
            continue
        x1, y1 = int(p1.x * w), int(p1.y * h)
        x2, y2 = int(p2.x * w), int(p2.y * h)
        # เส้น skeleton แขน — สีฟ้าอมเขียว
        cv2.line(frame, (x1, y1), (x2, y2), (0, 210, 180), 3, cv2.LINE_AA)

    # วาด joint circles
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


def draw_progress_bar(frame, x, y, w, h, progress, color_fill=(0, 200, 100), color_bg=(60, 60, 60)):
    """วาด progress bar"""
    cv2.rectangle(frame, (x, y), (x + w, y + h), color_bg, -1)
    fill_w = int(w * progress)
    if fill_w > 0:
        cv2.rectangle(frame, (x, y), (x + fill_w, y + h), color_fill, -1)
    cv2.rectangle(frame, (x, y), (x + w, y + h), (200, 200, 200), 1)


def draw_ui(frame, fps, seq_count, is_recording, has_hand):
    """วาด overlay UI"""
    h, w = frame.shape[:2]

    # แถบด้านบน (semi-transparent)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 55), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Label และสถานะ
    cv2.putText(frame, f"Label: [{LABEL}]", (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 220, 80), 2)
    cv2.putText(frame, f"FPS: {fps:.0f}", (w - 100, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    # Hand Indicator
    hand_color = (0, 220, 80) if has_hand else (0, 80, 220)
    hand_text = "HAND: OK" if has_hand else "HAND: --"
    cv2.putText(frame, hand_text, (w - 160, 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, hand_color, 1)

    # แถบด้านล่าง
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, h - 70), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay2, 0.75, frame, 0.25, 0, frame)

    # Progress Bar
    progress = seq_count / NUMBER_OF_SEQUENCES
    bar_color = (0, 180, 90) if not is_recording else (0, 80, 220)
    draw_progress_bar(frame, 10, h - 60, w - 20, 18, progress, bar_color)

    # ข้อความ progress
    cv2.putText(frame, f"Samples: {seq_count} / {NUMBER_OF_SEQUENCES}  ({progress*100:.0f}%)",
                (10, h - 68), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    # สถานะ Recording
    if is_recording:
        status_text = ">>> AUTO RECORDING <<<"
        status_color = (0, 80, 255)
        # กระพริบ
        if int(time.time() * 2) % 2 == 0:
            cv2.putText(frame, status_text, (10, h - 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)
    else:
        cv2.putText(frame, "READY  [S]=Start  [Q]=Quit", (10, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 220, 120), 1)

    return frame


# =========================
# Main Loop
# =========================
while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    # FPS calculation
    curr_time = time.time()
    fps = 1.0 / max(curr_time - prev_time, 1e-6)
    prev_time = curr_time

    display_frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False
    results = holistic.process(rgb)
    rgb.flags.writeable = True

    has_hand = False

    # วาด skeleton แขน (ต้องวาดก่อน เพื่อให้อยู่ด้านล่าง hand)
    draw_arm_skeleton(display_frame, results.pose_landmarks)

    # วาด Hand landmarks ทั้งสองข้าง
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

    draw_ui(display_frame, fps, sequence_count, is_recording_mode, has_hand)
    cv2.imshow("Sign Language Data Collector", display_frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("s"):
        is_recording_mode = not is_recording_mode
        if is_recording_mode:
            print(f"\n>>> เริ่มโหมดอัดต่อเนื่อง <<<")
        else:
            print(f"\n>>> หยุดโหมดอัดชั่วคราว <<<")

    if key == ord("q"):
        break

    # ==================
    # Auto Recording Loop
    # ==================
    if is_recording_mode:
        if sequence_count >= NUMBER_OF_SEQUENCES:
            print(f"\n✅ คำว่า '{LABEL}' เก็บครบ {NUMBER_OF_SEQUENCES} samples แล้ว!")
            is_recording_mode = False
            continue

        # 1. Countdown / พักระหว่างรอบ
        start_delay = time.time()
        cancelled = False

        while time.time() - start_delay < DELAY_BETWEEN_RECORD:
            ret, cd_frame = cap.read()
            if not ret:
                break
            cd_frame = cv2.flip(cd_frame, 1)
            time_left = DELAY_BETWEEN_RECORD - (time.time() - start_delay)

            # Countdown overlay
            overlay = cd_frame.copy()
            cv2.rectangle(overlay, (0, 0), (cd_frame.shape[1], cd_frame.shape[0]), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.3, cd_frame, 0.7, 0, cd_frame)

            cv2.putText(cd_frame, "GET READY",
                        (180, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 200, 0), 3)
            cv2.putText(cd_frame, f"{time_left:.1f}s",
                        (270, 280), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 220, 255), 4)
            cv2.putText(cd_frame, f"Sample {sequence_count + 1} / {NUMBER_OF_SEQUENCES}",
                        (160, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

            cv2.imshow("Sign Language Data Collector", cd_frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ord("q") or k == ord("s"):
                is_recording_mode = False
                cancelled = True
                break

        if cancelled:
            continue

        # 2. เก็บข้อมูล SEQUENCE_LENGTH เฟรม
        sequence = []
        frame_hand_count = 0

        for frame_number in range(SEQUENCE_LENGTH):
            ret, rec_frame = cap.read()
            if not ret:
                break
            rec_flipped = cv2.flip(rec_frame, 1)
            rec_rgb = cv2.cvtColor(rec_flipped, cv2.COLOR_BGR2RGB)
            rec_rgb.flags.writeable = False
            rec_results = holistic.process(rec_rgb)
            rec_rgb.flags.writeable = True

            left_hand  = [0.0] * 63
            right_hand = [0.0] * 63
            detected_this_frame = False

            # ดึง landmarks จาก Holistic (left/right แยกถึงกันเลย)
            if rec_results.left_hand_landmarks:
                detected_this_frame = True
                frame_hand_count += 1
                lm_list = []
                for lm in rec_results.left_hand_landmarks.landmark:
                    lm_list.extend([lm.x, lm.y, lm.z])
                left_hand = lm_list

            if rec_results.right_hand_landmarks:
                detected_this_frame = True
                if not rec_results.left_hand_landmarks:  # นับ ถ้ายังไม่นับ
                    frame_hand_count += 1
                lm_list = []
                for lm in rec_results.right_hand_landmarks.landmark:
                    lm_list.extend([lm.x, lm.y, lm.z])
                right_hand = lm_list

            # วาด arm skeleton
            draw_arm_skeleton(rec_flipped, rec_results.pose_landmarks)

            # วาด hand landmarks
            if rec_results.left_hand_landmarks:
                mp_drawing.draw_landmarks(
                    rec_flipped, rec_results.left_hand_landmarks,
                    mp_holistic.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )
            if rec_results.right_hand_landmarks:
                mp_drawing.draw_landmarks(
                    rec_flipped, rec_results.right_hand_landmarks,
                    mp_holistic.HAND_CONNECTIONS,
                    mp_drawing_styles.get_default_hand_landmarks_style(),
                    mp_drawing_styles.get_default_hand_connections_style()
                )

            sequence.append(left_hand + right_hand)

            # HUD ระหว่างบันทึก
            progress_ratio = (frame_number + 1) / SEQUENCE_LENGTH
            draw_progress_bar(rec_flipped, 10, rec_flipped.shape[0] - 30,
                              rec_flipped.shape[1] - 20, 15, progress_ratio,
                              color_fill=(0, 80, 255))
            cv2.putText(rec_flipped,
                        f"REC {sequence_count + 1}/{NUMBER_OF_SEQUENCES}  Frame {frame_number + 1}/{SEQUENCE_LENGTH}",
                        (10, rec_flipped.shape[0] - 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 80, 255), 1)

            cv2.putText(rec_flipped, "● REC", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            cv2.imshow("Sign Language Data Collector", rec_flipped)
            cv2.waitKey(1)

        # 3. Validate และบันทึก
        if len(sequence) == SEQUENCE_LENGTH:
            hand_ratio = frame_hand_count / SEQUENCE_LENGTH

            # ถ้า REQUIRE_HAND=True ต้องตรวจพบมือ >= 50% ของเฟรม
            if REQUIRE_HAND and hand_ratio < 0.5:
                bad_frames_skipped += 1
                print(f"⚠️  [ข้าม] ตรวจพบมือเพียง {hand_ratio*100:.0f}% ({frame_hand_count}/{SEQUENCE_LENGTH} เฟรม) → ข้ามไป")
            else:
                filename = os.path.join(label_path, f"{sequence_count}.npy")
                np.save(filename, np.array(sequence, dtype=np.float32))
                sequence_count += 1
                print(f"✅ [{sequence_count:3d}/{NUMBER_OF_SEQUENCES}] บันทึก: {filename}  (hand={hand_ratio*100:.0f}%)")

# =========================
# สรุปผล
# =========================
print("\n" + "=" * 50)
print(f"  สรุปผลการเก็บข้อมูล: [{LABEL}]")
print("=" * 50)
print(f"  ✅ บันทึกสำเร็จ  : {sequence_count} samples")
print(f"  ⚠️  ข้ามเนื่องจาก no-hand: {bad_frames_skipped} samples")
print(f"  📁 บันทึกใน: {label_path}")
print("=" * 50)

cap.release()
cv2.destroyAllWindows()