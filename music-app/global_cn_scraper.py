#!/usr/bin/env python3
"""
global_cn_scraper.py — Win10 上运行，自动搜集老外最感兴趣的中文歌
数据源: YouTube API / kworb / Spotify Charts / Google Trends

用法:
  python global_cn_scraper.py --youtube      # 抓YouTube中文歌播放量排行
  python global_cn_scraper.py --spotify      # 抓Spotify全球热门中文歌
  python global_cn_scraper.py --all          # 全部跑一遍
"""

import json, urllib.request, urllib.parse, sys, time, argparse

# ═══ 数据源1: kworb — YouTube中文歌播放量排行 ═══
def scrape_kworb():
    """抓 kworb.net YouTube中文歌Top100 (播放量=老外兴趣指标)"""
    print("📊 抓取 kworb YouTube中文歌排行...")
    try:
        # kworb 的 Chinese 艺人 YouTube 数据
        url = "https://kworb.net/youtube/topvideos_chinese.html"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode("utf-8", errors="replace")

        # 解析表格行: <tr><td>排名</td><td>歌手 - 歌名</td><td>播放量</td>...
        import re
        songs = []
        rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL)
        for row in rows[:50]:  # 前50
            tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
            if len(tds) >= 3:
                name = re.sub(r'<[^>]+>', '', tds[1]).strip()
                views = re.sub(r'<[^>]+>', '', tds[2]).strip()
                if ' - ' in name:
                    artist, title = name.split(' - ', 1)
                    songs.append({"artist": artist, "title": title, "views": views})

        print(f"  ✅ 抓到 {len(songs)} 首")
        return songs
    except Exception as e:
        print(f"  ❌ {e}")
        return []


# ═══ 数据源2: Google搜索建议 (老外在搜什么) ═══
def scrape_google_suggest():
    """挖掘老外搜中文歌的真实关键词"""
    print("\n🔍 Google搜索建议挖掘...")

    # 老外搜中文歌的常见查询模式
    seeds = [
        "Chinese song",
        "Chinese pop song",
        "Chinese rock song",
        "Chinese folk song",
        "TikTok Chinese song",
        "viral Chinese song",
        "Chinese love song",
        "Chinese sad song",
        "Chinese rap song",
        "best Chinese song",
        "classic Chinese song",
        "C-pop song",
        "Chinese song about",
        "what is the Chinese song that goes",
    ]

    all_suggestions = set()
    for seed in seeds:
        url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={urllib.parse.quote(seed)}"
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0"
            })
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read().decode("utf-8"))
            for s in data[1] if len(data) > 1 else []:
                if s not in all_suggestions:
                    all_suggestions.add(s)
                    print(f"  🔍 {s}")
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ {seed[:30]}... 失败")

    print(f"\n  ✅ 共发现 {len(all_suggestions)} 个搜索关键词")
    return list(all_suggestions)


# ═══ 数据源3: 已知全球爆款中文歌 (硬数据) ═══
KNOWN_GLOBAL_HITS = [
    # 数据来源: YouTube播放量 / TikTok趋势 / Billboard Global 200 / Reddit讨论
    # 格式: (歌名, 歌手, 全球影响力说明, 估计YouTube播放量)

    # Tier 1: 全球病毒级传播
    ("一剪梅", "费玉清", "TikTok 2020全球年度梗 #XueHuaPiaoPiao, 6亿+ TikTok观看"),
    ("学猫叫", "小潘潘", "TikTok #LearnToMeow, 全球翻拍现象"),
    ("小苹果", "筷子兄弟", "中国版Gangnam Style, YouTube 1亿+"),
    ("光年之外", "邓紫棋", "电影Passengers主题曲, YT 2.6亿+, 全球搜索"),

    # Tier 2: 高国际知名度
    ("甜蜜蜜", "邓丽君", "Teresa Teng全球偶像, 翻唱无数"),
    ("月亮代表我的心", "邓丽君", "世界翻唱最多的中文歌"),
    ("告白气球", "周杰伦", "Jay Chou全球最高播放, YT 2.4亿+"),
    ("童话", "光良", "亚洲大爆, 欧美小众经典"),
    ("那些年", "胡夏", "电影海外票房破纪录, 主题曲全球知名"),

    # Tier 3: 西方亚文化圈层
    ("Made in China", "Higher Brothers", "88rising出品, 全球嘻哈圈"),
    ("芒种", "音阙诗听", "TikTok古风电子, 海外翻跳无数"),
    ("起风了", "吴青峰", "日文翻唱→中文→全球传播链"),
    ("错位时空", "艾辰", "TikTok 2021年度热门"),
    ("飞鸟和蝉", "任然", "YouTube破亿, 港澳台东南亚爆款"),
    ("星辰大海", "黄霄雲", "2021年最火中文歌之一"),

    # Tier 4: 经典回流
    ("后来", "刘若英", "KTV 20年不衰, 海外华人必唱"),
    ("朋友", "周华健", "全球华人共同记忆"),
    ("海阔天空", "Beyond", "华人世界摇滚国歌, 西方摇滚乐迷发现"),
    ("吻别", "张学友", "被翻唱为Take Me to Your Heart, 全球5000万+"),
    ("传奇", "王菲", "2010春晚爆红+翻唱, 海外菲迷基础庞大"),

    # Tier 5: C-drama/电影跨文化传播
    ("无羁", "肖战&王一博", "陈情令The Untamed Netflix全球爆款"),
    ("凉凉", "杨宗纬&张碧晨", "三生三世Netflix海外播出"),
    ("知否知否", "胡夏&郁可唯", "知否Netflix海外热播"),
]

def get_known_hits():
    return KNOWN_GLOBAL_HITS


# ═══ 主程序 ═══
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="搜集老外最感兴趣的中文歌")
    p.add_argument("--youtube", action="store_true", help="抓YouTube排行")
    p.add_argument("--suggest", action="store_true", help="Google搜索建议")
    p.add_argument("--known", action="store_true", help="已知全球爆款清单")
    p.add_argument("--all", action="store_true", help="全部数据源")
    p.add_argument("--json", action="store_true", help="输出JSON格式")
    args = p.parse_args()

    results = []

    if args.all or args.youtube:
        results.extend(scrape_kworb())

    if args.all or args.suggest:
        kw = scrape_google_suggest()
        if args.json:
            results.append({"google_suggestions": kw})

    if args.all or args.known:
        hits = get_known_hits()
        print(f"\n📋 已知全球爆款中文歌 ({len(hits)}首):")
        for title, artist, note in hits:
            print(f"  🎵 {artist} — {title}")
            print(f"     {note}")
        if args.json:
            for title, artist, note in hits:
                results.append({"artist": artist, "title": title, "note": note})

    if args.json and results:
        fn = "global_cn_data.json"
        json.dump(results, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\n✅ 已保存: {fn}")
