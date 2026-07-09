#!/usr/bin/env python3
"""
GitHub 热门项目 → 自动写博客 + 生成工具导航数据
每天跑一次：python3 auto-blog.py
"""

import requests, json, os, subprocess, random, re, shutil
from datetime import datetime
from pathlib import Path
from collections import Counter

# ═══ 配置 ═══
REPO_DIR = Path(__file__).parent
BLOG_DIR = REPO_DIR / "blog"
BLOG_EN_DIR = REPO_DIR / "blog" / "en"
TOOLS_JSON = REPO_DIR / "tools.json"
MAX_NEW_POSTS = 2  # 每天最多写几篇（避免太频繁）
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
UA = "slowbuild-bot/1.0"

# ═══ 中文文案模板 ═══
TOOL_INTROS = [
    "最近在 GitHub 上发现了一个很有意思的项目——",
    "如果你也经常遇到{problem}的烦恼，这个工具可能正好解决你的问题：",
    "今天给大家安利一个 GitHub 上的宝藏项目：",
    "程序员圈子最近都在讨论这个开源工具——",
    "发现一个能省不少事的小工具，分享一下：",
]

USE_CASES = [
    "这个工具可以帮你{use_case}，省去手动操作的麻烦。",
    "用它之后，{use_case}只需要几秒钟，效率直接拉满。",
    "简单配置一下就能{use_case}，比之前快了好几倍。",
]

PROBLEM_TAGS = {
    "pdf": "处理PDF文件",
    "image": "处理图片",
    "video": "视频转换/剪辑",
    "audio": "音频处理",
    "json": "JSON数据处理",
    "markdown": "写Markdown文档",
    "api": "调API接口",
    "docker": "Docker部署",
    "backup": "备份文件",
    "convert": "文件格式转换",
    "download": "下载资源",
    "ai": "AI辅助工作",
    "monitor": "监控系统状态",
    "automation": "重复性工作自动化",
    "search": "搜索文件/代码",
    "database": "数据库管理",
    "encrypt": "数据加密保护",
    "compress": "压缩文件",
    "note": "记笔记/知识管理",
    "password": "管理密码",
    "screenshot": "截图/录屏",
}

TECK_TAGS = ["开源工具", "GitHub热门", "效率工具", "免费软件"]

def http(url, **kw):
    kw.setdefault("headers", {"User-Agent": UA})
    if GITHUB_TOKEN:
        kw["headers"]["Authorization"] = f"token {GITHUB_TOKEN}"
    kw.setdefault("timeout", 20)
    return requests.get(url, **kw)

# ══════════════════════════════════════════
# 1. 抓取 GitHub 热门项目
# ══════════════════════════════════════════

