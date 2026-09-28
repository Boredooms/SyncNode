"""Render public/og-image.svg (1200x630) to public/og-image.png using OpenCV."""
import cv2
import numpy as np
import re
import os

SVG_PATH = r"C:\syncnode\website\public\og-image.svg"
PNG_PATH = r"C:\syncnode\website\public\og-image.png"

W, H = 1200, 630

# Canvas: radial fog background (#161616 center → #060606 edges)
img = np.zeros((H, W, 3), dtype=np.float32)
cx, cy, r = W / 2, H * 0.38, W * 0.75
yy, xx = np.mgrid[0:H, 0:W]
d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
d = np.clip(d, 0, 1)
center = np.array([0x16, 0x16, 0x16], dtype=np.float32)
edge = np.array([0x06, 0x06, 0x06], dtype=np.float32)
# cv2 uses BGR — center/edge are grayscale so order is irrelevant
img = (center * (1 - d)[..., None] + edge * d[..., None]).astype(np.uint8)

def hex_to_bgr(h):
    h = h.lstrip("#")
    return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))  # RGB→BGR

def draw_text(text, size, color_hex, weight_cv, y, letter_spacing):
    """Draw letter-spaced text centered horizontally at baseline y."""
    font = cv2.FONT_HERSHEY_DUPLEX if weight_cv >= 600 else cv2.FONT_HERSHEY_PLAIN
    color = hex_to_bgr(color_hex)
    # measure width with spacing
    widths = []
    for ch in text:
        (tw, th), _ = cv2.getTextSize(ch, font, size, weight_cv)
        widths.append(tw)
    total_w = sum(widths) + letter_spacing * (len(text) - 1)
    x = (W - total_w) // 2
    for ch, tw in zip(text, widths):
        cv2.putText(img, ch, (x, y), font, size, color, weight_cv, cv2.LINE_AA)
        x += tw + letter_spacing
    return total_w

# Grid lines (#1B1B1B)
grid = hex_to_bgr("#1B1B1B")
cv2.line(img, (W // 2, 0), (W // 2, H), grid, 1)
cv2.line(img, (W // 4, 0), (W // 4, H), grid, 1)
cv2.line(img, (3 * W // 4, 0), (3 * W // 4, H), grid, 1)
cv2.line(img, (0, H // 2), (W, H // 2), grid, 1)

# Node ring at top center
cv2.circle(img, (W // 2, 112), 10, hex_to_bgr("#EDEDED"), 2, cv2.LINE_AA)

# Text (baseline y values from the SVG layout)
draw_text("SYNCNODE", 2.6, "#F2F2F2", 2, y=255, letter_spacing=26)
draw_text("THINK LOCALLY.", 1.35, "#9A9A9A", 1, y=360, letter_spacing=7)
draw_text("ACT INTELLIGENTLY.", 1.35, "#9A9A9A", 1, y=415, letter_spacing=7)
draw_text("SOVEREIGN LOCAL AI WORKBENCH", 0.72, "#565656", 1, y=540, letter_spacing=5)

cv2.imwrite(PNG_PATH, img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
print("wrote", PNG_PATH, os.path.getsize(PNG_PATH), "bytes")
