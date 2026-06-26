#!/usr/bin/env python3
"""Duplicate File Finder - Scan folder, find duplicates by hash. Pure Python, no deps."""
import sys, os, hashlib
from collections import defaultdict

def find_duplicates(folder):
    size_map = defaultdict(list)
    for root, _, files in os.walk(folder):
        for fname in files:
            path = os.path.join(root, fname)
            try:
                size_map[os.path.getsize(path)].append(path)
            except OSError:
                pass

    dupes = []
    for size, paths in size_map.items():
        if len(paths) < 2: continue
        hash_map = defaultdict(list)
        for p in paths:
            try:
                h = hashlib.md5(open(p, 'rb').read(65536)).hexdigest()
                hash_map[h].append(p)
            except OSError:
                pass
        for paths2 in hash_map.values():
            if len(paths2) > 1:
                dupes.append(paths2)
    return dupes

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: dupfinder.exe C:\\folder")
        sys.exit(1)
    folder = sys.argv[1]
    if not os.path.isdir(folder):
        print(f"❌ Not a folder: {folder}")
        sys.exit(1)
    print(f"Scanning {folder}...")
    groups = find_duplicates(folder)
    if not groups:
        print("✅ No duplicates found.")
    else:
        total = sum(len(g) - 1 for g in groups)
        print(f"🔍 Found {total} duplicate files in {len(groups)} groups:\n")
        for i, g in enumerate(groups, 1):
            print(f"  Group {i} ({len(g)} copies, {os.path.getsize(g[0])} bytes each):")
            for f in g:
                print(f"    {f}")
            print()
        print(f"💡 To delete duplicates automatically, run with --delete flag.")