def fetch_trending():
    """搜索近期热门开源工具（排除知名大项目）"""
    EXCLUDE = {"tensorflow","pytorch","kubernetes","vue","react","angular",
               "vscode","flutter","linux","rust","golang","deno","bun",
               "next.js","svelte","tailwindcss","bootstrap","django","laravel",
               "node","ohmyzsh","n8n","supabase","AutoGPT"}
    
    all_repos = []
    
    # 几个不同维度的搜索
    queries = [
        ("stars:>100 pushed:>2026-06-01", "hot", 5),
        ("stars:50..500 created:>2026-05-01", "new", 5),
        ("stars:>200 topic:tool", "tool", 5),
    ]
    
    for q, label, n in queries:
        try:
            r = http("https://api.github.com/search/repositories",
                     params={"q": q, "sort": "stars", "order": "desc", "per_page": n})
            for repo in r.json().get("items", []):
                name = repo.get("full_name", "")
                # 过滤大项目
                skip = False
                for ex in EXCLUDE:
                    if ex.lower() in name.lower():
                        skip = True
                        break
                if skip:
                    continue
                all_repos.append({
                    "full_name": name,
                    "name": repo.get("name", ""),
                    "description": repo.get("description") or "",
                    "url": repo.get("html_url", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language") or "",
                    "topics": repo.get("topics", []),
                    "forks": repo.get("forks_count", 0),
                    "updated": repo.get("updated_at", ""),
                    "homepage": repo.get("homepage") or "",
                    "source": label,
                })
        except Exception as e:
            print(f"  ⚠️ 搜索 '{q}' 失败: {e}")
    
    # 去重并排序
    seen = set()
    unique = []
    for r in sorted(all_repos, key=lambda x: x["stars"], reverse=True):
        if r["full_name"] not in seen:
            seen.add(r["full_name"])
            unique.append(r)
    
    return unique[:30]


# ══════════════════════════════════════════
# 2. 选最有博客价值的项目
# ══════════════════════════════════════════

def pick_blog_worthy(repos, n=MAX_NEW_POSTS):
    """挑选最有故事可写的项目"""
    scored = []
    for r in repos:
        score = 0
        desc = (r.get("description") or "").lower()
        name = r.get("name", "").lower()
        topics = " ".join(r.get("topics", [])).lower()
        text = desc + " " + name + " " + topics
        
        # 有描述加分
        if len(desc) > 30: score += 3
        elif len(desc) > 10: score += 1
        
        # 中文描述加分
        if any('\u4e00' <= c <= '\u9fff' for c in desc):
            score += 2
        
        # 有 homepage 加分（意味着有在线体验）
        if r.get("homepage"): score += 2
        
        # 有 topics 加分
        if r.get("topics"): score += min(len(r["topics"]), 5)
        
        # 小众工具加分（stars 适中，不要太少也不要太多）
        stars = r["stars"]
        if 50 <= stars <= 500: score += 4
        elif 500 < stars <= 2000: score += 3
        elif stars > 2000: score += 1
        
        # 有明确使用场景
        for kw, problem in PROBLEM_TAGS.items():
            if kw in text:
                score += 2
                r["_problem_tag"] = problem
                break
        
        scored.append((score, r))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:n]]


# ══════════════════════════════════════════
# 3. 生成博客 HTML（中英双语）
# ══════════════════════════════════════════

EN_INTROS = [
    "Just discovered a gem on GitHub that might save you hours of work — ",
    "If you've ever struggled with {problem}, this open-source tool is exactly what you need: ",
    "Here's a GitHub project that's been getting a lot of attention lately — ",
    "Found a developer tool that actually makes {problem} easy. Seriously: ",
    "Another day, another awesome open-source project: ",
]

EN_USE_CASES = [
    "This tool lets you {use_case} in seconds instead of wrestling with manual workflows.",
    "With this, {use_case} becomes a one-click operation. No joke.",
    "It turns {use_case} from a headache into something you barely think about.",
]

EN_PROBLEMS = {
    "pdf": "PDF manipulation", "image": "image processing",
    "video": "video conversion", "audio": "audio editing",
    "json": "JSON formatting", "markdown": "writing Markdown",
    "api": "API integration", "docker": "Docker deployment",
    "backup": "file backups", "convert": "file conversion",
    "download": "downloading resources", "ai": "AI-powered workflows",
    "monitor": "system monitoring", "automation": "workflow automation",
    "search": "code search", "database": "database management",
    "encrypt": "data encryption", "compress": "file compression",
    "note": "note-taking", "password": "password management",
}

EN_TECH_TAGS = ["open source", "GitHub trending", "dev tools", "free software", "productivity"]

def _gen_filename(repo):
    return "tool-" + re.sub(r'[^a-z0-9-]', '', repo.get("name","tool").lower().replace(" ", "-"))[:40] + ".html"

def gen_blog_html_en(repo):
    """Generate English blog post"""
    name = repo.get("full_name", repo.get("name", ""))
    desc = (repo.get("description") or f"{name} — open source tool").strip()[:150]
    desc_short = desc[:120] + ("..." if len(desc) > 120 else "")
    stars = repo.get("stars", 0)
    lang_name = repo.get("language", "")
    url = repo.get("url", "")
    homepage = repo.get("homepage", "")
    topics = repo.get("topics", [])[:5]
    problem = repo.get("_problem_tag", "daily workflow tasks")
    problem_en = EN_PROBLEMS.get(repo.get("_problem_keyword", ""), problem)
    today = datetime.now().strftime("%B %d, %Y")
    intro = random.choice(EN_INTROS).format(problem=problem_en)
    filename = _gen_filename(repo)
    tags = topics[:3] if topics else []
    tags += random.sample(EN_TECH_TAGS, min(2, len(EN_TECH_TAGS)))

    return filename, f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{name} — Open Source Tool Spotlight | SlowBuild</title>
