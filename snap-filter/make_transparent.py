import cv2
import numpy as np

def make_transparent(input_path, output_path):
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"Failed to load {input_path}")
        return
    
    # Ensure image has alpha channel
    if img.shape[2] == 3:
        b_channel, g_channel, r_channel = cv2.split(img)
        alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255
        img = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))
        
    # Find white pixels (approximate)
    white_threshold = 240
    white_pixels = (img[:, :, 0] > white_threshold) & \
                   (img[:, :, 1] > white_threshold) & \
                   (img[:, :, 2] > white_threshold)
                   
    img[white_pixels, 3] = 0 # Set alpha to 0 for white pixels
    
    cv2.imwrite(output_path, img)
    print(f"Saved {output_path}")

in_base = r"C:\Users\Arnav Patil\.gemini\antigravity\brain\8641c0c8-7aca-4f95-8706-345f73cde96d"
out_base = r"d:\value-added-program\snap-filter\filters"

make_transparent(fr"{in_base}\zombie_filter_1774593992929.png", fr"{out_base}\zombie.png")
make_transparent(fr"{in_base}\crown_filter_1774594122372.png", fr"{out_base}\crown.png")
make_transparent(fr"{in_base}\alien_filter_1774594149936.png", fr"{out_base}\alien.png")
