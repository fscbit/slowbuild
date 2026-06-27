#!/usr/bin/env python3
"""
🔍 slowbuild 工具挖掘机 — 多源监控 + 邮件推送
=================================================
监控 GitHub / Product Hunt / Hacker News 等平台，
发现快速增长的工具项目，自动发送QQ邮箱报告。

用法:
    python tool_scout.py                  # 完整扫描，输出报告到 stdout
    python tool_scout.py --email          # 扫描并发送邮件到站长QQ邮箱
    python tool_scout.py --cron           # 定时模式：只报新发现和变化
    python tool_scout.py --quick          # 快速扫描（每个源精简）
    python tool_scout.py --top 20         # 输出TOP20推荐

定时任务（NAS/VM）:
    # 每天早8点跑一次，发邮件
    0 8 * * * cd /path/to/slowbuild && python3 scripts/tool_scout.py --cron --email

环境变量（可选）:
    GITHUB_TOKEN     GitHub Token（提升 API 限额到 5000/小时）
    SCOUT_EMAIL      接收报告的邮箱（默认 184723392@qq.com）
"""

import os, sys, json, time, re, hashlib, argparse, smtplib, ssl
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# ═══════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "scout_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
TARGET_EMAIL = os.environ.get("SCOUT_EMAIL", "184723392@qq.com")

# QQ邮箱 SMTP
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "184723392@qq.com"
SMTP_PASS = "tiabxxqucyhzbhbj"
FROM_NAME = "slowbuild Scout 🤖"

# 语言偏好（按封装难度排序）
LANGS = ["python", "go", "javascript", "typescript", "rust"]

# 排除关键词（纯库/框架/玩具）
EXCLUDE_KEYWORDS = [
    "framework", "library", "boilerplate", "starter-template",
    "awesome-list", "interview", "leetcode", "algorithm",
    "machine-learning", "deep-learning", "neural-network",
    "blockchain", "crypto-wallet", "nft"
]

# ═══════════════════════════════════════════
#  多源数据抓取
# ═══════════════════════════════════════════

def github_api(path, params=None):
    """调用 GitHub REST API v3"""
    url = f"https://api.github.com/{path}"
    if params:
        url += "?" + urlencode(params)
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "slowbuild-scout/1.0"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except HTTPError as e:
        if e.code == 403:
            print(f"  ⚠️ GitHub API 限流，等待 60s...", file=sys.stderr)
            time.sleep(60)
            return github_api(path, params)
        return None
    except Exception as e:
        print(f"  ⚠️ GitHub API error: {e}", file=sys.stderr)
        return None

def github_search_repos(query, min_stars=300, per_page=20, sort="stars"):
    """搜索 GitHub 仓库"""
    data = github_api("search/repositories", {
        "q": f"{query} stars:>{min_stars} pushed:>2025-01-01",
        "sort": sort, "order": "desc", "per_page": str(per_page)
    })
    if not data or "items" not in data:
        return []
    results = []
    for r in data["items"]:
        results.append({
            "source": "github",
            "name": r["full_name"],
            "url": r["html_url"],
            "stars": r["stargazers_count"],
            "language": (r.get("language") or "").lower(),
            "description": (r.get("description") or ""),
            "updated": r.get("updated_at", ""),
            "topics": r.get("topics", []),
            "forks": r.get("forks_count", 0),
            "license": (r.get("license") or {}).get("spdx_id", ""),
        })
    return results

def github_trending_weekly():
    """
    用 GitHub Search API 模拟 Trending 效果。
    API 比 HTML 解析更稳定可靠。
    """
    results = []
    # 按语言分别搜索最近创建的高星项目
    for lang in LANGS[:3]:  # python, go, js
        data = github_api("search/repositories", {
            "q": f"language:{lang} created:>2025-01-01 stars:>500",
            "sort": "stars", "order": "desc", "per_page": "10"
        })
        if not data or "items" not in data:
            continue
        for r in data["items"]:
            results.append({
                "source": "github-trending",
                "name": r["full_name"],
                "url": r["html_url"],
                "stars": r["stargazers_count"],
                "language": (r.get("language") or "").lower(),
                "description": r.get("description") or "",
                "updated": r.get("updated_at", ""),
                "topics": r.get("topics", []),
                "forks": r.get("forks_count", 0),
                "license": (r.get("license") or {}).get("spdx_id", ""),
                "weekly_stars": r.get("stargazers_count", 0),
            })
        time.sleep(1.2)
    return results

