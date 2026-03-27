import cv2
import numpy as np

def overlay_transparent(background, overlay, x, y, size=None, angle=0):
    """
    Overlays a transparent PNG onto a background with scaling and rotation.
    """
    img = overlay.copy()
    if size:
        img = cv2.resize(img, size)
    
    # Rotate the filter based on head tilt
    if angle != 0:
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1)
        img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))

    h, w = img.shape[:2]
    
    # Ensure overlay is within frame boundaries intelligently (handling partial out-of-bounds)
    y1, y2 = max(0, y), min(background.shape[0], y + h)
    x1, x2 = max(0, x), min(background.shape[1], x + w)
    
    y1o, y2o = max(0, -y), h - max(0, (y + h) - background.shape[0])
    x1o, x2o = max(0, -x), w - max(0, (x + w) - background.shape[1])
    
    if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
        return background

    overlay_img = img[y1o:y2o, x1o:x2o, :3]
    mask = img[y1o:y2o, x1o:x2o, 3:] / 255.0
    
    background[y1:y2, x1:x2] = (1.0 - mask) * background[y1:y2, x1:x2] + mask * overlay_img
    return background

def overlay_warped_mask(background, overlay, dst_pts, alpha_multiplier=1.0):
    """
    dst_pts: numpy array of 3 points (Left Eye, Right Eye, Chin) [[x,y], [x,y], [x,y]]
    alpha_multiplier: Opacity of the mask (e.g. 0.8 for 80% opacity)
    """
    h, w = overlay.shape[:2]
    # Source points matching standard generic face proportions of the PNGs
    src_pts = np.array([
        [w * 0.35, h * 0.45],   # Left Eye
        [w * 0.65, h * 0.45],   # Right Eye
        [w * 0.50, h * 0.90]    # Chin
    ], dtype=np.float32)
    
    # Get affine transform matrix
    M = cv2.getAffineTransform(src_pts, dst_pts.astype(np.float32))
    
    # Warp the overlay image to fit exactly onto the face coordinates
    warped_overlay = cv2.warpAffine(overlay, M, (background.shape[1], background.shape[0]), 
                                    flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))
    
    # Alpha Blending for the warped mask with variable transparency
    mask = (warped_overlay[:, :, 3:] / 255.0) * alpha_multiplier
    overlay_img = warped_overlay[:, :, :3]
    
    background = (1.0 - mask) * background + mask * overlay_img
    return background.astype(np.uint8)
