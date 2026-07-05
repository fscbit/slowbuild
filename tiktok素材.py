#!/usr/bin/env python3
"""
TikTok 每日素材包生成器 — 零 token 消耗，纯模板+数据
每天跑一次，输出 3 条视频文案 + 素材建议
"""

import requests, json, os, random, re
from datetime import datetime, timedelta
from pathlib import Path

REPO_DIR = Path(__file__).parent
OUTPUT_DIR = REPO_DIR / "tiktok-素材"
UA = "slowbuild-bot/1.0"
T = 15

# ══════════════════════════════════════════
# 📚 内置语录库（中英双语）
# ══════════════════════════════════════════

MOTIVATIONAL_QUOTES = [
    ("The only way to do great work is to love what you do. — Steve Jobs",
     "做伟大的工作的唯一方法就是热爱你所做的事。"),
    ("It does not matter how slowly you go as long as you do not stop. — Confucius",
     "走得慢没关系，只要不停下来。"),
    ("Your limitation—it's only your imagination.",
     "你的限制——只是你的想象力。"),
    ("Push yourself, because no one else is going to do it for you.",
     "鞭策自己，因为没有人会替你这么做。"),
    ("Great things never come from comfort zones.",
     "伟大的事情永远不会从舒适区来。"),
    ("Dream it. Wish it. Do it.",
     "梦想，渴望，实践。"),
    ("Success is not final, failure is not fatal: it is the courage to continue that counts.",
     "成功不是终点，失败不是末日：重要的是继续前进的勇气。"),
    ("The harder you work for something, the greater you'll feel when you achieve it.",
     "越努力，越幸运。"),
    ("Don't stop when you're tired. Stop when you're done.",
     "累了别停，做完了再停。"),
    ("Wake up with determination. Go to bed with satisfaction.",
     "带着决心醒来，带着满足入睡。"),
    ("Little things make big days. — Unknown",
     "小事成就大日子。"),
    ("Everything you've ever wanted is on the other side of fear. — George Addair",
     "你渴望的一切都在恐惧的另一边。"),
    ("The secret of getting ahead is getting started. — Mark Twain",
     "成功的秘诀就是开始行动。"),
    ("It's not about having time. It's about making time.",
     "不是有没有时间，而是会不会挤时间。"),
    ("Your vibe attracts your tribe.",
     "你的气场吸引你的圈子。"),
]

LIFE_TIPS = [
    ("Keep a 'Done List' next to your To-Do list. Seeing what you've accomplished builds momentum.",
     "待办清单旁边放一个「已完成清单」，看到自己做了什么比看到还要做什么更激励人。"),
    ("The 5-minute rule: if a task takes less than 5 minutes, do it immediately. Don't let small tasks pile up.",
     "5分钟法则：一件事如果5分钟内能搞定，立刻做，别堆积。"),
    ("Drink a glass of water first thing in the morning. Your brain is 75% water.",
     "起床先喝一杯水，你的大脑 75% 是水。"),
    ("Put your phone in another room when you need to focus. Out of sight, out of mind.",
     "需要专注时把手机放另一个房间。眼不见心不烦。"),
    ("Use the '2-day rule': never skip a habit for more than 2 days in a row.",
     "2天法则：任何习惯连续中断不超过 2 天。"),
    ("Write down 3 things you're grateful for every night. It rewires your brain for positivity.",
     "每晚写下 3 件感恩的事，这能重新训练你的大脑。"),
    ("If you're stuck, change your environment. A 5-minute walk resets your brain.",
     "卡壳了就换个环境，散步5分钟等于重启大脑。"),
    ("Batch similar tasks together. Context switching costs 20+ minutes each time.",
     "同类任务批量处理，每次切换上下文浪费 20 分钟以上。"),
    ("The best productivity system is the one you actually use. Don't over-engineer it.",
     "最好的效率系统就是你实际在用的那个，别过度设计。"),
    ("Before bed, write down your top 3 priorities for tomorrow. Wake up with clarity.",
     "睡前写下明天的 3 个优先级，醒来就有方向。"),
    ("Say no to good opportunities so you can say yes to great ones.",
     "对好机会说不，才能对更好的机会说是。"),
    ("Your morning routine sets the tone for your entire day. Protect it.",
     "早晨的节奏决定一天的基调，保护它。"),
]

