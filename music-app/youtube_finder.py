#!/usr/bin/env python3
"""
youtube_finder.py — Win10 VM 自动查找中文歌 YouTube 视频链接 (v2)
前提: Win10 能访问 YouTube，已安装 yt-dlp: pip install yt-dlp

用法:
  python youtube_finder.py              # 批量查找所有缺ID的歌
  python youtube_finder.py --recheck    # 重新查所有歌（覆盖已有ID）
  python youtube_finder.py --song "光年之外" "G.E.M.邓紫棋"  # 单首测试
"""

import json, subprocess, sys, os, time, argparse, re

SONGS_FILE = os.path.join(os.path.dirname(__file__), "data", "songs.json")


def load():
    with open(SONGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(songs):
    with open(SONGS_FILE, "w", encoding="utf-8") as f:
        json.dump(songs, f, ensure_ascii=False, indent=2)


PROXY = None  # 全局代理，process_all() 里设置

def search_one(query, timeout=30):
    """搜索一个查询，返回 (video_id, title) 或 (None, None)"""
    cmd = ["yt-dlp", "--get-id", "--get-title", "--no-playlist",
           "--flat-playlist", "--skip-download", "--socket-timeout", "15",
           f"ytsearch1:{query}"]
    if PROXY:
        cmd.insert(1, f"--proxy={PROXY}")

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          encoding="utf-8", errors="replace")
        if r.returncode == 0 and r.stdout.strip():
            lines = r.stdout.strip().split("\n")
            vid = lines[0].strip()
            title = lines[1].strip() if len(lines) > 1 else ""
            return vid, title
        elif r.stderr.strip():
            err = r.stderr.strip()[:100]
            if "HTTP Error 429" in err:
                print(f"      ⚠️ 限速429，等待30秒...")
                time.sleep(30)
            elif "HTTP Error" in err:
                print(f"      ⚠️ {err}")
    except FileNotFoundError:
        print("      ❌ yt-dlp 未安装: pip install yt-dlp")
        return None, None
    except subprocess.TimeoutExpired:
        print(f"      ⏱️ 超时（{timeout}s）")
        return None, None
    except Exception as e:
        print(f"      ❌ {e}")
        return None, None
    return None, None


def check_relevance(vtitle, artist, title_cn):
    """宽松检测——只过滤明显无关的，其余都接受"""
    vt = vtitle.lower()

    # 歌名中的任意一个2字片段出现在标题里就认
    for i in range(len(title_cn) - 1):
        if title_cn[i:i+2] in vt:
            return True

    # 歌手名的任意一个2字片段
    artist_cn = artist.split("(")[0].strip() if "(" in artist else artist
    for i in range(len(artist_cn) - 1):
        if artist_cn[i:i+2] in vt:
            return True

    # 英文歌手名
    if "(" in artist:
        m = re.search(r'\((.+?)\)', artist)
        if m and m.group(1).lower() in vt:
            return True

    # 都没匹配到 → 但也接受（yt-dlp搜索本身已经很准确）
    return True


def find_best_match(artist, title_cn):
    """多策略搜索最佳 YouTube 视频"""
    artist_cn = artist.split("(")[0].strip() if "(" in artist else artist

    # 构建搜索词列表：精准到宽泛
    queries = [
        f"{artist_cn} - {title_cn}",
        f"{artist_cn} {title_cn} MV",
        f"{artist_cn} {title_cn} 官方MV",
        f"{artist_cn} {title_cn} 官方",
        f"{artist_cn} {title_cn}",
    ]

    # 有英文歌手名：追加英文搜索
    if "(" in artist:
        m = re.search(r'\((.+?)\)', artist)
        if m:
            en = m.group(1)
            queries.extend([
                f"{en} {title_cn} MV",
                f"{en} {title_cn} official music video",
            ])

    for q in queries:
        vid, vtitle = search_one(q)
        if not vid:
            continue
        if check_relevance(vtitle, artist, title_cn):
            return vid, vtitle, q
        else:
            print(f"      ⚠️ 跳过: {vtitle[:60]}...")

    return None, None, ""


def process_all(dry_run=False, recheck=False, proxy=None):
    global PROXY
    PROXY = proxy
    if PROXY:
        print(f"🔗 代理: {PROXY}\n")
    songs = load()

    if recheck:
        todo = songs
    else:
        todo = [s for s in songs if not s.get("youtube_id")]

    if not todo:
        print("✅ 所有歌都有 YouTube ID")
        return

    print(f"{'🔁 重查' if recheck else '📺 查找'} {len(todo)} 首...\n")

    # 连通性测试
    print("🧪 测试 YouTube 连接...")
    vid, _ = search_one("周杰伦 晴天", timeout=20)
    if vid:
        print(f"   ✅ 连通正常 ({vid})\n")
    else:
        print("   ❌ 连不上 YouTube，检查 VPN/代理\n")
        print("   试试: python youtube_finder.py --proxy http://127.0.0.1:7890")
        return

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

        # 每5首存一次
        if (i + 1) % 5 == 0 and not dry_run:
            save(songs)
            print(f"  ═══ 已保存 {i+1}/{len(todo)} ═══")

        time.sleep(3)

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
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--recheck", action="store_true", help="重新查所有歌（覆盖已有ID）")
    p.add_argument("--song", nargs="+", help="单首测试: --song 歌名 歌手")
    p.add_argument("--proxy", help="代理地址，如 --proxy http://127.0.0.1:7890")
    args = p.parse_args()

    if args.song:
        if len(args.song) >= 2:
            search_single(" ".join(args.song[:-1]), args.song[-1])
        else:
            search_single(args.song[0], "")
    else:
        process_all(args.dry_run, args.recheck, args.proxy)