<meta name="description" content="{desc_short} — {stars}+ GitHub stars. {lang_name} project. Daily open source tool recommendations from SlowBuild.">
<meta name="keywords" content="{','.join(tags[:5])},open source,github,developer tools">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.slowbuild.top/blog/en/{filename}">
<link rel="alternate" hreflang="en" href="https://www.slowbuild.top/blog/en/{filename}">
<link rel="alternate" hreflang="zh-CN" href="https://www.slowbuild.top/blog/{filename}">
<meta property="og:title" content="{name} — Open Source Tool | SlowBuild">
<meta property="og:description" content="{desc_short}">
<meta property="og:url" content="https://www.slowbuild.top/blog/en/{filename}">
<meta property="og:type" content="article">
<style>
:root{{--bg:#0a0a0f;--surface:#12121a;--border:#1e1e2e;--text:#d4d4e0;--muted:#707088;--gold:#d4a853;--teal:#38bdf8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.8}}
.container{{max-width:860px;margin:0 auto;padding:20px 24px}}
.breadcrumb{{font-size:.8rem;color:var(--muted);margin-bottom:24px}}
.breadcrumb a{{color:var(--teal);text-decoration:none}}
h1{{font-size:1.8rem;background:linear-gradient(135deg,#d4a853,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}}
.date{{text-align:center;color:var(--muted);font-size:.8rem;margin-bottom:30px}}
h2{{font-size:1.3rem;color:var(--gold);margin:32px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--border)}}
p{{font-size:.92rem;color:#c0c0d0;margin-bottom:14px}}
ul,ol{{font-size:.9rem;color:#c0c0d0;padding-left:24px;margin-bottom:14px}}
li{{margin-bottom:6px}}
a{{color:var(--teal);text-decoration:underline}}
code{{background:var(--surface);padding:2px 8px;border-radius:4px;font-size:.85rem;color:var(--gold)}}
pre{{background:var(--surface);padding:16px;border-radius:8px;overflow-x:auto;margin:16px 0;font-size:.82rem}}
.repo-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px;margin:20px 0}}
.repo-card .stars{{color:var(--gold);font-weight:700;font-size:1.1rem}}
.repo-card .lang{{color:var(--teal);font-size:.8rem;margin-left:8px}}
.repo-card .btn{{display:inline-block;background:var(--gold);color:#000;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.85rem;margin-top:12px;transition:all .2s}}
.repo-card .btn:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(212,168,83,.3)}}
.repo-card .btn.secondary{{background:var(--surface);color:var(--teal);border:1px solid var(--teal)}}
.cta-box{{background:linear-gradient(135deg,rgba(212,168,83,.15),rgba(56,189,248,.1));border:1px solid var(--gold);border-radius:12px;padding:24px;margin:40px 0;text-align:center}}
.cta-box h3{{color:var(--gold);margin-bottom:10px}}
.cta-box p{{color:#b0b0c0;margin-bottom:16px}}
.cta-box .btn{{display:inline-block;background:var(--gold);color:#000;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.9rem;transition:all .2s}}
.cta-box .btn:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(212,168,83,.3)}}
.tags{{margin-top:30px;display:flex;flex-wrap:wrap;gap:8px}}
.tag{{background:var(--surface);color:var(--teal);padding:4px 12px;border-radius:20px;font-size:.75rem}}
footer{{text-align:center;padding:40px 20px;color:var(--muted);font-size:.75rem;border-top:1px solid var(--border)}}
footer a{{color:var(--teal)}}
</style>
</head>
<body>
<div class="container">
<div class="breadcrumb"><a href="/">Home</a> / <a href="/blog/en/">Blog</a> / {name}</div>
<article>
<h1>🚀 {name}: Open Source {problem_en} Tool</h1>
<p class="date">{today} · ⭐ {stars} Stars · {lang_name + ' · ' if lang_name else ''}SlowBuild Spotlight</p>
<p>{intro}<strong>{name}</strong> has earned <strong>{stars}+ stars</strong> on GitHub. If {problem_en} is part of your workflow, this tool deserves a look.</p>
<div class="repo-card">
  <p style="font-size:1.1rem;font-weight:600;margin-bottom:4px">{name}</p>
  <p style="color:var(--muted);font-size:.85rem;margin-bottom:8px">{desc}</p>
  <p><span class="stars">⭐ {stars}</span><span class="lang">{lang_name}</span></p>
  <p style="margin-top:8px">
    <a href="{url}" target="_blank" rel="noopener" class="btn">View on GitHub</a>
    {"<a href=\"" + homepage + "\" target=\"_blank\" rel=\"noopener\" class=\"btn secondary\">Live Demo</a>" if homepage else ""}
  </p>
</div>
<h2>What does it do?</h2>
<p><code>{name}</code> solves a real problem: <strong>{problem_en}</strong>. {random.choice(EN_USE_CASES).format(use_case=problem_en)}</p>
<p>Key highlights:</p>
<ul>
  <li>100% open source — code on GitHub</li>
  <li>Active community, actively maintained</li>
  <li>{lang_name + ' project — easy to deploy and customize' if lang_name else 'Cross-platform — works on Windows, Mac & Linux'}</li>
  <li>{stars}+ stars = community trust</li>
</ul>
<h2>Who is it for?</h2>
<p>If {problem_en} comes up in your daily work, give this tool a try. Whether you&apos;re working solo or on a team, it&apos;ll save you real time.</p>
<p>For developers, the source code is clean and well-organized — a great reference if you want to learn or customize it.</p>
<blockquote>
  <p>💡 <strong>Tip:</strong> Always check the project&apos;s license and last commit date. Active maintenance matters more than star count.</p>
</blockquote>
<div class="cta-box">
  <h3>🔧 More Free Tools</h3>
  <p>SlowBuild has more free online tools — PDF conversion, JSON formatting, QR codes, bazi fortune reading. No sign-up needed.</p>
  <a href="/" class="btn">Browse All Tools →</a>
</div>
<div class="tags">{"".join(f'<span class="tag">{t}</span>' for t in tags)}</div>
</article>
<footer><p>SlowBuild · Free online tools for office workers worldwide</p><p><a href="/">slowbuild.top</a></p></footer>
</div>
</body>
</html>"""


# ══════════════════════════════════════════
# 3b. 中文博客（原版）
def gen_blog_html_zh(repo):
    """生成中文博客 HTML"""
    name = repo.get("full_name", repo.get("name", ""))
    desc = repo.get("description", "") or f"{name} - 一个实用的开源工具"
    desc_short = desc[:120] + ("..." if len(desc) > 120 else "")
    stars = repo.get("stars", 0)
    lang_name = repo.get("language", "")
    url = repo.get("url", "")
    homepage = repo.get("homepage", "")
    topics = repo.get("topics", [])[:5]
    problem = repo.get("_problem_tag", "日常工作效率")
    
    # 文件命名
    slug = re.sub(r'[^a-z0-9-]', '', repo.get("name","tool").lower().replace(" ", "-"))[:40]
    filename = f"tool-{slug}.html"
    
    # 选一个不同的介绍
    intro = random.choice(TOOL_INTROS).format(problem=problem)
    
    # 日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 标签
    tags = topics[:3] if topics else []
    tags += random.sample(TECK_TAGS, min(2, len(TECK_TAGS)))
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{name} - GitHub 热门开源工具推荐 | SlowBuild</title>
<meta name="description" content="{desc_short} - SlowBuild 为你精选的 GitHub 开源工具推荐。{stars}+ Stars，{lang_name}项目。">
<meta name="keywords" content="{','.join(tags[:5])}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://www.slowbuild.top/blog/{filename}">
<meta property="og:title" content="{name} - 开源工具推荐 | SlowBuild">
<meta property="og:description" content="{desc_short}">
<meta property="og:url" content="https://www.slowbuild.top/blog/{filename}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="SlowBuild">
<style>
:root{{--bg:#0a0a0f;--surface:#12121a;--border:#1e1e2e;--text:#d4d4e0;--muted:#707088;--gold:#d4a853;--teal:#38bdf8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.8}}
.container{{max-width:860px;margin:0 auto;padding:20px 24px}}
.breadcrumb{{font-size:.8rem;color:var(--muted);margin-bottom:24px;padding:8px 0}}
.breadcrumb a{{color:var(--teal);text-decoration:none}}
article h1{{font-size:1.8rem;background:linear-gradient(135deg,#d4a853,#38bdf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:10px}}
article .date{{text-align:center;color:var(--muted);font-size:.8rem;margin-bottom:30px}}
article h2{{font-size:1.3rem;color:var(--gold);margin:32px 0 14px;padding-bottom:8px;border-bottom:1px solid var(--border)}}
article p{{font-size:.92rem;color:#c0c0d0;margin-bottom:14px}}
article ul,article ol{{font-size:.9rem;color:#c0c0d0;padding-left:24px;margin-bottom:14px}}
article li{{margin-bottom:6px}}
article a{{color:var(--teal);text-decoration:underline}}
article code{{background:var(--surface);padding:2px 8px;border-radius:4px;font-size:.85rem;color:var(--gold)}}
article pre{{background:var(--surface);padding:16px;border-radius:8px;overflow-x:auto;margin:16px 0;font-size:.82rem}}
.repo-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:24px;margin:20px 0;display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap}}
.repo-card .stars{{color:var(--gold);font-weight:700;font-size:1.1rem}}
.repo-card .lang{{color:var(--teal);font-size:.8rem;margin-left:8px}}
.repo-card .btn{{display:inline-block;background:var(--gold);color:#000;padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.85rem;margin-top:12px;transition:all .2s}}
.repo-card .btn:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(212,168,83,.3)}}
.repo-card .btn.secondary{{background:var(--surface);color:var(--teal);border:1px solid var(--teal)}}
.cta-box{{background:linear-gradient(135deg,rgba(212,168,83,.15),rgba(56,189,248,.1));border:1px solid var(--gold);border-radius:12px;padding:24px;margin:40px 0;text-align:center}}
.cta-box h3{{color:var(--gold);margin-bottom:10px}}
.cta-box p{{color:#b0b0c0;margin-bottom:16px}}
.cta-box .btn{{display:inline-block;background:var(--gold);color:#000;padding:12px 28px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.9rem;transition:all .2s}}
.cta-box .btn:hover{{transform:translateY(-2px);box-shadow:0 8px 24px rgba(212,168,83,.3)}}
.tags{{margin-top:30px;display:flex;flex-wrap:wrap;gap:8px}}
.tag{{background:var(--surface);color:var(--teal);padding:4px 12px;border-radius:20px;font-size:.75rem}}
footer{{text-align:center;padding:40px 20px;color:var(--muted);font-size:.75rem}}
footer a{{color:var(--teal);text-decoration:none}}
</style>
</head>
<body>
<div class="container">
<div class="breadcrumb"><a href="/" class="lang-zh">首页</a> / <a href="/blog/">博客</a> / {name}</div>
<article>
<h1>🚀 {name}：{problem}的开源神器</h1>
<p class="date">{today} · ⭐ {stars} Stars · {lang_name + ' · ' if lang_name else ''}SlowBuild 推荐</p>

<p>{intro}<strong>{name}</strong> 最近在 GitHub 上收获了 <strong>{stars}+ Stars</strong>，对于经常需要{problem}的人来说，这个工具真的很实用。</p>

<div class="repo-card">
  <div>
    <p style="font-size:1.1rem;font-weight:600;margin-bottom:4px">{name}</p>
    <p style="color:var(--muted);font-size:.85rem;margin-bottom:8px">{desc}</p>
    <p><span class="stars">⭐ {stars}</span><span class="lang">{lang_name}</span></p>
    <p style="margin-top:8px">
      <a href="{url}" target="_blank" rel="noopener" class="btn">GitHub 主页</a>
      {"<a href=\"" + homepage + "\" target=\"_blank\" rel=\"noopener\" class=\"btn secondary\">在线体验</a>" if homepage else ""}
    </p>
  </div>
</div>

<h2>这个工具有什么用？</h2>
<p>简单来说，<code>{name}</code> 解决的核心问题是<strong>{problem}</strong>。{random.choice(USE_CASES).format(use_case=problem)}</p>
<p>它的主要特点包括：</p>
<ul>
  <li>完全开源免费，代码托管在 GitHub</li>
  <li>社区活跃，持续维护更新</li>
  <li>{lang_name + ' 编写，部署简单' if lang_name else '跨平台支持，Windows/Mac/Linux 都能用'}</li>
  <li>Star 数 {stars}+，说明社区认可度很高</li>
</ul>

<h2>适合谁用？</h2>
<p>如果你在工作中经常需要处理{problem}相关的任务，这个工具绝对值得一试。不管是个人项目还是团队协作，都能提升不少效率。</p>
<p>对于开发者来说，它的源码也很清晰，想二次开发或者学习的话，拿来参考非常合适。</p>

<blockquote>
  <p>💡 <strong>小提示：</strong>开源工具虽然免费，但使用前建议先看看项目的 License 和最近更新日期，确保还在活跃维护中。</p>
</blockquote>

<div class="cta-box">
  <h3>🔧 更多实用工具</h3>
  <p>SlowBuild 上还有更多免费在线工具——PDF转换、JSON格式化、二维码生成、八字算命，都不需要注册。</p>
  <a href="/" class="btn">浏览全部工具 →</a>
</div>

<div class="tags">
  {"".join(f'<span class="tag">{t}</span>' for t in tags)}
</div>
</article>

<footer>
  <p>SlowBuild · 为打工人打造的免费在线工具站</p>
  <p><a href="/">slowbuild.top</a></p>
</footer>
</div>
</body>
</html>"""
    return filename, html


# ══════════════════════════════════════════
# 4. 生成 tools.json（工具导航数据）
# ══════════════════════════════════════════

def gen_tools_json(repos):
    """生成工具导航 JSON"""
    tools = []
    for r in repos:
        tools.append({
            "name": r.get("full_name", r.get("name", "")),
            "description": (r.get("description") or "")[:120],
            "url": r.get("url", ""),
            "homepage": r.get("homepage") or "",
            "stars": r.get("stars", 0),
            "language": r.get("language") or "",
            "topics": r.get("topics", [])[:5],
            "source": r.get("source", ""),
            "updated": r.get("updated", ""),
        })
    return tools


# ══════════════════════════════════════════
# 5. 自动上架到商店
# ══════════════════════════════════════════

PRODUCTS_FILE = REPO_DIR / "products.json"
SHOP_ICONS = ["🛠️", "⚡", "🔧", "📦", "🚀", "💡", "🎯", "🔮", "⚙️", "🖥️"]
SHOP_MAX_AUTO = 15  # 最多保留多少自动上架的商品


def gen_shop_products(repos):
    """将 GitHub 热项目生成商店 product 条目"""
    products = []
    if PRODUCTS_FILE.exists():
        try:
            existing = json.loads(PRODUCTS_FILE.read_text(encoding="utf-8"))
        except:
            existing = []
    else:
        existing = []
    
    existing_ids = {p.get("id", "") for p in existing}
    existing_gh_names = set()
    for p in existing:
        gh = p.get("github", "")
        if gh:
            existing_gh_names.add(gh.lower())
    
    new_count = 0
    
    for r in repos:
        name = r.get("full_name", "")
        if not name or name.lower() in existing_gh_names:
            continue
        
        # 生成 id
        pid = "gh-" + re.sub(r'[^a-z0-9-]', '', name.lower().replace("/", "-"))[:30]
        if pid in existing_ids:
            continue
        
        desc_text = (r.get("description") or f"{name} - Open source tool").strip()[:150]
        stars = r.get("stars", 0)
        
        product = {
            "id": pid,
            "type": "digital",
            "image": "https://www.slowbuild.top/images/default-tool.png",
            "icon": random.choice(SHOP_ICONS),
            "price": 0,  # 免费开源工具
            "buyLink": r.get("url", ""),  # 直接链到 GitHub
            "github": name,
            "github_stars": stars,
            "name": {
                "en": name,
                "zh-CN": f"{name} (GitHub ⭐{stars})",
                "zh-TW": f"{name} (GitHub ⭐{stars})"
            },
            "desc": {
                "en": desc_text,
                "zh-CN": f"{desc_text} | GitHub {stars}+ Stars 开源项目",
                "zh-TW": f"{desc_text} | GitHub {stars}+ Stars 開源項目"
            },
            "category": "github-tools",
            "source": "auto"
        }
        products.append(product)
        existing_gh_names.add(name.lower())
        existing_ids.add(pid)
        new_count += 1
    
    # 合并：保留老的手动商品，替换自动商品
    # 1. 保留非 auto 的商品
    manual = [p for p in existing if p.get("source") != "auto"]
    # 2. 保留旧的 auto 商品（不超过限制）
    old_auto = [p for p in existing if p.get("source") == "auto"]
    # 3. 新商品插入到旧自动商品前面
    all_auto = products + old_auto
    all_auto = all_auto[:SHOP_MAX_AUTO]
    
    merged = manual + all_auto
    return merged, new_count


# ══════════════════════════════════════════
# 6. 主流程
# ══════════════════════════════════════════

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"🤖 SlowBuild 自动内容生成 - {now}")
    print("=" * 50)
    
    # 抓 GitHub 热门
    print("[1/5] 抓取 GitHub 热门项目...")
    repos = fetch_trending()
    print(f"  ✅ 抓取 {len(repos)} 个项目")
    
    # 生成 tools.json
    print("[2/5] 生成工具导航数据...")
    tools = gen_tools_json(repos)
    TOOLS_JSON.write_text(json.dumps(tools, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ tools.json ({len(tools)} 个工具)")
    
    # 写博客（中英双语）
    print("[3/5] 写博客（EN + 中文）...")
    worthy = pick_blog_worthy(repos)
    new_posts = []
    for repo in worthy:
        # English blog
        fname, html = gen_blog_html_en(repo)
        fpath_en = BLOG_EN_DIR / fname
        if not fpath_en.exists():
            BLOG_EN_DIR.mkdir(parents=True, exist_ok=True)
            fpath_en.write_text(html, encoding="utf-8")
            new_posts.append(f"en/{fname}")
            print(f"  ✅ EN: {fname} ({repo['full_name']})")
        else:
            print(f"  ⏭️ EN 已有: {fname}")
        
        # Chinese blog
        fname_cn, html_cn = gen_blog_html_zh(repo)
        fpath_cn = BLOG_DIR / fname_cn
        if not fpath_cn.exists():
            fpath_cn.write_text(html_cn, encoding="utf-8")
            new_posts.append(fname_cn)
            print(f"  ✅ CN: {fname_cn} ({repo['full_name']})")
        else:
            print(f"  ⏭️ CN 已有: {fname_cn}")
    
    if not new_posts:
        print("  ℹ️ 无新项目值得写")
    
    # 自动上架到商店
    print("[4/5] 更新商店商品...")
    merged, shop_new = gen_shop_products(repos)
    # 备份
    if PRODUCTS_FILE.exists():
        shutil.copy2(PRODUCTS_FILE, str(PRODUCTS_FILE) + ".bak")
    PRODUCTS_FILE.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ 商店: {len(merged)} 商品 (新增 {shop_new} 个)")
    
    # Git 提交
    print("[5/5] Git 提交...")
    os.chdir(REPO_DIR)
    
    try:
        subprocess.run(["git", "add", "tools.json", "products.json", "blog/"], check=True, capture_output=True)
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if result.stdout.strip():
            parts = []
            if new_posts: parts.append(f"{len(new_posts)} posts")
            if shop_new: parts.append(f"{shop_new} shop items")
            parts.append("auto update")
            msg = "auto: " + " + ".join(parts) + f" ({now})"
            subprocess.run(["git", "commit", "-m", msg], check=True)
            subprocess.run(["git", "push", "origin", "master"], check=True)
            print(f"  ✅ 已推送: {msg}")
        else:
            print("  ℹ️ 无变更，跳过推送")
    except Exception as e:
        print(f"  ❌ Git 失败: {e}")
    
    print(f"\n🎉 完成! {len(new_posts)} 文章 | {len(tools)} 工具 | {shop_new} 新商品")


if __name__ == "__main__":
    main()