TODAY_ILEARNED = [
    ("Octopuses have three hearts, and two of them stop beating when they swim.",
     "章鱼有三颗心脏，游泳时其中两颗会停止跳动。"),
    ("Bananas are berries, but strawberries aren't.",
     "香蕉是浆果，草莓不是。"),
    ("A day on Venus is longer than a year on Venus.",
     "金星上的一天比一年还长。"),
    ("Sharks existed before trees.",
     "鲨鱼比树更早出现在地球上。"),
    ("The Eiffel Tower can be 15 cm taller during summer due to thermal expansion.",
     "埃菲尔铁塔夏天因热胀冷缩会变高 15 厘米。"),
    ("Honey never spoils. Archaeologists found 3000-year-old honey in Egyptian tombs.",
     "蜂蜜永远不会变质，考古学家在埃及古墓发现了 3000 年前的蜂蜜。"),
    ("There are more stars in the universe than grains of sand on all Earth's beaches.",
     "宇宙中的星星比地球上所有沙滩的沙粒还多。"),
    ("A group of flamingos is called a 'flamboyance'.",
     "一群火烈鸟叫一个「flamboyance」（华丽）。"),
    ("The shortest war in history was between Britain and Zanzibar in 1896. It lasted 38 minutes.",
     "历史上最短的战争是 1896 年英国和桑给巴尔之战，持续了 38 分钟。"),
    ("Wombat poop is cube-shaped.",
     "袋熊的💩是方形的。"),
    ("The human nose can detect over 1 trillion different scents.",
     "人类的鼻子能分辨超过 1 万亿种不同气味。"),
    ("Lightning strikes the Earth about 100 times every second.",
     "地球每秒被闪电击中约 100 次。"),
    ("Scotland's national animal is the unicorn.",
     "苏格兰的国兽是独角兽🦄。"),
    ("There's a species of jellyfish that is biologically immortal.",
     "有一种水母在生物学上是不死的。"),
]

TOOL_DEMO_TEMPLATES = [
    "This free tool saved me 3 hours today. Link in bio 🔗 #productivity #techtok",
    "Stop doing this manually. There's a free tool for that. #dev #opensource",
    "One command. That's all it takes. 🤯 #coding #programmer",
    "I found this on GitHub and now I use it every day. #opensource #tools",
    "The tool every developer needs but nobody talks about. #programming",
]

# ══════════════════════════════════════════
# 数据抓取（零 token，全 API）
# ══════════════════════════════════════════

def http(url, **kw):
    kw.setdefault("headers", {"User-Agent": UA})
    kw.setdefault("timeout", T)
    return requests.get(url, **kw)

def fetch_github_tools():
    """热门小工具"""
    try:
        r = http("https://api.github.com/search/repositories",
                 params={"q": "stars:50..500 pushed:>2026-06-01", "sort": "stars",
                         "order": "desc", "per_page": 5})
        tools = []
        for repo in r.json().get("items", []):
            tools.append({
                "name": repo.get("full_name", ""),
                "desc": (repo.get("description") or "")[:80],
                "stars": repo.get("stargazers_count", 0),
                "url": repo.get("html_url", ""),
                "lang": repo.get("language") or "",
            })
        return tools
    except:
        return []

def fetch_hn_stories():
    """Hacker News 热帖"""
    try:
        r = http("https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=5")
        stories = []
        for hit in r.json().get("hits", []):
            title = hit.get("title", "")[:100]
            points = hit.get("points", 0)
            comments = hit.get("num_comments", 0)
            url = hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID','')}")
            stories.append({"title": title, "points": points, "comments": comments, "url": url})
        return stories
    except:
        return []

def fetch_wiki_random():
    """Wikipedia 随机冷知识"""
    try:
        r = http("https://en.wikipedia.org/api/rest_v1/page/random/summary")
        d = r.json()
        return {
            "title": d.get("title", ""),
            "extract": (d.get("extract", "") or "")[:200],
        }
    except:
        return None

def fetch_zhihu_hot(limit=5):
    """知乎热榜"""
    try:
        r = http("https://api.zhihu.com/topstory/hot-list")
        items = []
        for item in r.json().get("data", [])[:limit]:
            t = item.get("target", {})
            items.append({
                "title": t.get("title", "")[:80],
                "url": f"https://www.zhihu.com/question/{t.get('id','')}",
                "hot": item.get("detail_text", ""),
            })
        return items
    except:
        return []

