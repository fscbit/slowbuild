#!/usr/bin/env python3
"""PDF Merger - Merge multiple PDFs into one. Requires PyPDF2."""
import sys, os
try:
    from PyPDF2 import PdfMerger
except ImportError:
    print("Installing PyPDF2...")
    os.system(f"{sys.executable} -m pip install PyPDF2 -q")
    from PyPDF2 import PdfMerger

def merge_pdfs(file_list, output="merged.pdf"):
    merger = PdfMerger()
    for f in file_list:
        if os.path.exists(f):
            merger.append(f)
        else:
            print(f"⚠️  Skipping missing: {f}")
    merger.write(output)
    merger.close()
    print(f"✅ Merged {len(file_list)} files → {output}")
    return output

if __name__ == "__main__":
    files = sys.argv[1:]
    if not files:
        print("Drag PDF files onto this EXE, or run: pdf_merge.exe file1.pdf file2.pdf ...")
        sys.exit(1)
    merge_pdfs(files)