def product_hunt_trending():
    """抓取 Product Hunt 热门工具产品"""
    url = "https://api.producthunt.com/v1/posts?sort_by=votes_count&order=desc&per_page=20"
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Authorization": "Bearer _unused_but_required"
    }
    results = []
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for post in data.get("posts", []):
            name = post.get("name", "")
            tagline = post.get("tagline", "")
            url_ph = post.get("redirect_url", "")
            votes = post.get("votes_count", 0)
            # 只关注工具类产品
            if any(kw in (tagline + name).lower() for kw in ["tool", "converter", "generator", "editor", "pdf", "image", "file"]):
                results.append({
                    "source": "producthunt",
                    "name": name,
                    "url": url_ph,
                    "stars": votes,
                    "language": "",
                    "description": tagline,
                    "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "topics": [],
                    "forks": 0,
                    "license": "",
                    "weekly_stars": votes,
                })
    except Exception as e:
        print(f"  ⚠️ Product Hunt fetch failed: {e}", file=sys.stderr)
    return results

def hacker_news_show():
    """抓取 Hacker News Show HN（自荐工具产品）"""
    url = "https://hn.algolia.com/api/v1/search_by_date?tags=show_hn&hitsPerPage=30"
    results = []
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for hit in data.get("hits", []):
            title = hit.get("title", "").replace("Show HN: ", "")
            url_hn = hit.get("url", "") or f"https://news.ycombinator.com/item?id={hit['objectID']}"
            points = hit.get("points", 0)
            if points >= 10:  # 降低门槛，10分以上就收
                results.append({
                    "source": "hackernews",
                    "name": title[:80],
                    "url": url_hn,
                    "stars": points,
                    "language": "",
                    "description": title[:200],
                    "updated": hit.get("created_at", ""),
                    "topics": [],
                    "forks": 0,
                    "license": "",
                    "weekly_stars": points,
                })
    except Exception as e:
        print(f"  ⚠️ HN fetch failed: {e}", file=sys.stderr)
    return results

# ═══════════════════════════════════════════
#  分类搜索策略
# ═══════════════════════════════════════════

CATEGORIES = {
    "PDF": [
        "pdf converter tool", "word to pdf", "pdf editor open source",
        "pdf compressor", "pdf merge split", "ocr pdf tool"
    ],
    "图片处理": [
        "image converter tool", "image compressor cli",
        "background remover tool", "image resizer batch",
        "screenshot tool", "image format converter"
    ],
    "文件转换": [
        "file converter tool", "document converter",
        "format converter cli", "ebook converter",
        "markdown converter tool", "office to markdown"
    ],
    "视频/音频": [
        "video converter tool", "audio converter tool",
        "subtitle generator tool", "text to speech cli",
        "screen recorder tool", "gif maker tool"
    ],
    "数据处理": [
        "csv json converter", "text processing cli",
        "data formatter tool", "regex tester tool",
        "diff tool cli", "batch rename tool"
    ],
    "开发者工具": [
        "json formatter tool", "base64 encoder tool",
        "qrcode generator cli", "uuid generator cli",
        "password generator cli", "hash calculator tool"
    ],
    "效率办公": [
        "notes tool cli", "clipboard manager tool",
        "timer tool cli", "todo list cli",
        "file organizer tool", "calendar tool cli"
    ],
}

# ═══════════════════════════════════════════
#  筛选与评分
# ═══════════════════════════════════════════

def is_valid_tool(repo):
    """检查是否是适合封装的开源工具"""
    desc = (repo.get("description", "") + " " + repo.get("name", "")).lower()
    lang = repo.get("language", "")
    
    # 排除纯库/框架
    if any(kw in desc for kw in EXCLUDE_KEYWORDS):
        return False
    
    # 语言偏好（GitHub repo）
    if repo["source"] == "github" and lang and lang not in LANGS:
        return False  # 非偏好语言的跳过（但仍可在报告中标注）
    
    # 星标门槛
    if repo.get("stars", 0) < 20:
        return False
    
    return True

