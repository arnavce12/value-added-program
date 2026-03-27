<div align="center">

# 📸 Snapchat-Style AR Filters (Desktop)

[![Python Support](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MediaPipe](https://img.shields.io/badge/Powered%20By-MediaPipe-orange.svg)](https://mediapipe.dev/)
[![OpenCV](https://img.shields.io/badge/Powered%20By-OpenCV-green.svg)](https://opencv.org/)

---

### 🎭 Experience real-time filters with 3D tracking & gesture control!

---

## ✨ Features

**8 Dynamic Filters & Masks**
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

---

## 🖐️ Touchless Controls

**No mouse? No problem.**  
*Use your hands to navigate the experience.*

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
| **`app.py`** | 🖥️ Main Desktop GUI & Event Loop |
| **`face.py`** | 👤 MediaPipe Face Landmarking (v0.10+) |
| **`hand.py`** | ✋ Gestural Control & Swipe Detection |
| **`overlay.py`**| 🧊 3D Affine Warping & Blending |
| **`utils.py`** | 🌊 EMA Stabilization for Jitter Removal |

---

### *Created during the VAP as a demonstration of opencv and mediapipe.💫*

</div>
