#!/usr/bin/env python3
"""Video to MP3 - Extract audio from any video file. Requires ffmpeg."""
import sys, os, subprocess

def video_to_mp3(video_path, output=None):
    if output is None:
        base = os.path.splitext(video_path)[0]
        output = base + ".mp3"
    cmd = ["ffmpeg", "-i", video_path, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", output, "-y"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"✅ Audio extracted → {output}")
    return output

if __name__ == "__main__":
    files = sys.argv[1:]
    if not files:
        print("Drag video files onto this EXE.")
        sys.exit(1)
    for f in files:
        if os.path.exists(f):
            video_to_mp3(f)
        else:
            print(f"⚠️  Not found: {f}")
