#!/usr/bin/env python3
"""
Build script: Package all premium tools into standalone EXEs.
Run on Windows with Python 3.12 + PyInstaller installed.
Usage: python build_tools.py
"""
import subprocess, os, sys

TOOLS = {
    "pdf_merge": "tools/pdf_merge.py",
    "video_to_mp3": "tools/video_to_mp3.py",
    "dupfinder": "tools/dupfinder.py",
    "img2pdf": "tools/img2pdf.py",
    "renamer": "tools/renamer.py",
    "csv_json": "tools/csv_json.py",
}

EXE_NAMES = {
    "pdf_merge": "PDF-Merger",
    "video_to_mp3": "Video-to-MP3",
    "dupfinder": "Duplicate-Finder",
    "img2pdf": "Image-to-PDF",
    "renamer": "Batch-Renamer",
    "csv_json": "CSV-JSON-Converter",
}

OUTPUT_DIR = "dist"

def build(name, script):
    exe_name = EXE_NAMES[name]
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--clean",
        "--name", exe_name,
        "--distpath", OUTPUT_DIR,
        "--workpath", f"build/{name}",
        "--specpath", f"build/{name}",
        script
    ]
    print(f"🔨 Building {exe_name}...")
    subprocess.run(cmd, check=True)
    size_mb = os.path.getsize(f"{OUTPUT_DIR}/{exe_name}.exe") / (1024*1024)
    print(f"   ✅ {exe_name}.exe ({size_mb:.1f} MB)")

if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for name, script in TOOLS.items():
        if not os.path.exists(script):
            print(f"⚠️  SKIP {name}: {script} not found")
            continue
        build(name, script)
    
    print(f"\n🎉 Done! EXE files in '{OUTPUT_DIR}/'")
    print("\n📦 To create bundle ZIP:")
    print(f"   python -c \"import shutil; shutil.make_archive('dist/SlowBuild-Toolbox', 'zip', '{OUTPUT_DIR}')\"")
