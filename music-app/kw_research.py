#!/usr/bin/env python3
"""
kw_research.py — Win10 上运行，挖掘老外搜索中文歌的真实关键词
用途：Google 搜索建议 → 找到长尾关键词 → 指导网站内容选择

用法:
  python kw_research.py
  python kw_research.py --song "光年之外"
"""

import json, urllib.request, urllib.parse, sys, argparse

GOOGLE_SUGGEST = "https://suggestqueries.google.com/complete/search?client=firefox&q="

# 老外搜中文歌的核心查询模板
QUERY_TEMPLATES = [
    "Chinese song {} meaning",
    "{} lyrics translation English",
    "{} Chinese song explained",
    "what is {} about Chinese song",
    "{} English subtitles",
    "Chinese TikTok song {}",
    "{} song meaning in English",
    "viral Chinese song {}",
]

def fetch_suggestions(query):
    """获取 Google 搜索建议"""
    url = GOOGLE_SUGGEST + urllib.parse.quote(query)
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read().decode("utf-8"))
        return data[1] if len(data) > 1 else []
    except Exception as e:
        print(f"  ⚠️ 查询失败: {e}")
        return []

def research_song(title, title_en="", artist=""):
    """研究单首歌的关键词潜力"""
    print(f"\n{'='*50}")
    print(f"🎵 {title} — {artist}")
    print(f"{'='*50}")

    all_keywords = []

    # 用英文标题搜
    search_term = title_en or title
    for tmpl in QUERY_TEMPLATES:
        query = tmpl.format(search_term)
        suggestions = fetch_suggestions(query)
        if suggestions:
            for s in suggestions:
                if s not in all_keywords:
                    all_keywords.append(s)
                    print(f"  🔍 {s}")

    # 直接用中文搜（有些老外会用拼音）
    if any('\u4e00' <= c <= '\u9fff' for c in title):
        suggestions = fetch_suggestions(f"{title} lyrics")
        for s in suggestions:
            if s not in all_keywords:
                all_keywords.append(s)
                print(f"  🔍 {s}")

    # 歌手名联表
    if artist:
        suggestions = fetch_suggestions(f"{artist} song explained")
        for s in suggestions[:5]:
            if s not in all_keywords:
                all_keywords.append(s)
                print(f"  🔍 {s}")

    return all_keywords

def research_all():
    """批量研究所有中文歌"""
    songs = json.load(open("data/songs.json", "r", encoding="utf-8"))
    cn_songs = [s for s in songs if s.get("language", "zh") == "zh"][:20]  # 先研究前20首

    print(f"研究 {len(cn_songs)} 首中文歌的关键词潜力...\n")
    total_kw = 0

    for s in cn_songs:
        kws = research_song(s["title"], s.get("title_en", ""), s["artist"])
        total_kw += len(kws)
        print(f"  → {len(kws)} 个关键词")

    print(f"\n{'='*50}")
    print(f"总计发现 {total_kw} 个潜在搜索关键词")
    print(f"用这些关键词优化 title_en / review_en 字段可大幅提升 SEO")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="中文歌英文关键词调研")
    p.add_argument("--song", type=str, help="研究单首歌")
    p.add_argument("--artist", type=str, default="")
    p.add_argument("--title-en", type=str, default="")
    args = p.parse_args()

    if args.song:
        research_song(args.song, args.title_en, args.artist)
    else:
        research_all()
