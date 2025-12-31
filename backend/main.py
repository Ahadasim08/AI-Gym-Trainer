import json
import base64
import cv2
import numpy as np
import time
import math
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ultralytics import YOLO
from collections import deque

app = FastAPI()

# Load Model
print("⏳ Loading YOLO Model...")
model = YOLO("yolov8n-pose.pt")
print("✅ Model Loaded!")

# --- Helper Functions ---
def calculate_angle(p1, p2, p3):
    try:
        if p1 is None or p2 is None or p3 is None: return 0
        a, b, c = np.array(p1), np.array(p2), np.array(p3)
        ba, bc = a - b, c - b
        cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
        return 0 if np.isnan(angle) else int(angle)
    except:
        return 0

def calculate_vertical_angle(p1, p2):
    try:
        if p1 is None or p2 is None: return 0
        return math.degrees(math.atan2(abs(p1[0] - p2[0]), abs(p1[1] - p2[1])))
    except:
        return 0

def safe_int(value):
    try:
        return 0 if (value is None or np.isnan(value)) else int(value)
    except:
        return 0

# --- MAIN WEBSOCKET ENDPOINT ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Client Connected!")
    
    # Session State
    current_mode = "squat" 
    count = 0
    state = "Start"
    last_rep_time = 0
    REP_COOLDOWN = 0.6
    session_active = False  
    calibration_frames = 0  
    CALIBRATION_TARGET = 10 
    
    # Visuals
    glow_timer = 0
    angle_buffer = deque(maxlen=5)
    
    # Thresholds
    CURL_UP_THRESH = 80     
    CURL_DOWN_THRESH = 140  

    while True:
        try:
            raw_data = await websocket.receive_text()
            
            # 1. Handle Config
            if "config" in raw_data:
                config = json.loads(raw_data)
                current_mode = config.get("mode", "squat")
                count = 0 
                state = "Start"
                session_active = False
                calibration_frames = 0
                angle_buffer.clear()
                glow_timer = 0
                print(f"🔄 Switched to {current_mode}")
                continue

            # 2. Decode Image
            image_data = raw_data.split(',')[1] if "," in raw_data else raw_data
            image_bytes = base64.b64decode(image_data)
            np_arr = np.frombuffer(image_bytes, np.uint8)
            if len(np_arr) == 0: continue
            
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            if frame is None: continue

            # Resize to 480p
            height, width = frame.shape[:2]
            if width > 480:
                scale = 480 / width
                frame = cv2.resize(frame, (480, int(height * scale)))

            # 3. AI Inference
            results = model(frame, verbose=False)
            
            feedback = "Stand in Frame"
            color = "gray"
            angle_val = 0
            
            p1, p2, p3 = None, None, None
            shoulder_point, hip_point = None, None
            ai_remark = ""

            # --- PROCESS BODY SKELETON ---
            if len(results[0].boxes) > 0:
                boxes = results[0].boxes.xyxy.cpu().numpy()
                areas = [(box[2]-box[0])*(box[3]-box[1]) for box in boxes]
                max_idx = np.argmax(areas)
                kp = results[0].keypoints.data[max_idx].cpu().numpy()

                # --- MODE: BICEP CURLS ---
                if current_mode == "curl":
                    left_conf = sum(kp[i][2] for i in [5,7,9])
                    right_conf = sum(kp[i][2] for i in [6,8,10])
                    side_idxs = [5,7,9] if left_conf > right_conf else [6,8,10]
                    
                    if kp[side_idxs[0]][2] > 0.5: 
                        p1, p2, p3 = kp[side_idxs[0]][:2], kp[side_idxs[1]][:2], kp[side_idxs[2]][:2]
                        active_shoulder = p1

                        raw_angle = calculate_angle(p1, p2, p3)
                        angle_buffer.append(raw_angle)
                        angle_val = sum(angle_buffer) / len(angle_buffer)

                        if not session_active:
                            if angle_val > 150:
                                calibration_frames += 1
                                progress = int((calibration_frames / CALIBRATION_TARGET) * 100)
                                feedback, color = f"READY? {progress}%", "yellow"
                                if calibration_frames > CALIBRATION_TARGET: session_active = True
                            elif angle_val < 130: session_active = True
                            else: feedback, color = "START POSITION", "red"
                        else:
                            if angle_val > CURL_DOWN_THRESH:
                                feedback, color, state = "STRETCH", "cyan", "Down"
                            elif angle_val < CURL_UP_THRESH:
                                if state == "Down" and (time.time() - last_rep_time > REP_COOLDOWN):
                                    count += 1
                                    last_rep_time = time.time()
                                    state = "Up"
                                    glow_timer = 15
                                
                                if calculate_vertical_angle(active_shoulder, p2) > 35:
                                    feedback, color, ai_remark = "ELBOW SWING ⚠️", "orange", "Lock your elbows by your side!"
                                else:
                                    feedback, color = "PERFECT!", "green"
                            else:
                                feedback, color = "CURL...", "orange"

                        # DRAW CURL
                        if p1 is not None:
                            if glow_timer > 0:
                                # Yellow Glow (BGR: 0, 255, 255)
                                draw_color, thickness = (0, 255, 255), 10 
                                glow_timer -= 1
                            else:
                                draw_color = (0, 255, 0) if session_active else (0, 0, 255)
                                thickness = 4
                            
                            pt1, pt2, pt3 = (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (int(p3[0]), int(p3[1]))
                            cv2.line(frame, pt1, pt2, draw_color, thickness)
                            cv2.line(frame, pt2, pt3, draw_color, thickness)
                            cv2.putText(frame, str(int(angle_val)), (pt2[0]-40, pt2[1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

                # --- MODE: SQUATS ---
                elif current_mode == "squat":
                    if kp[11][2] > 0.3 and kp[13][2] > 0.3:
                        p1, p2, p3 = kp[11][:2], kp[13][:2], kp[15][:2]
                        shoulder_point = kp[5][:2]
                        hip_point = kp[11][:2]

                        raw_angle = calculate_angle(p1, p2, p3)
                        angle_buffer.append(raw_angle)
                        angle_val = sum(angle_buffer) / len(angle_buffer)
                        
                        torso_lean = calculate_vertical_angle(shoulder_point, hip_point)

                        if not session_active:
                            if angle_val > 160:
                                calibration_frames += 1
                                progress = int((calibration_frames / CALIBRATION_TARGET) * 100)
                                feedback, color = f"READY? {progress}%", "yellow"
                                if calibration_frames > CALIBRATION_TARGET: session_active = True
                            elif angle_val < 140: session_active = True
                            else: feedback, color = "STAND STRAIGHT", "red"
                        else:
                            if torso_lean > 50: 
                                feedback, color, ai_remark = "CHEST UP! ⚠️", "red", "Keep chest high to save your back!"
                            elif angle_val < 95: 
                                feedback, color, state = "GOOD DEPTH!", "green", "Down"
                            elif angle_val > 160:
                                feedback, color = "STAND", "cyan"
                                if state == "Down" and (time.time() - last_rep_time > REP_COOLDOWN):
                                    count += 1
                                    last_rep_time = time.time()
                                    state = "Up"
                                    glow_timer = 15
                            else: feedback, color = "LOWER...", "orange"

                        # DRAW SQUAT
                        if p1 is not None:
                            if glow_timer > 0:
                                # Yellow Glow (BGR: 0, 255, 255)
                                draw_color, thickness = (0, 255, 255), 10
                                glow_timer -= 1
                            else:
                                draw_color = (0, 255, 0) if session_active else (0, 0, 255)
                                thickness = 4

                            pt1, pt2, pt3 = (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), (int(p3[0]), int(p3[1]))
                            s_pt, h_pt = (int(shoulder_point[0]), int(shoulder_point[1])), (int(hip_point[0]), int(hip_point[1]))

                            cv2.line(frame, pt1, pt2, draw_color, thickness)
                            cv2.line(frame, pt2, pt3, draw_color, thickness)
                            
                            back_color = (0, 0, 255) if torso_lean > 50 else (0, 255, 255)
                            cv2.line(frame, s_pt, h_pt, back_color, 4)
                            
                            cv2.putText(frame, str(int(angle_val)), (pt2[0]-50, pt2[1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

            # Encode Response
            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 35])
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            
            keypoints_data = {}
            if current_mode == "curl" and p1 is not None:
                keypoints_data = {"p1": [safe_int(p1[0]), safe_int(p1[1])], "p2": [safe_int(p2[0]), safe_int(p2[1])], "p3": [safe_int(p3[0]), safe_int(p3[1])]}
            elif current_mode == "squat" and p1 is not None:
                keypoints_data = {
                    "p1": [safe_int(p1[0]), safe_int(p1[1])], "p2": [safe_int(p2[0]), safe_int(p2[1])], "p3": [safe_int(p3[0]), safe_int(p3[1])],
                    "s_pt": [safe_int(shoulder_point[0]), safe_int(shoulder_point[1])], "h_pt": [safe_int(hip_point[0]), safe_int(hip_point[1])]
                }
            
            await websocket.send_json({
                "reps": count,
                "feedback": feedback,
                "color": color,
                "processed_image": frame_b64, 
                "angle": safe_int(angle_val),
                "ai_remark": ai_remark,
                "keypoints": keypoints_data
            })

        except WebSocketDisconnect:
            print("❌ Client Disconnected")
            break
        except Exception as e:
            print(f"⚠️ Recovered from Error: {e}")
            continue