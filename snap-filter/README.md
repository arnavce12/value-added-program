<div align="center">

# 📸 Smart AI Vision & AR Filters (Desktop)

[![Python Support](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MediaPipe](https://img.shields.io/badge/Powered%20By-MediaPipe-orange.svg)](https://mediapipe.dev/)
[![OpenCV](https://img.shields.io/badge/Powered%20By-OpenCV-green.svg)](https://opencv.org/)

---

### 🎭 A Dual-Mode Application for 3D AR Filters and Smart Facial Recognition!

---

## ✨ Features

The application now supports a full **Multi-Tab UI** powered by Tkinter, allowing users to seamlessly switch between two distinct vision modes:

### 1. 🎭 AR Filters Mode
Experience real-time filters with 3D tracking & gesture control!
| Filter | Description | Type |
| :---: | :---: | :---: |
| 👓 | Classic Aviator Glasses | 3D Static |
| 🐶 | Cute Dog Ears | 3D Static |
| 👨‍💼 | Stylized Mustache | 3D Static |
| 🤡 | Joker Face | 3D Warped |
| 🎭 | Anonymous Mask | 3D Warped |
| 🧟 | Photo-Realistic Zombie | Full Opaque |
| 👑 | King's Royal Crown | 3D Static |
| 👽 | Green Alien Mask | 3D Warped |

### 2. 🧠 Smart Scanner Mode (Identity & Emotion)
A futuristic HUD overlay running a custom mathematical face-scanning engine.
- **Micro-Expression Detection**: Actively reads facial expressions (Happy, Sad, Angry, Surprised) in real-time.
- **Identity Recognition**: Maps a 190-Dimensional geometric web across your face to verify your identity against a reference photo (`filters/arnav.jpg`).
- **Age/Gender Simulation**: Heuristic-based demographic overlays.

> **Note on Recognition Accuracy (~0.7)**: Because Python 3.14 does not currently support heavy ML libraries like TensorFlow or PyTorch, this scanner uses a custom 190-D Euclidean distance mapping algorithm rather than Deep Neural Network Embeddings (like FaceNet). As a result, tracking accuracy is around `0.7` and can trigger false positives on similar facial bone structures. For production use on standard Python versions, this logic can be completely revamped/replaced with the `deepface` library.

---

## 🖐️ Touchless Controls

**No mouse? No problem.**  
*Use your hands to navigate the AR experience.*

| Gesture | Action |
| :---: | :--- |
| ✋ `1-5 Fingers` | **Jump** directly to filters 1–5 |
| ✊ `Fist (0)` | **Clear** current filter |
| 👆 `Point Right` | **Next** filter in carousel |
| 👈 `Point Left` | **Previous** filter in carousel |
| 👍 `Thumbs Up` | **Screenshot** (saves to `screenshots/`) |

---

## 🛠️ Ready to Play?

### 1. 📥 Installation
```bash
git clone <your-repo-url>
cd snap-filter
pip install -r requirements.txt
```

### 2. 🚀 Launch App
```bash
python app.py
```

---

## 📂 Under the Hood

| Module | Responsibility |
| :--- | :--- |
| **`app.py`** | 🖥️ Main Desktop GUI, Tab Navigation & Event Loop |
| **`face.py`** | 👤 MediaPipe Face Landmarking & Native 190-D Identity Algorithms |
| **`hand.py`** | ✋ Gestural Control & Swipe Detection |
| **`overlay.py`**| 🧊 3D Affine Warping & Blending |
| **`utils.py`** | 🌊 EMA Stabilization for Jitter Removal |

---

### *Created during the VAP as a demonstration of opencv and mediapipe.💫*

</div>
