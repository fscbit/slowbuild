#!/usr/bin/env python3
"""
youtube_finder.py — 在 Win10 VM 上运行，自动查找中文歌的 YouTube 官方 MV
用法: python youtube_finder.py [--dry-run]
      python youtube_finder.py --song "光年之外" "G.E.M.邓紫棋"  # 单个查找
"""

import json, subprocess, sys, os, time, argparse

SONGS_FILE = os.path.join(os.path.dirname(__file__), "data", "songs.json")

def load_songs():
    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_songs(songs):
    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)

def search_youtube(query):
    """
    用 yt-dlp 搜索 YouTube，返回第一条结果的 video ID
    需要先安装: pip install yt-dlp
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "--get-id", "--no-playlist", "--flat-playlist",
             "--skip-download", f"ytsearch1:{query}"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            vid = result.stdout.strip().split("\n")[0]
            print(f"      找到: https://www.youtube.com/watch?v={vid}")
            return vid
        else:
            print(f"      未找到 ({result.stderr[:60]})")
            return None
    except FileNotFoundError:
        print("      ❌ yt-dlp 未安装，请先运行: pip install yt-dlp")
        return None
    except Exception as e:
        print(f"      ❌ 出错: {e}")
        return None

def find_single(title, artist):
    """查找单首歌"""
    query = f"{artist} {title} official MV"
    print(f"  搜索: {query}")
    return search_youtube(query)

def process_all(dry_run=False):
    """批量处理所有缺 YouTube ID 的歌"""
    songs = load_songs()
    missing = [s for s in songs if not s.get("youtube_id")]

    if not missing:
        print("✅ 所有歌曲都有 YouTube ID 了")
        return

    print(f"共 {len(missing)} 首缺 YouTube ID\n")
    found = 0

    for i, s in enumerate(missing):
        title = s.get("title_en") or s["title"]
        artist = s["artist"]
        query = f"{artist} {title}"
        print(f"[{i+1}/{len(missing)}] {artist} - {title}")

        vid = search_youtube(query)
        if not vid:
            # 试试加 "MV" 后缀
            vid = search_youtube(f"{artist} {title} MV")

        if vid:
            found += 1
            if not dry_run:
                s["youtube_id"] = vid
                save_songs(songs)
        else:
            print(f"      ⚠️  未找到，手动到后台添加")

        if (i + 1) % 5 == 0 and not dry_run:
            print(f"  --- 已保存 ({i+1}/{len(missing)}) ---")

        time.sleep(2)  # 避免太快被封

    if not dry_run:
        save_songs(songs)

    print(f"\n🎉 完成: 新找到 {found}/{len(missing)} 个 YouTube ID")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="自动查找中文歌曲 YouTube ID")
    parser.add_argument("--dry-run", action="store_true", help="只搜索不保存")
    parser.add_argument("--song", nargs=2, metavar=("TITLE", "ARTIST"),
                        help="查找单首歌")
    args = parser.parse_args()

    if args.song:
        title, artist = args.song
        vid = find_single(title, artist)
        if vid:
            print(f"\nYouTube ID: {vid}")
            print(f"视频链接: https://www.youtube.com/watch?v={vid}")
    else:
        process_all(dry_run=args.dry_run)
