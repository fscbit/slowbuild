#!/usr/bin/env python3
"""Image to PDF - Convert images to a single or multiple PDFs. Pure Python."""
import sys, os
try:
    from PIL import Image
except ImportError:
    print("Installing Pillow...")
    os.system(f"{sys.executable} -m pip install Pillow -q")
    from PIL import Image

def images_to_pdf(image_paths, output="output.pdf"):
    images = []
    for p in image_paths:
        if os.path.exists(p):
            img = Image.open(p).convert("RGB")
            images.append(img)
    if not images:
        print("❌ No valid images found.")
        return
    images[0].save(output, save_all=True, append_images=images[1:])
    print(f"✅ {len(images)} images → {output}")

if __name__ == "__main__":
    files = sys.argv[1:]
    if not files:
        print("Drag image files onto this EXE, or run: img2pdf.exe img1.jpg img2.png ...")
        sys.exit(1)
    images_to_pdf(files)