def fetch_devto():
    """Dev.to 热文"""
    try:
        r = http("https://dev.to/api/articles?per_page=5")
        articles = []
        for a in r.json():
            articles.append({
                "title": a.get("title", "")[:80],
                "url": a.get("url", ""),
                "reactions": a.get("positive_reactions_count", 0),
                "tags": a.get("tag_list", [])[:3],
            })
        return articles
    except:
        return []


# ══════════════════════════════════════════
# 素材包生成
# ══════════════════════════════════════════

def generate_pack(tools, hn_stories, zhihu_items, devto_articles):
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_name = day_names[today.weekday()]
    
    pack = {
        "date": date_str,
        "day": day_name,
        "generated_at": today.strftime("%Y-%m-%d %H:%M"),
        "videos": []
    }
    
    # ═══ 视频 1: 励志语录 ═══
    quote_en, quote_cn = random.choice(MOTIVATIONAL_QUOTES)
    pack["videos"].append({
        "id": 1,
        "type": "motivational_quote",
        "script_en": quote_en,
        "script_cn": quote_cn,
        "hashtags": ["#motivation", "#quotes", f"#{day_name}Motivation", "#mindset", "#inspiration"],
        "visual": "Dark gradient background + white text appearing word by word",
        "music": "Lo-fi / ambient / cinematic soft piano",
        "duration": "15-20 seconds",
        "english_voiceover": quote_en,  # 给 AI 配音用的
        "tip": "用 CapCut 文字动画模板：'Typewriter' 效果",
    })
    
    # ═══ 视频 2: 工具推荐 ═══
    if tools:
        tool = random.choice(tools)
        hook = random.choice(TOOL_DEMO_TEMPLATES)
        pack["videos"].append({
            "id": 2,
            "type": "tool_demo",
            "tool_name": tool["name"],
            "tool_desc": tool["desc"],
            "tool_url": tool["url"],
            "stars": tool["stars"],
            "language": tool["lang"],
            "hook": hook,
            "hashtags": ["#opensource", "#github", "#devtools", "#programming", "#techtok"],
            "visual": f"Screen recording showing {tool['name']} in action",
            "music": "Tech/electronic light beat",
            "duration": "25-30 seconds",
            "english_caption": f"{tool['name']}: {tool['desc']} // {tool['stars']}+ ⭐ on GitHub // Link in bio 🔗",
            "tip": "OBS 录屏 30 秒，加 CapCut 自动英文字幕，不用说话",
        })
    else:
        pack["videos"].append({
            "id": 2,
            "type": "tool_demo",
            "placeholder": True,
            "tool_name": "SlowBuild Free Tools",
            "tool_url": "https://slowbuild.top",
            "hashtags": ["#freetools", "#productivity", "#techtok"],
            "visual": "Show slowbuild.top homepage scrolling",
            "tip": "GitHub API 暂未拉取到数据，用 slowbuild 主页替代",
        })
    
    # ═══ 视频 3: 冷知识/有趣发现 ═══
    fact_en, fact_cn = random.choice(TODAY_ILEARNED)
    pack["videos"].append({
        "id": 3,
        "type": "did_you_know",
        "fact_en": fact_en,
        "fact_cn": fact_cn,
        "hashtags": ["#didyouknow", "#facts", "#mindblown", "#todayilearned", "#interesting"],
        "visual": "Related stock image/video + white text overlay",
        "music": "Curious/mysterious tone",
        "duration": "10-15 seconds",
        "english_caption": f"Did you know? 💡\n{fact_en}\n\nFollow for more daily facts 🔔",
        "tip": "Pexels 找免费相关素材，CapCut 加文字动画",
    })
    
    # ═══ 额外素材: Reddit 替代 — HN/DevTo 热帖 ═══
    content_ideas = []
    for s in hn_stories[:3]:
        content_ideas.append({
            "source": "HackerNews",
            "title": s["title"],
            "url": s["url"],
            f"pts": s["points"],
            "use_for": "Discussion starter: screenshot the title, add your take, ask followers their opinion"
        })
    for a in devto_articles[:2]:
        content_ideas.append({
            "source": "Dev.to",
            "title": a["title"],
            "url": a["url"],
            "tags": a.get("tags", []),
            "use_for": "Tool/app review or tutorial idea"
        })
    for z in zhihu_items[:2]:
        content_ideas.append({
            "source": "知乎热榜",
            "title": z["title"],
            "url": z["url"],
            "use_for": "Hot topic in China — translate/adapt for global audience"
        })
    
    pack["content_ideas"] = content_ideas
    
    # Life tips for extra content
    tip_en, tip_cn = random.choice(LIFE_TIPS)
    pack["bonus"] = {
        "life_tip_en": tip_en,
        "life_tip_cn": tip_cn,
        "use_for": "Extra video: text-only 'Productivity Tip of the Day' — 10 seconds, no face needed",
    }
    
    return pack