def score_tool(repo):
    """综合评分 0-100"""
    score = 0
    stars = repo.get("stars", 0)
    
    # 星标分（0-40）
    if stars >= 10000: score += 40
    elif stars >= 5000: score += 35
    elif stars >= 1000: score += 30
    elif stars >= 500: score += 25
    elif stars >= 100: score += 15
    else: score += 5
    
    # 增速分（0-30）
    if repo.get("weekly_stars", 0) >= 500: score += 30
    elif repo.get("weekly_stars", 0) >= 200: score += 25
    elif repo.get("weekly_stars", 0) >= 100: score += 20
    elif repo.get("weekly_stars", 0) >= 50: score += 15
    elif repo.get("weekly_stars", 0) >= 20: score += 10
    
    # 封装难度分（0-15）
    lang = repo.get("language", "").lower()
    if lang in ("python",):
        score += 15  # PyInstaller 最容易
    elif lang in ("go",):
        score += 15  # 编译单文件
    elif lang in ("javascript", "typescript"):
        score += 10  # pkg 可打
    elif lang in ("rust",):
        score += 8
    
    # 源分（0-15）
    if repo["source"] == "github-trending":
        score += 15  # 实时热榜信号强
    elif repo["source"] == "producthunt":
        score += 10
    elif repo["source"] == "hackernews":
        score += 5
    else:
        score += 3
    
    return min(score, 100)

def classify_repo(repo):
    """自动分类"""
    text = (repo.get("description", "") + " " + repo.get("name", "")).lower()
    topics = " ".join(repo.get("topics", []))
    text += " " + topics
    
    if any(w in text for w in ["pdf", "ocr", "document"]): return "PDF"
    if any(w in text for w in ["image", "photo", "picture", "screenshot", "background remove", "watermark"]): return "图片处理"
    if any(w in text for w in ["video", "audio", "mp3", "mp4", "subtitle", "speech", "tts", "gif", "screen record"]): return "视频/音频"
    if any(w in text for w in ["convert", "format", "markdown", "ebook", "office", "docx", "xlsx"]): return "文件转换"
    if any(w in text for w in ["json", "csv", "xml", "yaml", "regex", "diff", "batch", "rename", "hash", "base64"]): return "数据处理"
    if any(w in text for w in ["qrcode", "uuid", "password", "color picker", "formatter", "encode", "decode", "generator"]): return "开发者工具"
    if any(w in text for w in ["notes", "clipboard", "timer", "todo", "organize", "calendar", "productivity"]): return "效率办公"
    
    return "其他"

# ═══════════════════════════════════════════
#  报告生成
# ═══════════════════════════════════════════

