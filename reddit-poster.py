#!/usr/bin/env python3
"""
Reddit 帖子自动生成器 v2
每天根据 GitHub Trending + Hacker News + ProductHunt 热搜，
生成 Reddit 帖子草稿 + 推荐板块，发到指定邮箱。
"""

import smtplib
import json
import re
import random
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError
import ssl

# ===================== 配置 =====================

EMAIL = "184723392@qq.com"
SMTP_PASS = "tiabxxqucyhzbhbj"
SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
import os
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
TZ = timezone(timedelta(hours=8))

# 全局超时
socket.setdefaulttimeout(15)

# ===================== 数据源 =====================

def fetch_github_trending():
    """抓取 GitHub Trending — 用 Search API + token，只取6条"""
    posts = []
    try:
        since = (datetime.now(TZ) - timedelta(days=3)).strftime("%Y-%m-%d")
        url = f"https://api.github.com/search/repositories?q=created:>{since}&sort=stars&order=desc&per_page=6"
        ctx = ssl.create_default_context()
        req = Request(url, headers={
            "User-Agent": "SlowBuild-Bot/1.0",
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {GITHUB_TOKEN}"
        })
        with urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read())
        for item in data.get("items", [])[:6]:
            posts.append({
                "title": item.get("full_name", ""),
                "desc": item.get("description", "") or "",
                "url": item.get("html_url", ""),
                "stars": item.get("stargazers_count", 0),
                "lang": item.get("language") or "",
                "source": "github"
            })
        print(f"  GitHub: {len(posts)} 条")
    except Exception as e:
        print(f"  GitHub fetch error: {e}")
    return posts


def fetch_hackernews():
    """抓取 Hacker News — 用 Algolia API（快很多）"""
    posts = []
    try:
        ctx = ssl.create_default_context()
        url = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=5"
        with urlopen(url, context=ctx, timeout=10) as resp:
            data = json.loads(resp.read())
        for hit in data.get("hits", [])[:5]:
            title = hit.get("title", "")
            url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            points = hit.get("points", 0) or 0
            if title and points >= 50:
                posts.append({
                    "title": title,
                    "desc": "",
                    "url": url,
                    "score": points,
                    "source": "hackernews"
                })
        print(f"  HN: {len(posts)} 条")
    except Exception as e:
        print(f"  HN fetch error: {e}")
    return posts


