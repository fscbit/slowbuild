#!/usr/bin/env python3
"""Batch File Renamer - Rename files with find & replace, numbering, etc."""
import sys, os, re

def batch_rename(folder, pattern, replacement, dry_run=True):
    files = sorted(os.listdir(folder))
    renamed = 0
    for old in files:
        new = re.sub(pattern, replacement, old) if pattern else old
        if new == old:
            continue
        old_path = os.path.join(folder, old)
        new_path = os.path.join(folder, new)
        if os.path.exists(new_path):
            print(f"⚠️  Skip (exists): {old} → {new}")
            continue
        if dry_run:
            print(f"  {old} → {new}")
        else:
            os.rename(old_path, new_path)
            print(f"✅ {old} → {new}")
        renamed += 1
    action = "Would rename" if dry_run else "Renamed"
    print(f"\n{action} {renamed} files.")
    if dry_run and renamed:
        print("💡 Add --go to actually rename.")

if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run = True
    if "--go" in args:
        args.remove("--go")
        dry_run = False
    
    if len(args) < 1:
        print("Batch File Renamer")
        print("  Usage: renamer.exe C:\\folder find_pattern replace_pattern")
        print("  Add --go to actually rename (default: preview only)")
        print("  Example: renamer.exe . 'IMG_' ''   → removes IMG_ prefix")
        sys.exit(1)
    
    folder = args[0]
    pattern = args[1] if len(args) > 1 else ""
    replacement = args[2] if len(args) > 2 else ""
    
    if not os.path.isdir(folder):
        print(f"❌ Not a folder: {folder}")
        sys.exit(1)
    
    batch_rename(folder, pattern, replacement, dry_run)
