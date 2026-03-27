import cv2
import os
import numpy as np
import time
import face
import hand
import overlay
from utils import Stabilizer

def main():
    print("Initializing Snapchat-style filters (MediaPipe 3D)...")
    
    # Init face mesh
    face_mesh = face.load_face_mesh()
    
    # Load filters (must have alpha channel)
    filter_paths = {
        '1': 'filters/glasses.png',
        '2': 'filters/dog_ears.png',
        '3': 'filters/mustache.png',
        '4': 'filters/joker.png',
        '5': 'filters/mask.png'
    }
    
    filters = {}
    for key, path in filter_paths.items():
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            filters[key] = img
        else:
            print(f"Warning: Could not load filter '{path}'")
            
    active_filter_key = '0' # Default no filter
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return
        
    print("Press Q to quit, S to save screenshot. (Or use Hand Gestures!)")
    os.makedirs('screenshots', exist_ok=True)
    shot_count = 0
    last_shot_time = 0
    flash_end_time = 0
    
    from collections import Counter
    finger_buffer = []
    last_filter_switch_time = 0
    
    # Init stabilizers with much higher alpha (0.7) for much faster, more responsive tracking
    stable_pos = Stabilizer(alpha=0.7)
    stable_size = Stabilizer(alpha=0.7)
    stable_angle = Stabilizer(alpha=0.7)
    stable_warppts = Stabilizer(alpha=0.8)
    
    last_filter = active_filter_key

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error capturing frame from camera.")
            break
            
        frame = cv2.flip(frame, 1)
        ih, iw, _ = frame.shape
        
        # Reset stabilizers if filter changed
        if active_filter_key != last_filter:
            stable_pos.reset()
            stable_size.reset()
            stable_angle.reset()
            stable_warppts.reset()
            last_filter = active_filter_key

        # Process Hand Gestures first
        finger_count, is_thumbs_up = hand.analyze_hand(frame)
        current_time = time.time()
        
        if finger_count != -1:
            finger_buffer.append(finger_count)
            if len(finger_buffer) > 20: 
                finger_buffer.pop(0)
                
            most_common = Counter(finger_buffer).most_common(1)[0][0]
            
            if current_time - last_filter_switch_time > 1.0:
                if str(most_common) in ['1', '2', '3', '4', '5']:
                    if active_filter_key != str(most_common):
                        active_filter_key = str(most_common)
                        print(f"Hand Gesture: Switched to filter {active_filter_key}")
                        last_filter_switch_time = current_time
                        finger_buffer.clear()
                elif most_common == 0:
                    if active_filter_key != '0':
                        active_filter_key = '0'
                        print("Hand Gesture: Cleared filter (Fist)")
                        last_filter_switch_time = current_time
                        finger_buffer.clear()
                    
        if is_thumbs_up and current_time - last_shot_time > 2.0:
            file_name = f"screenshots/screenshot_{shot_count}.jpg"
            cv2.imwrite(file_name, frame)
            print(f"Thumbs Up! Saved {file_name}")
            shot_count += 1
            last_shot_time = current_time
            flash_end_time = current_time + 1.0

        multi_face_landmarks = face.detect_faces(frame, face_mesh)
        
        if active_filter_key in filters and multi_face_landmarks:
            filter_img = filters[active_filter_key]
            
            for face_landmarks in multi_face_landmarks:
                # Key Landmarks
                left_eye = face_landmarks[33]
                right_eye = face_landmarks[263]
                forehead = face_landmarks[10]
                lip_top = face_landmarks[164]
                nose_tip = face_landmarks[1]
                left_cheek = face_landmarks[234]
                right_cheek = face_landmarks[454]
                chin = face_landmarks[152]
                
                # 1. Provide exact 3D distance calculations invariant to head turn (yaw)
                eye_dx = (right_eye.x - left_eye.x) * iw
                eye_dy = (right_eye.y - left_eye.y) * ih
                eye_dz = (right_eye.z - left_eye.z) * iw # depth scaling
                eye_dist_3d = np.sqrt(eye_dx**2 + eye_dy**2 + eye_dz**2)
                
                face_dx = (right_cheek.x - left_cheek.x) * iw
                face_dy = (right_cheek.y - left_cheek.y) * ih
                face_dz = (right_cheek.z - left_cheek.z) * iw
                face_width_3d = np.sqrt(face_dx**2 + face_dy**2 + face_dz**2)
                
                face_hx = (chin.x - forehead.x) * iw
                face_hy = (chin.y - forehead.y) * ih
                face_hz = (chin.z - forehead.z) * iw
                face_height_3d = np.sqrt(face_hx**2 + face_hy**2 + face_hz**2)
                
                # 2. Angle calculation
                raw_angle = -np.degrees(np.arctan2(eye_dy, eye_dx))
                angle = stable_angle.update(raw_angle)
                
                if active_filter_key in ('4', '5'):
                    # Affine Warping Path for Masks
                    raw_pts = np.array([
                        [left_eye.x * iw, left_eye.y * ih],
                        [right_eye.x * iw, right_eye.y * ih],
                        [chin.x * iw, chin.y * ih]
                    ])
                    # Flatten tracking points for stabilizer
                    flat_pts = tuple(raw_pts.flatten())
                    smoothed_flat = stable_warppts.update(flat_pts)
                    smoothed_pts = np.array(smoothed_flat).reshape(3, 2)
                    
                    frame = overlay.overlay_warped_mask(frame, filter_img, smoothed_pts, alpha_multiplier=0.8)
                
                else: 
                    # Transparent Overlay Path for Glasses/Ears/Mustache
                    if active_filter_key == '1': # Glasses
                        raw_w = eye_dist_3d * 2.0
                        raw_cx = (left_eye.x + right_eye.x) / 2 * iw
                        raw_cy = (left_eye.y + right_eye.y) / 2 * ih
                    elif active_filter_key == '2': # Dog Ears
                        raw_w = face_width_3d * 1.5
                        raw_cx = forehead.x * iw
                        raw_cy = forehead.y * ih - face_height_3d * 0.25
                    elif active_filter_key == '3': # Mustache
                        raw_w = eye_dist_3d * 1.5
                        raw_cx = lip_top.x * iw
                        raw_cy = lip_top.y * ih
                        
                    # Smooth coordinates and size
                    smoothed_cx, smoothed_cy = stable_pos.update((raw_cx, raw_cy))
                    filter_width = int(stable_size.update(raw_w))
                    filter_height = int(filter_width * (filter_img.shape[0] / filter_img.shape[1]))
                    
                    pos_x = int(smoothed_cx - (filter_width / 2))
                    pos_y = int(smoothed_cy - (filter_height / 2))
                    
                    frame = overlay.overlay_transparent(frame, filter_img, pos_x, pos_y, (filter_width, filter_height), angle)

        cv2.putText(frame, "1:Glass|2:Dog|3:Must|4:Jkr|5:Msk|0:-",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
        if current_time < flash_end_time:
            cv2.putText(frame, "SAVED!", (iw//2 - 80, ih//2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

        cv2.imshow("Snap Filters Demo", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == ord('Q'):
            break
        elif key == ord('s') or key == ord('S'):
            file_name = f"screenshots/screenshot_{shot_count}.jpg"
            cv2.imwrite(file_name, frame)
            print(f"Saved {file_name}")
            shot_count += 1
        elif chr(key) in ['0', '1', '2', '3', '4', '5']:
            active_filter_key = chr(key)
            print(f"Switched to filter {active_filter_key}")
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