# ══════════════════════════════════════════
# 输出
# ══════════════════════════════════════════

def format_markdown(pack):
    """生成易读的 Markdown"""
    md = f"""# 🎬 TikTok 素材包 — {pack['date']} ({pack['day']})

> 生成时间: {pack['generated_at']}
> 每天 3 条视频文案 + 额外素材灵感

---

"""
    for v in pack["videos"]:
        md += f"""## 📹 视频 {v['id']}: {v['type'].replace('_', ' ').title()}

"""
        if v.get("placeholder"):
            md += f"""⚠️ 本期无新数据

**替代方案:** {v.get('tip', '')}

**Hashtags:** {' '.join(v.get('hashtags', []))}

"""
        elif v["type"] == "motivational_quote":
            md += f"""**英文文案（给AI配音用）:**
> {v['script_en']}

**中文参考:**
{v['script_cn']}

**画面:** {v['visual']}
**BGM:** {v['music']}
**时长:** {v['duration']}
**制作:** {v['tip']}

**Hashtags:** {' '.join(v['hashtags'])}

"""
        elif v["type"] == "tool_demo":
            md += f"""**工具:** [{v['tool_name']}]({v['tool_url']}) ⭐ {v.get('stars', '?')}
**简介:** {v.get('tool_desc', '')}
**语言:** {v.get('language', 'N/A')}

**Hook（可做视频封面标题）:**
> {v['hook']}

**英文字幕:**
{v['english_caption']}

**画面:** {v['visual']}
**BGM:** {v['music']}
**时长:** {v['duration']}

**Hashtags:** {' '.join(v['hashtags'])}

"""
        elif v["type"] == "did_you_know":
            md += f"""**英文:**
> {v['fact_en']}

**中文:**
{v['fact_cn']}

**英文字幕:**
{v['english_caption']}

**画面:** {v['visual']}
**BGM:** {v['music']}
**时长:** {v['duration']}
**制作:** {v['tip']}

**Hashtags:** {' '.join(v['hashtags'])}

"""
        md += "---\n\n"
    
    # Content ideas
    md += "## 💡 额外内容灵感（来自 HN / Dev.to / 知乎）\n\n"
    for idea in pack.get("content_ideas", []):
        md += f"- **[{idea['source']}]** [{idea['title'][:60]}]({idea['url']})\n"
        md += f"  → {idea['use_for']}\n\n"
    
    # Bonus
    b = pack.get("bonus", {})
    md += f"""---
## 🎁 彩蛋：每日锦囊

**EN:** {b.get('life_tip_en', '')}
**CN:** {b.get('life_tip_cn', '')}

→ 10秒文字视频，不用露脸，纯文字 + 轻音乐

---
*🤖 自动生成 by slowbuild.top | 零 token 消耗 | 每天 7:00 更新*
"""
    return md


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    print(f"🎬 TikTok 素材包生成 - {today}")
    print("=" * 40)
    
    # 抓数据
    print("[1/3] 抓取素材数据...")
    tools = fetch_github_tools()
    hn = fetch_hn_stories()
    zhihu = fetch_zhihu_hot()
    devto = fetch_devto()
    print(f"  GitHub: {len(tools)} | HN: {len(hn)} | 知乎: {len(zhihu)} | Dev.to: {len(devto)}")
    
    # 生成素材包
    print("[2/3] 生成视频文案...")
    pack = generate_pack(tools, hn, zhihu, devto)
    
    # 输出
    print("[3/3] 输出文件...")
    json_path = OUTPUT_DIR / f"{today}.json"
    md_path = OUTPUT_DIR / f"{today}.md"
    
    json_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(format_markdown(pack), encoding="utf-8")
    
    print(f"  ✅ JSON: {json_path}")
    print(f"  ✅ Markdown: {md_path}")
    print(f"\n📊 今日产出: {len(pack['videos'])} 条视频方案 + {len(pack.get('content_ideas',[]))} 个灵感")


if __name__ == "__main__":
    main()
