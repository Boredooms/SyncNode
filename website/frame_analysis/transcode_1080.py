"""
Re-encode the 4K (3840x2160) source videos to sharp, bandwidth-friendly
1080p H.264 for web delivery.

Why: the sources are 4K at a very low bitrate, so browsers downscaling them
to viewport size render soft (and cost 4x the bytes for no visible gain).
A true 1080p libx264 encode with high-quality settings looks sharper on
every device and roughly halves the payload.

Outputs (in website/public/videos/):
  <name> 1080p.mp4          — CRF 20, preset slow, faststart, no audio
  posters/<name>.jpg        — frame at 2.5 s, 1920px wide, q=5

Sources in website/video/ are never modified.

Run:  python website/frame_analysis/transcode_1080.py
"""

import os
import subprocess
import sys

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT, "video")
OUT_DIR = os.path.join(ROOT, "public", "videos")
POSTER_DIR = os.path.join(OUT_DIR, "posters")

CRF = "20"          # visually lossless for fog/gradient footage
PRESET = "slow"     # 10 s clips — quality over encode speed
FILES = [
    "Website main intro HD.mp4",   # high-quality 1080p master (replaces the old 4K cut)
    "About the Project.mp4",
    "About the project 2.0.mp4",
    "Features.mp4",
    "Features2.0.mp4",
    "Prototype.mp4",
    "Prototype2.0.mp4",
]


def out_name(src_name: str) -> str:
    stem = os.path.splitext(src_name)[0]
    return f"{stem} 1080p.mp4"


def probe(path: str) -> dict:
    """Minimal stream probe via `ffmpeg -i` stderr — ffprobe is unavailable."""
    r = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True)
    info = {"w": 0, "h": 0, "fps": 0.0, "duration": 0.0}
    for line in r.stderr.splitlines():
        line = line.strip()
        if "Video:" in line:
            for tok in line.split(","):
                tok = tok.strip()
                if "x" in tok and tok.split("x")[0].isdigit():
                    w, h = tok.split("x")[:2]
                    info["w"], info["h"] = int(w), int(h)
                elif tok.endswith("fps"):
                    try:
                        info["fps"] = float(tok.split()[0])
                    except ValueError:
                        pass
        if "Duration:" in line:
            try:
                hms = line.split("Duration:")[1].split(",")[0].strip()
                hh, mm, ss = hms.split(":")
                info["duration"] = int(hh) * 3600 + int(mm) * 60 + float(ss)
            except ValueError:
                pass
    return info


def transcode(src: str, dst: str) -> None:
    cmd = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", src,
        "-t", "10",
        "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
        "-c:v", "libx264", "-preset", PRESET, "-crf", CRF,
        "-profile:v", "high", "-level", "4.0",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        dst,
    ]
    subprocess.run(cmd, check=True)


def poster(src: str, dst: str) -> None:
    cmd = [
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "2.5", "-i", src,
        "-frames:v", "1",
        "-vf", "scale=1920:-2",
        "-q:v", "5",
        dst,
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    os.makedirs(POSTER_DIR, exist_ok=True)
    total_src = total_out = 0.0
    for name in FILES:
        src = os.path.join(SRC_DIR, name)
        if not os.path.exists(src):
            print(f"!! missing source: {src}")
            sys.exit(1)
        dst = os.path.join(OUT_DIR, out_name(name))
        info = probe(src)
        src_mb = os.path.getsize(src) / 1e6
        total_src += src_mb
        print(f"=== {name}  ({info['w']}x{info['h']} @ {info['fps']:.1f} fps, "
              f"{info['duration']:.1f}s, {src_mb:.1f} MB)")
        if os.path.exists(dst):
            print("   already encoded, skipping")
        else:
            transcode(src, dst)
        out_mb = os.path.getsize(dst) / 1e6 if os.path.exists(dst) else 0.0
        total_out += out_mb
        pdst = os.path.join(POSTER_DIR, os.path.splitext(name)[0] + ".jpg")
        if not os.path.exists(pdst):
            poster(src, pdst)
        print(f"   -> {out_name(name)}  {out_mb:.2f} MB  + poster {os.path.basename(pdst)}")

    print(f"\nTotal: {total_src:.1f} MB (4K source) -> {total_out:.1f} MB (1080p deliverables)")


if __name__ == "__main__":
    main()
