import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os

# Path to the face landmark detection model
MODEL_PATH = "face_landmarker.task"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading face landmark model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("Model downloaded.")

def load_face_mesh():
    """
    Initializes and returns the MediaPipe FaceLandmarker (Tasks API) for video stream mode.
    """
    ensure_model()
    
    base_options = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=False,
        num_faces=1,
        running_mode=vision.RunningMode.IMAGE
    )
    return vision.FaceLandmarker.create_from_options(options)

def detect_faces_full(frame, face_landmarker):
    """
    Processes the frame and returns the full results object containing landmarks and blendshapes.
    """
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    return face_landmarker.detect(mp_image)

def detect_faces(frame, face_landmarker):
    results = detect_faces_full(frame, face_landmarker)
    if results.face_landmarks:
        return results.face_landmarks
    return []

def get_face_signature(face_landmarks, iw, ih):
    import numpy as np
    l = face_landmarks
    
    # 20 incredibly stable 2D geometric anchor points
    anchors = [
        33, 263, 133, 362, 1, 168, 152, 132, 361, 234, 454,
        10, 46, 276, 61, 291, 0, 17, 64, 294
    ]
    
    # Map points to raw image pixel coordinates (ignoring Z to prevent fisheye perspective warping)
    pts = [(l[idx].x * iw, l[idx].y * ih) for idx in anchors]
    
    sig = []
    # Compute the precise 2D Euclidean distance between every single pair of the 20 points
    # (20 * 19) / 2 = 190 unique distances!
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = np.sqrt((pts[i][0] - pts[j][0])**2 + (pts[i][1] - pts[j][1])**2)
            sig.append(d)
            
    # L2-Normalize the 190-Dimensional array into a pure Mathematical Unit Vector
    sig = np.array(sig)
    norm = np.linalg.norm(sig)
    if norm == 0: return None
    return sig / norm
