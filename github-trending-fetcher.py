#!/usr/bin/env python3
"""
GitHub 热门项目自动抓取器（双版）
- 开发者版：CLI/编程工具/自动化
- 普通人版：桌面软件/网页工具/GUI应用
每周一、五发送两封邮件到 184723392@qq.com
"""

import requests
import json
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from pathlib import Path

# ═══ 邮箱配置 ═══
EMAIL_CONFIG = {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 465,
    "sender": "184723392@qq.com",
    "password": "tiabxxqucyhzbhbj",
    "receiver": "184723392@qq.com",
}

# ═══ 抓取配置 ═══
OUTPUT_DIR = Path(__file__).parent / "github-trending"
MAX_RESULTS_PER_MODE = 10
MIN_STARS = 50
MAX_STARS = 10000
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# ═══ 过滤：排除大项目 ═══
EXCLUDE_REPOS = {
    "AutoGPT", "n8n-io/n8n", "yt-dlp/yt-dlp", "flutter/flutter",
    "torvalds/linux", "microsoft/vscode", "microsoft/TypeScript",
    "facebook/react", "vuejs/vue", "tensorflow/tensorflow", "pytorch/pytorch",
    "kubernetes/kubernetes", "ohmyzsh/ohmyzsh", "twbs/bootstrap",
    "django/django", "laravel/laravel", "golang/go", "rust-lang/rust",
    "nodejs/node", "denoland/deno", "bun/bun", "supabase/supabase",
    "vercel/next.js", "sveltejs/svelte", "tailwindlabs/tailwindcss",
    "vitejs/vite",
}

# ═══ 两套抓取策略 ═══
MODES = {
    "dev": {
        "label": "🛠️ 开发者工具",
        "email_subject_prefix": "🛠️ 开发者工具",
        "keywords": ["tool", "cli", "api", "generator", "converter", "downloader",
                      "manager", "viewer", "editor", "crawler", "scraper", "monitor",
                      "dashboard", "automation", "backup", "sync", "organizer",
                      "compiler", "debugger", "formatter", "linter", "profiler",
                      "database", "devops", "docker", "server", "proxy"],
        "exclude_keywords": ["framework", "library", "sdk", "api-client", "wrapper",
                              "react-component", "vue-component", "plugin", "middleware",
                              "protocol", "package", "binding", "extension"],
    },
    "consumer": {
        "label": "🎯 普通用户工具",
        "email_subject_prefix": "🎯 普通人也能用的工具",
        "keywords": ["desktop", "gui", "web app", "application", "software",
                      "notepad", "note", "calendar", "todo", "reminder",
                      "photo", "image", "video", "audio", "music", "media",
                      "player", "recorder", "editor", "viewer",
                      "pdf", "document", "spreadsheet", "presentation",
                      "file manager", "explorer", "launcher", "dock",
                      " clipboard", "screenshot", "screen recorder",
                      "password manager", "bookmark", "reader", "ebook",
                      "diagram", "flowchart", "mind map", "whiteboard",
                      "chat", "messaging", "email client", "calendar",
                      "weather", "clock", "timer", "stopwatch",
                      "calculator", "unit converter", "translator",
                      "dictionary", "encyclopedia",
                      "drawing", "painting", "design", "3d model",
                      "game engine", "game launcher", "emulator",
                      "cleaner", "optimizer", "uninstaller",
                      "zip", "compress", "extract", "archive",
                      "backup", "restore", "sync",
                      "browser", "privacy", "ad blocker",
                      "wallpaper", "theme", "customization",
                      "startup manager", "task manager", "process",
                      "system tray", "status bar",
                      "text-to-speech", "speech-to-text", "ocr",
                      "qr code", "barcode", "generator"],
        "exclude_keywords": ["framework", "library", "sdk", "api", "cli",
                              "command-line", "npm", "pip", "package",
                              "middleware", "node.js module", "webpack",
                              "component", "react", "vue", "angular",
                              "server-side", "backend", "database driver"],
    }
}


