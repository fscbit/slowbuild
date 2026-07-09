#!/usr/bin/env python3
"""
youtube_finder.py — Win10 VM 自动查找中文歌 YouTube 视频链接
前提: Win10 能访问 YouTube（开VPN/代理），已安装 yt-dlp: pip install yt-dlp

用法:
  python youtube_finder.py              # 批量查找所有缺ID的歌
  python youtube_finder.py --dry-run    # 预览不保存
  python youtube_finder.py --recheck    # 重新查所有歌（覆盖已有ID）
  python youtube_finder.py --song "光年之外" "G.E.M.邓紫棋"  # 单首
"""

import json, subprocess, sys, os, time, argparse, re

SONGS_FILE = os.path.join(os.path.dirname(__file__), "data", "songs.json")

def load():
    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save(songs):
    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)


def search_one(query, timeout=12):
    """搜索一个查询，返回 (video_id, title) 或 (None, None)"""
    try:
        r = subprocess.run(
            ["yt-dlp", "--get-id", "--get-title", "--no-playlist",
             "--flat-playlist", "--skip-download", f"ytsearch1:{query}"],
            capture_output=True, text=True, timeout=timeout
        )
        if r.returncode == 0 and r.stdout.strip():
            lines = r.stdout.strip().split("\n")
            vid = lines[0].strip()
            title = lines[1].strip() if len(lines) > 1 else ""
            return vid, title
    except FileNotFoundError:
        print("      ❌ yt-dlp 未安装: pip install yt-dlp")
        return None, None
    except subprocess.TimeoutExpired:
        print("      ⏱️ 超时")
        return None, None
    except Exception as e:
        print(f"      ❌ {e}")
        return None, None
    return None, None


def find_best_match(artist, title_cn):
    """多策略搜索最佳 YouTube 视频"""
    title = title_cn  # 中文歌名

    # 策略1: 歌手 + 歌名 + official MV（最佳）
    for q in [
        f"{artist} {title} MV",
        f"{artist} {title} 官方MV",
        f"{artist} - {title} official",
        f"{artist} {title}",
    ]:
        vid, vtitle = search_one(q)
        if vid:
            # 检查相关性：歌名或歌手应出现在标题中
            artist_match = any(c in vtitle for c in artist[:2]) if len(artist) >= 2 else True
            title_match = title[:2] in vtitle if len(title) >= 2 else True
            if artist_match or title_match:
                return vid, vtitle, q
            else:
                print(f"      ⚠️ 跳过不相关: {vtitle[:50]}...")

    return None, None, ""


def process_all(dry_run=False, recheck=False):
    songs = load()

    if recheck:
        todo = songs  # 全部重查
    else:
        todo = [s for s in songs if not s.get("youtube_id")]

    if not todo:
        print("✅ 所有歌都有 YouTube ID")
        return

    print(f"{'🔁 重查' if recheck else '📺 查找'} {len(todo)} 首...\n")
    found, skipped = 0, 0
    t0 = time.time()

    for i, s in enumerate(todo):
        artist = s["artist"]
        title_cn = s["title"]
        print(f"[{i+1}/{len(todo)}] {artist} — {title_cn}")

        vid, vtitle, query = find_best_match(artist, title_cn)

        if vid:
            print(f"      ✅ {vtitle[:70]}")
            found += 1
            if not dry_run:
                s["youtube_id"] = vid
        else:
            print(f"      ❌ 未找到")
            skipped += 1

        if (i + 1) % 5 == 0 and not dry_run:
            save(songs)
            print(f"  ═══ 已保存 {i+1}/{len(todo)} ═══")

        time.sleep(2.5)  # 避免限速

    if not dry_run:
        save(songs)

    elapsed = int(time.time() - t0)
    print(f"\n🎉 完成 ({elapsed}s): 找到 {found} / 跳过 {skipped}")


def search_single(title, artist):
    print(f"🔍 {artist} — {title}")
    vid, vtitle, query = find_best_match(artist, title)
    if vid:
        print(f"\nQuery: 「{query}」")
        print(f"Title:  {vtitle}")
        print(f"ID:     {vid}")
        print(f"URL:    https://www.youtube.com/watch?v={vid}")
    else:
        print("❌ 未找到")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="自动查找中文歌曲 YouTube 视频")
    p.add_argument("--dry-run", action="store_true", help="只搜索不保存")
    p.add_argument("--recheck", action="store_true", help="重新查所有歌曲（覆盖已有ID）")
    p.add_argument("--song", nargs="+", help="单首查找: --song 歌名 歌手")
    args = p.parse_args()

    if args.song:
        if len(args.song) >= 2:
            search_single(" ".join(args.song[:-1]), args.song[-1])
        else:
            search_single(args.song[0], "")
    else:
        process_all(args.dry_run, args.recheck)