def generate_html_report(tools, title="slowbuild 工具挖掘日报"):
    """生成 HTML 邮件报告（美观）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(tools)
    
    # 按分类整理
    by_cat = {}
    for t in tools:
        cat = t.get("category", "其他")
        by_cat.setdefault(cat, []).append(t)
    
    # 工具卡片 HTML
    def tool_html(t):
        star_str = f"⭐ {t['stars']:,}" if t['stars'] > 0 else ""
        ws_str = f"📈 +{t.get('weekly_stars', 0)}/周" if t.get('weekly_stars', 0) > 50 else ""
        source_icon = {"github": "🐙", "github-trending": "🔥", "producthunt": "🐱", "hackernews": "🧠"}.get(t['source'], "📌")
        return f"""
    <tr>
      <td style="padding:8px 0;border-bottom:1px solid #eee">{source_icon}</td>
      <td style="padding:8px 12px;border-bottom:1px solid #eee">
        <a href="{t['url']}" style="color:#1a73e8;font-weight:600;text-decoration:none">{t['name'][:60]}</a>
        <div style="font-size:12px;color:#666;margin-top:2px">{t.get('description', '')[:120]}</div>
      </td>
      <td style="padding:8px 0;border-bottom:1px solid #eee;white-space:nowrap;font-size:13px">{t.get('language','').title()}</td>
      <td style="padding:8px 0;border-bottom:1px solid #eee;white-space:nowrap;font-size:13px;color:#333">{star_str}</td>
      <td style="padding:8px 12px;border-bottom:1px solid #eee;white-space:nowrap;font-size:13px">{t['score']}分</td>
    </tr>"""
    
    content = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,sans-serif;max-width:680px;margin:0 auto;padding:20px;background:#fafaf8">
  <div style="background:#1e1e1e;color:#fff;padding:24px;border-radius:12px 12px 0 0">
    <h1 style="margin:0;font-size:1.3rem">🤖 {title}</h1>
    <p style="margin:8px 0 0;opacity:.7;font-size:.82rem">{now} · 共发现 {total} 个候选工具</p>
  </div>
  <div style="background:#fff;padding:20px;border:1px solid #e5e5e0;border-top:none;border-radius:0 0 12px 12px">"""
    
    for cat, cat_tools in sorted(by_cat.items()):
        content += f"""
    <h2 style="font-size:1.05rem;margin:20px 0 10px;padding:6px 0;border-bottom:2px solid #e87d4b">📂 {cat} <span style="color:#999;font-size:.82rem">({len(cat_tools)}个)</span></h2>
    <table style="width:100%;border-collapse:collapse">
      <tr style="font-size:12px;color:#999;text-align:left">
        <th></th><th>项目</th><th style="width:60px">语言</th><th style="width:80px">星标</th><th style="width:50px">评分</th>
      </tr>""" + "".join(tool_html(t) for t in cat_tools) + "\n    </table>"
    
    content += """
    <hr style="margin:24px 0;border:none;border-top:1px solid #eee">
    <p style="font-size:12px;color:#999;text-align:center">
      🏭 slowbuild.top · 每日自动推送 · <a href="https://www.slowbuild.top" style="color:#e87d4b">打开工具站</a>
    </p>
  </div>
</body></html>"""
    return content