def search_github(query, per_page=20):
    """搜索 GitHub 仓库"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": per_page}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 403:
            print("  ⚠️ API 限流，等 60 秒重试...")
            import time; time.sleep(60)
            resp = requests.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  ⚠️ 搜索失败: {e}")
        return {"items": [], "total_count": 0}


def is_good_repo(repo, mode):
    """判断项目是否适合当前模式"""
    cfg = MODES[mode]

    name = (repo.get("name") or "")
    desc = (repo.get("description") or "")
    full_text = (name + " " + desc).lower()

    # 排除框架/库关键词
    if any(kw in full_text for kw in cfg["exclude_keywords"]):
        return False

    # 必须有描述
    if not desc or len(desc) < 10:
        return False

    # 不能是 archived/disabled
    if repo.get("archived") or repo.get("disabled"):
        return False

    # 要有匹配的关键词
    if any(kw in full_text for kw in cfg["keywords"]):
        return True

    # 兜底：描述够长且有实际内容
    if len(desc) > 50:
        return True

    return False


def calculate_growth(repo):
    """计算增长速度"""
    try:
        created = datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        days_old = max((datetime.now() - created).days, 1)
        return round(repo["stargazers_count"] / days_old, 1)
    except:
        return 0


def fetch_for_mode(mode):
    """按模式抓取"""
    queries = [
        f"stars:>{MIN_STARS} created:>{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}",
        f"stars:>200 pushed:>{(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')}",
        f"stars:>{MIN_STARS} pushed:>{(datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')}",
    ]

    seen = set()
    all_repos = []

    for q in queries:
        data = search_github(q, per_page=20)
        total = data.get("total_count", 0)
        print(f"  🔍 [{mode}] {q[:50]}... → {total} 结果")

        for repo in data.get("items", []):
            if not repo or not repo.get("id"):
                continue
            rid = repo["id"]
            if rid in seen:
                continue
            seen.add(rid)

            if not repo.get("language"):
                continue

            if repo["stargazers_count"] > MAX_STARS:
                continue
            if repo["full_name"] in EXCLUDE_REPOS:
                continue

            if is_good_repo(repo, mode):
                growth = calculate_growth(repo)
                all_repos.append({
                    "name": repo["full_name"],
                    "url": repo["html_url"],
                    "description": repo.get("description") or "",
                    "stars": repo["stargazers_count"],
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language") or "N/A",
                    "topics": repo.get("topics", []),
                    "growth": growth,
                    "updated": repo.get("updated_at", ""),
                    "homepage": repo.get("homepage") or "",
                    "license": (repo.get("license") or {}).get("spdx_id", ""),
                })

    # 按增长速度排序
    all_repos.sort(key=lambda r: r["growth"], reverse=True)
    return all_repos[:MAX_RESULTS_PER_MODE]


def build_email(repos, mode):
    """构建 HTML 邮件"""
    cfg = MODES[mode]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if not repos:
        return f"本次未找到符合条件的{cfg['label']}项目。"

    rows = ""
    for i, r in enumerate(repos):
        name = r["name"]
        desc = r["description"][:120]
        lang = r["language"]
        stars = r["stars"]
        growth = r["growth"]
        url = r["url"]
        homepage = r["homepage"]
        hp_html = f' | <a href="{homepage}" style="color:#28a745">🌐 演示站</a>' if homepage else ""

        rows += f"""
        <tr style="border-bottom:1px solid #eee">
            <td style="padding:10px;vertical-align:top">{i+1}</td>
            <td style="padding:10px;vertical-align:top">
                <a href="{url}" style="color:#0366d6;text-decoration:none;font-weight:bold">{name}</a>{hp_html}
                <br><span style="color:#666;font-size:13px">{desc}</span>
            </td>
            <td style="padding:10px;text-align:center;white-space:nowrap">{lang}</td>
            <td style="padding:10px;text-align:center;white-space:nowrap">⭐{stars}</td>
            <td style="padding:10px;text-align:center;white-space:nowrap">📈{growth}/天</td>
        </tr>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px">
    <h2 style="color:#24292e">🚀 GitHub 热门{cfg['label']} | 每周报告</h2>
    <p style="color:#666">抓取时间: {now_str} | 共找到 <b>{len(repos)}</b> 个项目</p>
    <table style="width:100%;border-collapse:collapse;font-size:14px">
        <tr style="background:#f6f8fa">
            <th style="padding:10px;text-align:left">#</th>
            <th style="padding:10px;text-align:left">项目</th>
            <th style="padding:10px;text-align:center">语言</th>
            <th style="padding:10px;text-align:center">⭐</th>
            <th style="padding:10px;text-align:center">📈/天</th>
        </tr>
        {rows}
    </table>
    <hr style="border:0;border-top:1px solid #eee;margin:20px 0">
    <p style="color:#666;font-size:13px">
        🛒 上架地址: <a href="https://slowbuild.top/admin.html">slowbuild.top/admin.html</a>
    </p>
    <p style="color:#999;font-size:12px">🤖 slowbuild.top 自动抓取</p>
    </body></html>"""


def send_one_email(repos, mode):
    """发送一封邮件"""
    cfg = MODES[mode]
    body = build_email(repos, mode)
    is_html = repos and True or False

    now_str = datetime.now().strftime("%m/%d %H:%M")
    subject = f"{cfg['email_subject_prefix']} - {now_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = EMAIL_CONFIG["receiver"]

    if is_html:
        msg.attach(MIMEText(body, "html", "utf-8"))
    else:
        msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.sendmail(EMAIL_CONFIG["sender"], [EMAIL_CONFIG["receiver"]], msg.as_string())
        print(f"  📧 [{mode}] 邮件已发送!")
    except Exception as e:
        print(f"  ⚠️ [{mode}] 邮件发送失败: {e}")


def print_table(repos, mode):
    """打印终端摘要"""
    cfg = MODES[mode]
    print(f"\n{'='*70}")
    print(f"  {cfg['label']} - {len(repos)} 个项目")
    print(f"{'='*70}")
    if not repos:
        print("  (无)")
        return
    print(f"  {'#':<4} {'项目':<32} {'语言':<10} {'⭐':<8} {'📈/天'}")
    print(f"  {'-'*60}")
    for i, r in enumerate(repos):
        name = r["name"].split("/")[-1][:30]
        lang = r["language"][:8]
        print(f"  {i+1:<4} {name:<32} {lang:<10} {r['stars']:<8} {r['growth']}")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"🚀 GitHub 双版抓取器 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 分别抓取
    for mode in ["dev", "consumer"]:
        print(f"\n📡 开始抓取 [{mode}] ...")
        repos = fetch_for_mode(mode)

        print_table(repos, mode)

        # 保存 JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        results_file = OUTPUT_DIR / f"trending_{mode}_{timestamp}.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump({
                "fetch_time": datetime.now().isoformat(),
                "mode": mode,
                "repos": repos,
            }, f, ensure_ascii=False, indent=2)

        # 发邮件
        send_one_email(repos, mode)

        # 间隔 3 秒，避免同时连 SMTP
        import time; time.sleep(3)

    print(f"\n✅ 完成！两封邮件已发送到 {EMAIL_CONFIG['receiver']}")
    print(f"📁 数据保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
