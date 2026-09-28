"""Extract sample frames from every video in website/video/ for visual analysis."""
import cv2
import os

VIDEO_DIR = r"C:\syncnode\website\video"
OUT_DIR = r"C:\syncnode\website\frame_analysis"
os.makedirs(OUT_DIR, exist_ok=True)

files = [
    "Website main intro.mp4",
    "About the Project.mp4",
    "About the project 2.0.mp4",
    "Features.mp4",
    "Features2.0.mp4",
    "Prototype.mp4",
    "Prototype2.0.mp4",
]

for name in files:
    path = os.path.join(VIDEO_DIR, name)
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        print(f"FAILED to open: {name}")
        continue
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    dur = total / fps if fps else 0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"{name}: {w}x{h} @ {fps:.1f}fps, {dur:.1f}s ({total} frames)")

    # 8 evenly spaced sample frames
    safe = name.replace(" ", "_").replace(".mp4", "")
    for i in range(8):
        idx = int(total * (i + 0.5) / 8)
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ok, frame = cap.read()
        if ok:
            small = cv2.resize(frame, (640, 360))
            cv2.imwrite(os.path.join(OUT_DIR, f"{safe}_f{i}.jpg"), small, [cv2.IMWRITE_JPEG_QUALITY, 80])
    cap.release()
print("done")
