import cv2
import os
import time
import tkinter as tk
from collections import Counter
import numpy as np
from PIL import Image, ImageTk

import face
import hand
import overlay
from utils import Stabilizer

class FilterApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        
        print("Initializing Snapchat-style filters (MediaPipe 3D)...")
        self.face_mesh = face.load_face_mesh()
        
        self.filter_paths = {
            '0': None,
            '1': 'filters/glasses.png',
            '2': 'filters/dog_ears.png',
            '3': 'filters/mustache.png',
            '4': 'filters/joker.png',
            '5': 'filters/mask.png',
            '6': 'filters/zombie.png',
            '7': 'filters/crown.png',
            '8': 'filters/alien.png'
        }
        self.filter_keys_ordered = list(self.filter_paths.keys())
        
        self.filters = {}
        for key, path in self.filter_paths.items():
            if path is None:
                continue
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is not None:
                self.filters[key] = img
            else:
                print(f"Warning: Could not load filter '{path}'")
                
        self.active_filter_key = '0'
        
        self.cap = cv2.VideoCapture(0)
        self.width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        # Build UI layout
        self.build_ui()
        
        os.makedirs('screenshots', exist_ok=True)
        self.shot_count = 0
        self.last_shot_time = 0
        self.flash_end_time = 0
        
        self.finger_buffer = []
        self.last_filter_switch_time = 0
        self.last_swipe_time = 0
        
        self.stable_pos = Stabilizer(alpha=0.7)
        self.stable_size = Stabilizer(alpha=0.7)
        self.stable_angle = Stabilizer(alpha=0.7)
        self.stable_warppts = Stabilizer(alpha=0.8)
        self.last_tracked_filter = self.active_filter_key

        self.delay = 15 # ms delay for update loop
        self.update_background_color()
        self.update()
        
    def build_ui(self):
        # Header
        self.header = tk.Label(self.window, text="Snap Filters Desktop", font=("Segoe UI", 18, "bold"), fg="#FFFFFF")
        self.header.pack(pady=10)
        
        # Canvas
        self.canvas = tk.Canvas(self.window, width=self.width, height=self.height, bg="#000000", highlightthickness=0)
        self.canvas.pack(padx=20, pady=10)
        
        # Controls Frame
        self.ctrl_frame = tk.Frame(self.window)
        self.ctrl_frame.pack(fill=tk.X, pady=10)
        
        self.btn_capture = tk.Button(self.ctrl_frame, text="📸 Capture Photo", command=self.take_screenshot, font=("Segoe UI", 12), bg="#444444", fg="white", activebackground="#666666", activeforeground="white", relief=tk.FLAT, padx=20, pady=5)
        self.btn_capture.pack()
        self.btn_capture.bind("<Enter>", lambda e: self.btn_capture.config(bg="#555555"))
        self.btn_capture.bind("<Leave>", lambda e: self.btn_capture.config(bg="#444444"))
        
        # Carousel Frame
        self.carousel = tk.Frame(self.window, pady=15)
        self.carousel.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.thumbnail_images = {}
        self.buttons = {}
        
        def create_hover_bindings(b, k):
            b.bind("<Enter>", lambda e: b.config(bg="#4a4a4a") if self.active_filter_key != k else None)
            b.bind("<Leave>", lambda e: b.config(bg="#2a2a2a") if self.active_filter_key != k else None)

        # Add a placeholder "No Filter" button
        b0 = tk.Button(self.carousel, text="🚫", font=("Segoe UI", 20), bg="#2a2a2a", fg="white", relief=tk.FLAT, width=3, height=1, command=lambda k='0': self.set_filter(k))
        b0.pack(side=tk.LEFT, padx=10, expand=True)
        self.buttons['0'] = b0
        create_hover_bindings(b0, '0')
        
        for key, path in self.filter_paths.items():
            if path is None: continue
            
            # Create thumbnail
            pil_img = Image.open(path).convert("RGBA")
            pil_img.thumbnail((50, 50))
            
            # Create background layer for transparent icons
            bg = Image.new("RGBA", pil_img.size, (42, 42, 42, 255))
            composite = Image.alpha_composite(bg, pil_img)
            
            photo = ImageTk.PhotoImage(composite)
            self.thumbnail_images[key] = photo # keep reference
            
            btn = tk.Button(self.carousel, image=photo, bg="#2a2a2a", relief=tk.FLAT, command=lambda k=key: self.set_filter(k))
            btn.pack(side=tk.LEFT, padx=10, expand=True)
            self.buttons[key] = btn
            create_hover_bindings(btn, key)
            
        self.update_button_colors()
            
    def set_filter(self, key):
        self.active_filter_key = key
        self.update_button_colors()
        
    def update_button_colors(self):
        for k, btn in self.buttons.items():
            if k == self.active_filter_key:
                btn.config(bg="#00ff88") # Minimalist neon green active highlight
            else:
                btn.config(bg="#2a2a2a")
                
    def take_screenshot(self):
        self.force_screenshot = True
        
    def update_background_color(self):
        # Deep neon RGB breathing animation
        t = time.time()
        r = int(18 + 10 * np.sin(t * 0.5))
        g = int(18 + 10 * np.sin(t * 0.7))
        b = int(28 + 15 * np.sin(t * 0.3))
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        
        self.window.configure(bg=hex_color)
        self.header.configure(bg=hex_color)
        self.ctrl_frame.configure(bg=hex_color)
        self.carousel.configure(bg=hex_color)
        
        self.window.after(50, self.update_background_color)
        
    def update(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            ih, iw, _ = frame.shape
            
            current_time = time.time()
            if hasattr(self, 'force_screenshot') and self.force_screenshot:
                is_thumbs_up = True
                self.force_screenshot = False
                finger_count = -1
                point_direction = None
            else:
                finger_count, is_thumbs_up, point_direction = hand.analyze_hand(frame)
            
            if self.active_filter_key != self.last_tracked_filter:
                self.stable_pos.reset()
                self.stable_size.reset()
                self.stable_angle.reset()
                self.stable_warppts.reset()
                self.last_tracked_filter = self.active_filter_key
                
            # Swipe gesture implementation
            if point_direction and current_time - self.last_swipe_time > 2.0:
                idx = self.filter_keys_ordered.index(self.active_filter_key)
                if point_direction == 'right':
                    next_idx = (idx + 1) % len(self.filter_keys_ordered)
                    self.set_filter(self.filter_keys_ordered[next_idx])
                    print(f"Hand Swipe: RIGHT -> Filter {self.active_filter_key}")
                elif point_direction == 'left':
                    prev_idx = (idx - 1) % len(self.filter_keys_ordered)
                    self.set_filter(self.filter_keys_ordered[prev_idx])
                    print(f"Hand Swipe: LEFT -> Filter {self.active_filter_key}")
                self.last_swipe_time = current_time
                self.finger_buffer.clear()
            # Standard finger count switching (Lock out numeric switching just after a swipe)
            elif finger_count != -1 and not point_direction and current_time - self.last_swipe_time > 2.0:
                self.finger_buffer.append(finger_count)
                if len(self.finger_buffer) > 7: 
                    self.finger_buffer.pop(0)
                most_common = Counter(self.finger_buffer).most_common(1)[0][0]
                
                if current_time - self.last_filter_switch_time > 0.4:
                    if str(most_common) in self.filter_paths.keys() and int(most_common) <= 5:
                        if self.active_filter_key != str(most_common):
                            self.set_filter(str(most_common))
                            print(f"Hand Gesture: Switched to filter {self.active_filter_key}")
                            self.last_filter_switch_time = current_time
                            self.finger_buffer.clear()
                            
            if is_thumbs_up and current_time - self.last_shot_time > 1.5:
                file_name = f"screenshots/screenshot_{self.shot_count}.jpg"
                cv2.imwrite(file_name, frame)
                print(f"Thumbs Up! Saved {file_name}")
                self.shot_count += 1
                self.last_shot_time = current_time
                self.flash_end_time = current_time + 1.0
                
            multi_face_landmarks = face.detect_faces(frame, self.face_mesh)
            
            if self.active_filter_key != '0' and self.active_filter_key in self.filters and multi_face_landmarks:
                filter_img = self.filters[self.active_filter_key]
                k = self.active_filter_key
                
                for face_landmarks in multi_face_landmarks:
                    left_eye = face_landmarks[33]
                    right_eye = face_landmarks[263]
                    forehead = face_landmarks[10]
                    lip_top = face_landmarks[164]
                    chin = face_landmarks[152]
                    left_cheek = face_landmarks[234]
                    right_cheek = face_landmarks[454]
                    
                    eye_dx = (right_eye.x - left_eye.x) * iw
                    eye_dy = (right_eye.y - left_eye.y) * ih
                    eye_dz = (right_eye.z - left_eye.z) * iw
                    eye_dist_3d = np.sqrt(eye_dx**2 + eye_dy**2 + eye_dz**2)
                    
                    face_dx = (right_cheek.x - left_cheek.x) * iw
                    face_dy = (right_cheek.y - left_cheek.y) * ih
                    face_dz = (right_cheek.z - left_cheek.z) * iw
                    face_width_3d = np.sqrt(face_dx**2 + face_dy**2 + face_dz**2)
                    
                    face_hx = (chin.x - forehead.x) * iw
                    face_hy = (chin.y - forehead.y) * ih
                    face_hz = (chin.z - forehead.z) * iw
                    face_height_3d = np.sqrt(face_hx**2 + face_hy**2 + face_hz**2)
                    
                    raw_angle = -np.degrees(np.arctan2(eye_dy, eye_dx))
                    angle = self.stable_angle.update(raw_angle)
                    
                    if k in ('4', '5', '6', '8'):
                        raw_pts = np.array([
                            [left_eye.x * iw, left_eye.y * ih],
                            [right_eye.x * iw, right_eye.y * ih],
                            [chin.x * iw, chin.y * ih]
                        ])
                        flat_pts = tuple(raw_pts.flatten())
                        smoothed_flat = self.stable_warppts.update(flat_pts)
                        smoothed_pts = np.array(smoothed_flat).reshape(3, 2)
                        
                        alpha = 0.8 if k in ('4', '5') else 1.0
                        frame = overlay.overlay_warped_mask(frame, filter_img, smoothed_pts, alpha_multiplier=alpha)
                    else:
                        if k == '1': # Glasses
                            raw_w = eye_dist_3d * 2.0
                            raw_cx = (left_eye.x + right_eye.x) / 2 * iw
                            raw_cy = (left_eye.y + right_eye.y) / 2 * ih
                        elif k == '2': # Dog Ears
                            raw_w = face_width_3d * 1.5
                            raw_cx = forehead.x * iw
                            raw_cy = forehead.y * ih - face_height_3d * 0.25
                        elif k == '3': # Mustache
                            raw_w = eye_dist_3d * 1.5
                            raw_cx = lip_top.x * iw
                            raw_cy = lip_top.y * ih
                        elif k == '7': # Crown
                            raw_w = face_width_3d * 1.3
                            raw_cx = forehead.x * iw
                            raw_cy = forehead.y * ih - face_height_3d * 0.45
                            
                        smoothed_cx, smoothed_cy = self.stable_pos.update((raw_cx, raw_cy))
                        filter_width = int(self.stable_size.update(raw_w))
                        filter_height = int(filter_width * (filter_img.shape[0] / filter_img.shape[1]))
                        
                        pos_x = int(smoothed_cx - (filter_width / 2))
                        pos_y = int(smoothed_cy - (filter_height / 2))
                        
                        frame = overlay.overlay_transparent(frame, filter_img, pos_x, pos_y, (filter_width, filter_height), angle)

            if current_time < self.flash_end_time:
                cv2.putText(frame, "SAVED!", (iw//2 - 80, ih//2), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

            # Convert BGR to RGB, then to PIL Image, then to ImageTk
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
            
        self.window.after(self.delay, self.update)

if __name__ == "__main__":
    root = tk.Tk()
    app = FilterApp(root, "Snap Filters Desktop")
    root.mainloop()