def fetch_producthunt():
    """抓取 ProductHunt RSS"""
    posts = []
    try:
        ctx = ssl.create_default_context()
        req = Request("https://www.producthunt.com/feed", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, context=ctx, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        titles = re.findall(r'<title>(.*?)</title>', html)
        links = re.findall(r'<link>(.*?)</link>', html)
        for t, l in zip(titles[1:6], links[1:6]):
            if t and l and "producthunt.com/posts/" in l:
                posts.append({
                    "title": t,
                    "desc": "",
                    "url": l,
                    "source": "producthunt"
                })
        print(f"  PH: {len(posts)} 条")
    except Exception as e:
        print(f"  PH fetch error: {e}")
    return posts


# ===================== 子版块推荐引擎 =====================

SUBREDDIT_RULES = [
    {
        "keywords": ["ai", "llm", "gpt", "claude", "machine learning", "deep learning",
                     "neural", "transformer", "diffusion", "stable diffusion", "openai",
                     "langchain", "agent", "chatbot", "rag", "embedding", "fine-tun", "anthropic"],
        "subreddits": [
            ("r/MachineLearning", "AI/ML 技术讨论，人气高"),
            ("r/artificial", "AI 综合讨论"),
            ("r/LocalLLaMA", "本地大模型社区，对开源模型极热情"),
        ],
    },
    {
        "keywords": ["tool", "cli", "terminal", "bash", "command", "devtool", "debug",
                     "productivity tool", "automation", "workflow", "plugin", "extension",
                     "converter", "generator"],
        "subreddits": [
            ("r/programming", "编程类工具首选"),
            ("r/coolgithubprojects", "GitHub 项目曝光专用板块"),
        ],
    },
    {
        "keywords": ["web", "frontend", "react", "vue", "css", "html", "javascript",
                     "typescript", "next.js", "tailwind", "component", "ui", "ux", "svelte"],
        "subreddits": [
            ("r/webdev", "前端开发大本营"),
            ("r/javascript", "JS 生态讨论"),
        ],
    },
    {
        "keywords": ["saas", "startup", "business", "monetize", "revenue", "indie",
                     "maker", "bootstrap", "side project", "solopreneur", "nocode"],
        "subreddits": [
            ("r/SaaS", "SaaS 产品讨论"),
            ("r/SideProject", "副业项目分享，氛围友好"),
        ],
    },
    {
        "keywords": ["self-host", "docker", "homelab", "nas", "server", "selfhost",
                     "docker-compose", "raspberry", "proxmox", "deploy"],
        "subreddits": [
            ("r/selfhosted", "自托管大本营，非常活跃"),
            ("r/homelab", "家庭服务器玩家"),
        ],
    },
    {
        "keywords": ["python", "pip", "pypi", "django", "flask", "fastapi"],
        "subreddits": [("r/Python", "Python 社区超大超活跃")],
    },
    {
        "keywords": ["rust", "golang", "go", "cpp", "c++", "zig", "systems programming"],
        "subreddits": [("r/programming", "通用编程板块")],
    },
    {
        "keywords": ["open source", "oss", "github", "free", "mit", "apache", "gpl", "foss"],
        "subreddits": [
            ("r/opensource", "开源社区"),
            ("r/coolgithubprojects", "好用 GitHub 项目"),
        ],
    },
    {
        "keywords": ["design", "figma", "color", "font", "icon", "template",
                     "illustration", "landing page", "ui kit", "css art"],
        "subreddits": [
            ("r/web_design", "网页设计"),
            ("r/InternetIsBeautiful", "好看网站分享"),
        ],
    },
]

DEFAULT_REDDIT = [
    ("r/InternetIsBeautiful", "有意思的网站/工具都适合"),
    ("r/SideProject", "副业项目展示"),
    ("r/programming", "技术类通用"),
]


def match_subreddits(item):
    text = (item.get("title", "") + " " + item.get("desc", "")).lower()
    for rule in SUBREDDIT_RULES:
        if any(kw in text for kw in rule["keywords"]):
            seen = set()
            unique = []
            for name, reason in rule["subreddits"]:
                if name not in seen:
                    seen.add(name)
                    unique.append((name, reason))
            return unique[:3]
    return list(DEFAULT_REDDIT)[:3]


# ===================== 帖子生成 =====================

REDDIT_TEMPLATES = {
    "github": [
        {
            "title": "Just found {name}: {oneliner}",
            "body": (
                "Stumbled upon [{name}]({url}) on GitHub today.\n\n"
                "{description}\n\n"
                "⭐ {stars} stars | 🛠️ {lang}\n\n"
                "Has anyone used this? What do you think?"
            ),
        },
        {
            "title": "{name} — {oneliner} [{lang}]",
            "body": (
                "Hey folks! Wanted to share [{name}]({url}) — it just hit {stars} stars on GitHub.\n\n"
                "**What it does:** {description}\n\n"
                "Built with {lang}.\n\n"
                "Anyone working on something similar?"
            ),
        },
        {
            "title": "TIL about {name}: {oneliner}",
            "body": (
                "Today I learned about [{name}]({url}) — {description}\n\n"
                "Currently at {stars} ⭐ on GitHub. Built in {lang}.\n\n"
                "What similar tools do you use? Always looking for recommendations."
            ),
        },
    ],
    "hackernews": [
        {
            "title": "{title} — interesting discussion on HN",
            "body": (
                "Saw this on HN front page: [{title}]({url})\n\n"
                "The discussion in the comments is really insightful. Wanted to share and hear what "
                "this community thinks.\n\n"
                "What's your take?"
            ),
        },
        {
            "title": "Thoughts on this? {title}",
            "body": (
                "This hit the front page of HN today: [{title}]({url})\n\n"
                "Curious what people here think. The HN discussion had some strong "
                "opinions on both sides.\n\n"
                "How would you approach this?"
            ),
        },
    ],
    "producthunt": [
        {
            "title": "Just launched on ProductHunt: {title}",
            "body": (
                "Spotted [{title}]({url}) launching on ProductHunt today.\n\n"
                "Looks useful for anyone into {category}.\n\n"
                "Anyone tried it yet? First impressions?"
            ),
        },
        {
            "title": "This new tool {title} looks promising — anyone tried it?",
            "body": (
                "Came across [{title}]({url}) on ProductHunt.\n\n"
                "Seems like a fresh take on {category} tools.\n\n"
                "Would love to hear real user experiences before I dive in."
            ),
        },
    ],
}


def gen_oneliner(desc, max_len=80):
    if not desc:
        return "a cool project"
    first = desc.split(".")[0].strip()
    if len(first) > max_len:
        first = first[:max_len - 3].rsplit(" ", 1)[0] + "..."
    return first


def infer_category(item):
    text = (item.get("title", "") + " " + item.get("desc", "")).lower()
    cats = {
        "developers": ["dev", "code", "api", "sdk", "library", "framework", "cli", "ide"],
        "designers": ["design", "ui", "figma", "color", "template"],
        "productivity": ["productivity", "task", "todo", "note", "automation", "workflow"],
        "AI enthusiasts": ["ai", "llm", "gpt", "model", "machine", "neural"],
        "self-hosters": ["self-host", "docker", "homelab", "server", "deploy"],
    }
    for cat, kws in cats.items():
        if any(kw in text for kw in kws):
            return cat
    return "tech enthusiasts"


def generate_reddit_post(item):
    source = item.get("source", "github")
    templates = REDDIT_TEMPLATES.get(source, REDDIT_TEMPLATES["github"])
    tpl = random.choice(templates)

    name = item.get("title", "this project")
    repo = name.split("/")[-1] if "/" in name else name
    oneliner = gen_oneliner(item.get("desc", ""))
    stars = item.get("stars", item.get("score", "N/A"))
    lang = item.get("lang", "").title() or "N/A"
    desc_long = item.get("desc", "") or item.get("title", "")
    category = infer_category(item)
    url = item.get("url", "")

    title = tpl["title"].format(
        name=name, repo=repo, oneliner=oneliner,
        title=item.get("title", ""), lang=lang, category=category
    )

    body = tpl["body"].format(
        name=name, repo=repo, url=url, description=desc_long,
        stars=stars, lang=lang, title=item.get("title", ""),
        category=category, oneliner=oneliner
    )

    subreddits = match_subreddits(item)

    return {
        "title": title,
        "body": body,
        "source_url": url,
        "source": source,
        "subreddits": subreddits,
        "stars": stars,
    }


# ===================== 邮件发送 =====================

def build_html_email(posts):
    today = datetime.now(TZ).strftime("%Y-%m-%d")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#1a1a2e;color:#e0e0e0;padding:20px;line-height:1.7}}
h1{{color:#ff6b6b;text-align:center;font-size:1.5em}}
h2{{color:#ffd93d;margin-top:30px;border-bottom:1px solid #333;padding-bottom:5px;font-size:1.2em}}
.sub-badge{{display:inline-block;background:#16213e;color:#4ecdc4;padding:2px 8px;border-radius:4px;margin:2px 4px;font-size:.85em}}
.reason{{color:#888;font-size:.8em}}
.post{{background:#16213e;border-radius:8px;padding:16px 20px;margin:12px 0}}
.post-title{{color:#ffd93d;font-weight:bold;font-size:1.05em;margin-bottom:6px}}
.post-body{{color:#ccc;white-space:pre-wrap;font-size:.9em;border-left:3px solid #333;padding-left:12px;margin:8px 0}}
.post-meta{{font-size:.75em;color:#666;margin-top:8px}}
.source-gh{{background:#2dba4e33;color:#2dba4e;padding:1px 6px;border-radius:3px;font-size:.7em;margin-right:6px}}
.source-hn{{background:#ff660033;color:#ff6600;padding:1px 6px;border-radius:3px;font-size:.7em;margin-right:6px}}
.source-ph{{background:#da552f33;color:#da552f;padding:1px 6px;border-radius:3px;font-size:.7em;margin-right:6px}}
.footer{{text-align:center;color:#555;margin-top:40px;font-size:.8em}}
a{{color:#4ecdc4}}
</style></head><body>
<h1>🗞️ Reddit 发帖灵感日报</h1>
<p style="text-align:center;color:#888">{today} · {len(posts)} 个帖子草稿 · 附推荐板块</p>
"""

    for i, p in enumerate(posts, 1):
        sub_tags = " ".join(
            f'<span class="sub-badge">🎯 {s[0]}</span>'
            for s in p["subreddits"]
        )
        reasons = "<br>".join(
            f"  → <b>{s[0]}</b>: {s[1]}" for s in p["subreddits"]
        )
        src = p.get("source", "github")
        src_tag = {"github": "source-gh", "hackernews": "source-hn", "producthunt": "source-ph"}.get(src, "source-gh")
        stars_info = f" · ⭐ {p.get('stars', 'N/A')}" if p.get("stars") else ""

        html += f"""
<div class="post">
  <div class="post-title">#{i} {p['title']}</div>
  <div class="post-body">{p['body']}</div>
  <div class="post-meta">
    <span class="{src_tag}">{src}</span>
    推荐板块：{sub_tags}{stars_info}
    <div class="reason">{reasons}</div>
    来源：<a href="{p['source_url']}">{p['source_url'][:80]}</a>
  </div>
</div>"""

    html += """
<div class="footer">
  <p>📬 每日自动生成 · SlowBuild</p>
  <p>⚠️ 提示：发帖前请检查目标子版块规则，部分板块对自推广有限制</p>
</div>
</body></html>"""
    return html


def send_email(html):
    today = datetime.now(TZ).strftime("%m/%d")
    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL
    msg["To"] = EMAIL
    msg["Subject"] = f"🗞️ Reddit 发帖灵感日报 — {today}"

    text = re.sub(r"<[^>]+>", "", html)
    text = re.sub(r"\n{3,}", "\n\n", text)
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
        s.login(EMAIL, SMTP_PASS)
        s.send_message(msg)
    print("邮件发送成功")


# ===================== 主流程 =====================

def main():
    print(f"[{datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}] Reddit Poster 开始运行...")

    # 1. 抓取数据
    print("抓取数据...")
    github = fetch_github_trending()
    hn = fetch_hackernews()
    ph = fetch_producthunt()

    all_items = github + hn + ph
    if not all_items:
        print("❌ 没有任何数据，退出")
        return

    # 2. 筛选并生成帖子（最多8条）
    selected = github[:4]  # GitHub 取前4
    if hn:
        selected.extend(hn[:2])  # HN 取前2
    if ph:
        selected.extend(ph[:2])  # PH 取前2
    selected = selected[:8]

    posts = []
    for item in selected:
        try:
            post = generate_reddit_post(item)
            posts.append(post)
            print(f"  ✅ {post['title'][:60]}... → {post['subreddits'][0][0] if post['subreddits'] else '?'}")
        except Exception as e:
            print(f"  ❌ 生成失败: {e}")

    if not posts:
        print("❌ 没有成功生成任何帖子")
        return

    # 3. 发送邮件
    html = build_html_email(posts)
    send_email(html)
    print(f"完成！共生成 {len(posts)} 个 Reddit 帖子")


if __name__ == "__main__":
    main()
