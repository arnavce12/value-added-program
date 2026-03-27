import cv2
import math
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os

MODEL_PATH = "hand_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading hand landmark model (Tasks API)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded.")

_hand_landmarker = None

def init_hands():
    global _hand_landmarker
    if _hand_landmarker is None:
        ensure_model()
        base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            running_mode=vision.RunningMode.IMAGE
        )
        _hand_landmarker = vision.HandLandmarker.create_from_options(options)

def dist(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)

def analyze_hand(frame):
    """
    Analyzes the frame for hands using the Tasks API.
    Returns:
    - finger_count: Int representing raised fingers (0-5), or -1 if no hand detected.
    - is_thumbs_up: Bool indicating if the 'Thumbs Up' gesture is performed.
    """
    init_hands()
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    results = _hand_landmarker.detect(mp_image)
    
    finger_count = -1
    is_thumbs_up = False
    point_direction = None
    
    if results.hand_landmarks:
        # Landmarks list directly returned in Tasks API
        hand_landmarks = results.hand_landmarks[0]
        
        # 1. Check main 4 fingers based strictly on vertical Y alignment
        index_up = hand_landmarks[8].y < hand_landmarks[6].y
        middle_up = hand_landmarks[12].y < hand_landmarks[10].y
        ring_up = hand_landmarks[16].y < hand_landmarks[14].y
        pinky_up = hand_landmarks[20].y < hand_landmarks[18].y
        
        main_fingers_up = sum([index_up, middle_up, ring_up, pinky_up])
        
        # 2. Advanced logic for Thumb
        thumb_tip = hand_landmarks[4]
        thumb_ip = hand_landmarks[3]
        index_mcp = hand_landmarks[5]
        pinky_mcp = hand_landmarks[17]
        
        hand_width = dist(index_mcp, pinky_mcp)
        
        # Thumb is considered 'out' open as a finger if the tip is extended far away from the index base knuckle
        thumb_distance = dist(thumb_tip, index_mcp)
        thumb_out = thumb_distance > (hand_width * 1.1)
        
        # Thumbs up gesture: Thumb tip is pointing vertically higher than the index base knuckle,
        # AND it is physically extended away from the hand (not tucked tightly in a fist)
        is_thumb_pointing_up = (thumb_tip.y < index_mcp.y) and (thumb_distance > hand_width * 0.8)
        
        if main_fingers_up == 0 and is_thumb_pointing_up:
            is_thumbs_up = True
            finger_count = -1 # strict gesture, not generic count
        else:
            finger_count = main_fingers_up + (1 if thumb_out else 0)
            if finger_count > 5: finger_count = 5
            
            # Check for Swipe Gestures (1 index finger extended horizontally)
            if main_fingers_up == 1 and index_up and not thumb_out:
                dx = hand_landmarks[8].x - hand_landmarks[5].x # index tip vs mcp
                dy = abs(hand_landmarks[8].y - hand_landmarks[5].y)
                
                # If pointing horizontally substantially more than vertically
                if abs(dx) > hand_width * 0.4 and abs(dx) > dy * 1.5:
                    if dx < 0: # Note: Flipped due to camera mirror effect
                        point_direction = 'right'
                    else:
                        point_direction = 'left'
            
    return finger_count, is_thumbs_up, point_direction