def generate_text_summary(tools, top_n=20):
    """生成纯文本摘要（cron 模式精简输出）"""
    top = sorted(tools, key=lambda t: t["score"], reverse=True)[:top_n]
    lines = [f"🔍 slowbuild 工具挖掘 — {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
    lines.append(f"共发现 {len(tools)} 个候选，TOP{top_n}如下：\n")
    
    for i, t in enumerate(top, 1):
        star_str = f"⭐{t['stars']:,}" if t['stars'] > 0 else ""
        ws_str = f"📈+{t.get('weekly_stars',0)}" if t.get('weekly_stars', 0) > 50 else ""
        lines.append(f"{i:2d}. [{t['score']}分] {t['name'][:50]}  {star_str} {ws_str}")
        lines.append(f"    {t.get('description','')[:100]}")
        lines.append(f"    {t['url']}")
        lines.append("")
    
    return "\n".join(lines)

# ═══════════════════════════════════════════
#  状态追踪（增量检测）
# ═══════════════════════════════════════════

def load_state():
    """加载上次扫描状态"""
    f = DATA_DIR / "scout_state.json"
    if f.exists():
        return json.loads(f.read_text())
    return {"last_run": "", "tools": {}, "sent_top": []}

def save_state(tools):
    """保存当前扫描状态"""
    state = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "tools": {t["url"]: {"name": t["name"], "stars": t["stars"], "score": t["score"]} for t in tools},
        "sent_top": [t["url"] for t in sorted(tools, key=lambda t: t["score"], reverse=True)[:20]]
    }
    (DATA_DIR / "scout_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2))

def get_new_tools(tools):
    """对比上次，找出新发现的工具"""
    old = load_state()
    old_urls = set(old["tools"].keys())
    return [t for t in tools if t["url"] not in old_urls]

def get_star_changes(tools):
    """检测星标增长变化"""
    old = load_state()
    changes = []
    for t in tools:
        if t["url"] in old["tools"]:
            old_stars = old["tools"][t["url"]]["stars"]
            if t["stars"] > old_stars + 200:
                changes.append((t, old_stars, t["stars"]))
    return sorted(changes, key=lambda c: c[0]["stars"] - c[1], reverse=True)

# ═══════════════════════════════════════════
#  邮件发送
# ═══════════════════════════════════════════

def send_email(to_email, subject, html_body):
    """通过 QQ SMTP 发送邮件"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        print(f"✅ 邮件已发送到 {to_email}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}", file=sys.stderr)
        return False

# ═══════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════

def run_scan(quick=False):
    """执行全源扫描"""
    all_tools = []
    
    # 1. GitHub Trending（本周热榜）
    print("🔥 抓取 GitHub Trending...")
    all_tools.extend(github_trending_weekly())
    print(f"   找到 {len(all_tools)} 个热门")
    
    # 2. GitHub 分类搜索
    if not quick:
        for cat, queries in CATEGORIES.items():
            for q in queries[:2]:  # 每个分类只搜2个关键词，节省API
                print(f"🔍 搜索: {q[:40]}...")
                results = github_search_repos(q, min_stars=100)
                all_tools.extend(results)
                time.sleep(1.5)  # 避免API限流
    
    # 3. Product Hunt
    print("🐱 抓取 Product Hunt...")
    ph_tools = product_hunt_trending()
    all_tools.extend(ph_tools)
    print(f"   找到 {len(ph_tools)} 个")
    
    # 4. Hacker News Show HN
    print("🧠 抓取 Hacker News Show...")
    hn_tools = hacker_news_show()
    all_tools.extend(hn_tools)
    print(f"   找到 {len(hn_tools)} 个")
    
    # 去重 + 筛选 + 评分 + 分类
    seen = set()
    unique = []
    for t in all_tools:
        key = t["url"]
        if key in seen:
            continue
        seen.add(key)
        if is_valid_tool(t):
            t["score"] = score_tool(t)
            t["category"] = classify_repo(t)
            unique.append(t)
    
    unique.sort(key=lambda t: t["score"], reverse=True)
    print(f"\n✅ 总候选: {len(unique)} 个 (去重筛选后)")
    return unique

def main():
    parser = argparse.ArgumentParser(description="slowbuild 工具挖掘机")
    parser.add_argument("--quick", action="store_true", help="快速扫描")
    parser.add_argument("--email", action="store_true", help="发送邮件报告")
    parser.add_argument("--cron", action="store_true", help="定时模式：只报告新发现")
    parser.add_argument("--top", type=int, default=30, help="输出TOP N (默认30)")
    parser.add_argument("--dry-run", action="store_true", help="不保存状态，不发送邮件")
    args = parser.parse_args()
    
    print("=" * 50)
    print("  🔍 slowbuild 工具挖掘机 v2.0")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  模式: {'⚡快速' if args.quick else '📡完整'} {'📧邮件' if args.email else ''} {'🕐定时' if args.cron else ''}")
    print("=" * 50)
    
    # 执行扫描
    tools = run_scan(quick=args.quick)
    
    if not tools:
        print("\n😞 未发现任何候选工具")
        return
    
    if args.cron:
        # 定时模式：只报告新发现和增长变化
        new = get_new_tools(tools)
        changes = get_star_changes(tools)
        
        if not new and not changes:
            print("\n📭 无新发现，跳过报告")
            if not args.dry_run:
                save_state(tools)
            return
        
        # 只取新发现 + 变化的
        report_tools = new + [c[0] for c in changes]
        report_tools = sorted(set(report_tools), key=lambda t: t["score"], reverse=True)
        
        subject = f"🆕 slowbuild 新工具发现 ({len(new)}个) — {datetime.now().strftime('%m/%d')}"
        if changes:
            subject += f" + {len(changes)}个增长"
        
        html = generate_html_report(report_tools, subject)
        print(f"\n📊 报告: {len(new)}新 + {len(changes)}增长")
        print(generate_text_summary(report_tools))
        
        if args.email and not args.dry_run:
            send_email(TARGET_EMAIL, subject, html)
        
        if not args.dry_run:
            save_state(tools)
    else:
        # 完整模式
        top_tools = tools[:args.top]
        subject = f"🔍 slowbuild 工具挖掘日报 — {datetime.now().strftime('%m/%d')}"
        html = generate_html_report(top_tools, subject)
        text = generate_text_summary(top_tools, args.top)
        
        print(f"\n📊 TOP{args.top} 推荐:")
        print(text)
        
        if args.email and not args.dry_run:
            send_email(TARGET_EMAIL, subject, html)
        
        if not args.dry_run:
            save_state(tools)
    
    print(f"\n💾 状态已保存到 {DATA_DIR / 'scout_state.json'}")

if __name__ == "__main__":
    main()
