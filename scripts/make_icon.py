"""
Generate icon.ico with a guaranteed 256x256 frame.
Uses PNG-compressed ICO format (Vista ICO) which electron-builder accepts.
Each size is saved as a separate PNG, then assembled into a proper ICO binary.
"""
import io
import struct
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).parents[1] / "frontend" / "electron" / "build" / "icon.ico"
OUT.parent.mkdir(parents=True, exist_ok=True)

SIZES = [16, 32, 48, 64, 128, 256]


def make_frame(size: int) -> bytes:
    """Render one icon frame and return as PNG bytes."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    pad = max(1, size // 12)
    radius = max(2, size // 6)
    d.rounded_rectangle(
        [pad, pad, size - pad - 1, size - pad - 1],
        radius=radius,
        fill=(12, 12, 14, 255),
    )

    # 'S' glyph
    w = int(size * 0.54)
    h = int(size * 0.60)
    x0 = (size - w) // 2
    y0 = (size - h) // 2
    bar = max(1, size // 14)
    mid = y0 + h // 2
    c = (255, 255, 255, 235)

    d.rectangle([x0,           y0,            x0 + w,     y0 + bar], fill=c)
    d.rectangle([x0,           mid,           x0 + w,     mid + bar], fill=c)
    d.rectangle([x0,           y0 + h - bar,  x0 + w,     y0 + h],   fill=c)
    d.rectangle([x0,           y0,            x0 + bar,   mid],       fill=c)
    d.rectangle([x0 + w - bar, mid,           x0 + w,     y0 + h],   fill=c)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# Render all frames
frames = [(size, make_frame(size)) for size in SIZES]

# Build ICO binary manually
# ICO header: 6 bytes
# Directory entries: 16 bytes × n
# Image data: concatenated

n = len(frames)
header = struct.pack("<HHH", 0, 1, n)  # reserved=0, type=1 (ICO), count=n

# Image data starts after header + directory
data_offset = 6 + 16 * n

entries = b""
image_data = b""

for size, png_bytes in frames:
    img_size = len(png_bytes)
    # Directory entry: width, height, colorcount, reserved, planes, bitcount, size, offset
    w = 0 if size == 256 else size   # 0 means 256 per ICO spec
    h = 0 if size == 256 else size
    entry = struct.pack(
        "<BBBBHHII",
        w, h,       # width, height (0 = 256)
        0,          # color count (0 = uses bit depth)
        0,          # reserved
        1,          # planes
        32,         # bit count (32-bit RGBA)
        img_size,   # size of image data
        data_offset + len(image_data),  # offset to image data
    )
    entries += entry
    image_data += png_bytes

ico_bytes = header + entries + image_data
OUT.write_bytes(ico_bytes)

# Verify with PIL
from PIL import Image as _I
ico = _I.open(str(OUT))
print(f"Written: {OUT}  ({len(ico_bytes):,} bytes)")
sizes_found = []
for i in range(n):
    try:
        ico.seek(i)
        sizes_found.append(ico.size)
    except EOFError:
        break
print(f"Frames: {sizes_found}")
assert (256, 256) in sizes_found, f"256x256 MISSING — {sizes_found}"
print("PASS — 256x256 confirmed")
