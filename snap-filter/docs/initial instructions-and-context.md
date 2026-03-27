# 📸 Snapchat-Style Filters with OpenCV (Python)

## 🧭 Project Overview

This project demonstrates a **real-time face filter system** similar to Snapchat using:

* **OpenCV** for video processing
* **Python** for logic
* **Basic image overlays (PNG with transparency)**

### 🎯 Goal

Build a lightweight, interactive application that:

* Detects faces from webcam feed
* Applies visual filters (glasses, ears, etc.)
* Runs in real time with minimal setup

> This is a **learning/demo project**, not production-grade software. Focus is on clarity, not robustness.

---

## ⚙️ Tech Stack

* Python 3.8+
* OpenCV (`cv2`)
* NumPy

---

## 📁 Step 1 — Create Project Structure

Run the following commands in your terminal:

```bash
mkdir snap-filters
cd snap-filters

# Core files
touch main.py face.py overlay.py requirements.txt README.md

# Assets
mkdir filters
mkdir screenshots

# Model
touch haarcascade.xml
```

---

## 📂 Final Structure

```
snap-filters/
│
├── main.py              # Entry point (camera + loop)
├── face.py              # Face detection logic
├── overlay.py           # Filter overlay logic
│
├── filters/             # PNG filters (transparent)
│   ├── glasses.png
│   ├── dog_ears.png
│   └── mustache.png
│
├── screenshots/         # Optional saved images
│
├── haarcascade.xml      # Face detection model
├── requirements.txt
└── README.md
```

---

## 📦 Step 2 — Install Dependencies

Create `requirements.txt`:

```
opencv-python
numpy
```

Install:

```bash
pip install -r requirements.txt
```

---

## 🧠 Step 3 — Core Components Breakdown

### 1. `main.py` (Controller)

Responsible for:

* Capturing webcam feed
* Handling keyboard input
* Calling detection + overlay modules
* Rendering output

---

### 2. `face.py` (Detection Layer)

Responsibilities:

* Load Haar cascade
* Convert frame to grayscale
* Detect faces

Expected output:

```python
[(x, y, w, h), ...]
```

---

### 3. `overlay.py` (Rendering Layer)

Responsibilities:

* Resize filter image based on face size
* Handle alpha channel blending
* Position filter correctly on face

---

## 🔁 Step 4 — Execution Flow

```
Camera Frame → Face Detection → Filter Selection → Overlay → Display
```

Per frame:

1. Capture frame
2. Detect faces
3. Choose active filter
4. Apply overlay
5. Display frame

---

## 🎮 Step 5 — Controls

| Key | Action          |
| --- | --------------- |
| 1   | Glasses         |
| 2   | Dog Ears        |
| 3   | Mustache        |
| 0   | No filter       |
| S   | Save screenshot |
| Q   | Quit            |

---

## 🖥️ Step 6 — Minimal UI Strategy

Use OpenCV text overlays:

```python
cv2.putText(frame, "1: Glasses | 2: Dog | 3: Mustache | Q: Quit",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
```

### Why this approach:

* Zero extra dependencies
* Keeps loop fast
* Ideal for demos

---

## 🧪 Step 7 — Core Learning Outcomes

By completing this project, you will understand:

* Real-time video processing
* Face detection fundamentals
* Image compositing (alpha blending)
* Frame-by-frame transformations
* Event-driven input handling

---

## 🚀 Step 8 — Feature Extensions (Next Iterations)

### 🟢 Level 1 (Easy Upgrades)

* Mirror flip (selfie mode)
* FPS counter
* Multiple face support
* Filter scaling improvements

---

### 🟡 Level 2 (Intermediate)

* Switch to MediaPipe Face Mesh
* Landmark-based positioning (eyes, nose, etc.)
* Better filter alignment

---

### 🔵 Level 3 (Advanced Demo)

* Gesture-based filter switching
* Emotion detection
* Background replacement
* Record video output

---

## 📱 Future Enhancement (Important Note)

You can later integrate:

* Phone camera as webcam (via DroidCam/IP stream)

No changes required in architecture — OpenCV treats it as a normal video source.

---

## 🧩 Design Philosophy

* Keep modules small and focused
* Avoid premature abstraction
* Prioritize visual output over edge-case handling
* Optimize for **clarity + demonstration**

---

## ⚠️ Common Pitfalls

* Not handling alpha channel → filters look broken
* High resolution → laggy performance
* Wrong filter positioning → misaligned overlays
* Camera index issues → no video feed

---

## ✅ Success Criteria

Your project is complete when:

* Webcam feed runs smoothly
* Face is detected reliably
* At least 2 filters work correctly
* Filters follow face in real time
* Keyboard switching works

---

## 📌 Notes for Antigravity IDE (Vibe Coding)

* Keep files small → easier for AI-assisted edits
* Work module-by-module:

  1. First detection
  2. Then overlay
  3. Then integration
* Test incrementally (don’t build everything at once)
* Use inline prints/logs for quick debugging

---

## 🏁 Final Thought

This project is less about complexity and more about:

> “Understanding how real-time computer vision systems are structured.”

Once this works, you have a solid base to build:

* AR filters
* AI camera apps
* Vision-based interfaces

---
