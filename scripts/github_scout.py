#!/usr/bin/env python3
"""
GitHub 工具挖掘脚本 — slowbuild.top
=====================================
自动扫描 GitHub 上快速增长的开源工具项目，
筛选适合封装为 EXE 或提供在线服务的候选。

用法:
    python github_scout.py                  # 完整扫描，输出报告
    python github_scout.py --quick          # 快速扫描（仅排名）
    python github_scout.py --output report.md  # 输出到指定文件
    python github_scout.py --cron           # cron 模式（仅输出新发现）

环境变量（可选）:
    GITHUB_TOKEN     GitHub Personal Access Token（提升 API 限额）
    SLOWBUILD_DATA   数据存储目录（默认 ./scout_data）
"""

import os
import sys
import json
import time
import hashlib
import argparse
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from pathlib import Path

# ─── 配置 ───────────────────────────────────────────────
CONFIG = {
    # GitHub API 配置
    "github_api": "https://api.github.com",
    "token": os.environ.get("GITHUB_TOKEN", ""),
    # 筛选阈值
    "min_stars": 500,
    "min_stars_rising": 300,  # 新星项目最低 stars
    "max_age_days": 365,       # 只关心一年内的新项目
    # 优先语言（易封装）
    "preferred_languages": [
        "Python", "Go", "TypeScript", "JavaScript", "Node.js"
    ],
    # 排除语言（难封装）
    "excluded_languages": [
        "C", "C++", "C#", "Java", "Kotlin", "Swift",
        "Rust", "Haskell", "Scala", "Dart", "Lua",
    ],
    # 排除关键词（不是工具的项目）
    "exclude_keywords": [
        "awesome", "list", "interview", "roadmap",
        "tutorial", "course", "book", "guide",
        "framework", "library", "sdk",
        "gpt", "llm", "agent", "skill",  # AI agent 类泛滥
    ],
    # 目标关键词（工具类）
    "target_keywords": [
        "cli", "tool", "converter", "processor",
        "generator", "downloader", "extractor",
        "compressor", "merger", "splitter",
        "ocr", "pdf", "image", "video", "audio",
        "subtitle", "ebook", "markdown",
    ],
    # 分类关键词映射
    "categories": {
        "PDF工具": ["pdf", "ocr"],
        "图片处理": ["image", "photo", "picture", "wallpaper", "screenshot"],
        "文件转换": ["converter", "convert", "transform", "transcode"],
        "文本处理": ["text", "markdown", "document", "translate"],
        "音视频": ["video", "audio", "subtitle", "media", "tts", "voice"],
        "开发者工具": ["cli", "dev", "build", "docker", "api"],
        "效率办公": ["organizer", "ebook", "audiobook", "productivity", "batch"],
    },
    # 输出目录
    "data_dir": os.environ.get("SLOWBUILD_DATA", str(Path(__file__).parent / "scout_data")),
    "report_dir": str(Path(__file__).parent.parent),
}


def api_request(endpoint, params=None):
    """调用 GitHub REST API，带速率限制处理"""
    url = f"{CONFIG['github_api']}/{endpoint}"
    if params:
        qs = urlencode(params)
        url += f"?{qs}"

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "slowbuild-tool-scout/1.0",
    }
    if CONFIG["token"]:
        headers["Authorization"] = f"token {CONFIG['token']}"

    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as e:
        if e.code == 403:
            # 速率限制
            reset_time = int(e.headers.get("X-RateLimit-Reset", 0))
            wait = max(reset_time - time.time(), 10)
            print(f"  ⚠️  API 速率限制，等待 {wait:.0f}s...")
            time.sleep(min(wait, 60))
            return api_request(endpoint, params)
        elif e.code == 422:
            print(f"  ⚠️  API 422 (查询语法可能有问题): {endpoint}")
            return {}
        else:
            print(f"  ⚠️  HTTP {e.code}: {endpoint}")
            return {}
    except URLError as e:
        print(f"  ⚠️  网络错误: {e}")
        return {}


def search_repos(query, min_stars, per_page=30, sort="stars", order="desc"):
    """
    搜索 GitHub 仓库
    query: 搜索关键词（支持 GitHub 搜索语法）
    """
    q = f"{query} stars:>{min_stars} fork:false"
    results = []
    for page in range(1, 3):  # 最多 2 页
        params = {
            "q": q,
            "sort": sort,
            "order": order,
            "per_page": per_page,
            "page": page,
        }
        data = api_request("search/repositories", params)
        items = data.get("items", [])
        if not items:
            break
        results.extend(items)
        if len(items) < per_page:
            break
        time.sleep(2)  # 避免速率限制
    return results


def fetch_new_hot_repos(min_stars=1000, days=365):
    """获取最近 X 天新建的高星项目"""
    date_cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    query = f"created:>{date_cutoff}"
    return search_repos(query, min_stars)


def fetch_trending_by_language(lang, min_stars=500, days=365):
    """按语言搜索趋势项目"""
    date_cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    query = f"language:{lang} created:>{date_cutoff}"
    return search_repos(query, min_stars)


def search_tool_category(category_keywords, min_stars=300):
    """按工具类别搜索"""
    kw = "+".join(category_keywords)
    query = f"{kw}+in:name,description"
    return search_repos(query, min_stars)


def filter_tools(repos):
    """
    按封装可行性过滤仓库
    返回: (入选列表, 排除列表)
    """
    passed = []
    excluded = []
    seen = set()

    for repo in repos:
        full_name = repo.get("full_name", "")
        if full_name in seen:
            continue
        seen.add(full_name)

        lang = repo.get("language") or ""
        desc = (repo.get("description") or "").lower()
        name = repo.get("name", "").lower()
        stars = repo.get("stargazers_count", 0)
        topics = [t.lower() for t in repo.get("topics", [])]
        all_text = f"{name} {desc} {' '.join(topics)}"

        reasons_skip = []

        # 排除：语言不匹配
        if lang in CONFIG["excluded_languages"]:
            reasons_skip.append(f"语言 {lang} 难封装")
            excluded.append({"repo": repo, "reason": reasons_skip})
            continue

        # 排除：stars 不够
        if stars < CONFIG["min_stars_rising"]:
            # 对 prefer 语言降低门槛
            if lang in CONFIG["preferred_languages"] and stars >= 200:
                pass  # 小星星但语言友好，允许
            else:
                reasons_skip.append(f"stars {stars} 不够")
                excluded.append({"repo": repo, "reason": reasons_skip})
                continue

        # 排除：纯库/框架/AI agent
        is_excluded = False
        for kw in CONFIG["exclude_keywords"]:
            if kw in all_text:
                reasons_skip.append(f"匹配排除词 '{kw}'")
                is_excluded = True
                break
        if is_excluded:
            excluded.append({"repo": repo, "reason": reasons_skip})
            continue

        # 加分：匹配工具关键词
        tool_score = sum(1 for kw in CONFIG["target_keywords"] if kw in all_text)

        # 减分：没有工具关键词且不是 CLI
        if tool_score == 0 and lang in CONFIG["preferred_languages"]:
            reasons_skip.append("没有工具关键词")
            excluded.append({"repo": repo, "reason": reasons_skip})
            continue

        # 分类
        category = classify_repo(all_text)

        passed.append({
            "full_name": full_name,
            "url": repo.get("html_url", ""),
            "stars": stars,
            "language": lang,
            "description": repo.get("description", ""),
            "category": category,
            "tool_score": tool_score,
            "created_at": repo.get("created_at", ""),
            "updated_at": repo.get("updated_at", ""),
            "topics": repo.get("topics", []),
        })

    return passed, excluded


def classify_repo(text):
    """根据文本自动分类"""
    for cat, keywords in CONFIG["categories"].items():
        for kw in keywords:
            if kw in text:
                return cat
    return "其他工具"


def prioritize_tools(tools):
    """
    工具评分排序
    score = stars_weight + language_bonus + tool_match_bonus
    """
    scored = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=CONFIG["max_age_days"])

    for t in tools:
        stars = t["stars"]
        lang = t["language"]
        tool_score = t["tool_score"]

        # 基础分：stars 对数
        base = min(stars / 1000, 50)  # 50 分封顶

        # 语言加分
        lang_bonus = 20 if lang in CONFIG["preferred_languages"] else 0

        # 工具匹配加分
        tool_bonus = min(tool_score * 5, 15)

        # 新项目加分（一年内）
        created = t.get("created_at", "")
        age_bonus = 0
        if created:
            try:
                dt = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                if dt > cutoff:
                    age_bonus = 15
            except ValueError:
                pass

        t["score"] = int(base + lang_bonus + tool_bonus + age_bonus)
        scored.append(t)

    return sorted(scored, key=lambda x: x["score"], reverse=True)


def generate_report(tools, title="Slowbuild 工具挖掘报告"):
    """生成 Markdown 报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 🔍 {title}",
        f"",
        f"> 自动生成：{now}",
        f"> 工具数量：{len(tools)}",
        f"",
        "---",
        "",
    ]

    # 按分类汇总
    by_category = {}
    for t in tools:
        cat = t["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(t)

    for cat in CONFIG["categories"]:
        items = by_category.get(cat, [])
        if not items:
            continue
        lines.append(f"## {cat}")
        lines.append("")
        lines.append("| Stars | 语言 | 项目 | 评分 | 说明 |")
        lines.append("|-------|------|------|------|------|")
        for t in items[:10]:
            name = t["full_name"]
            url = t["url"]
            lang = t["language"] or "?"
            desc = (t["description"] or "")[:60]
            md = f"[{name}]({url})"
            lines.append(f"| ⭐{t['stars']} | {lang} | {md} | {t['score']} | {desc} |")
        lines.append("")

    # 汇总排行 Top 20
    lines.append("## 🏆 综合推荐 Top 20")
    lines.append("")
    lines.append("| 排名 | Stars | 语言 | 项目 | 分类 | 评分 |")
    lines.append("|------|-------|------|------|------|------|")
    for i, t in enumerate(tools[:20], 1):
        name = t["full_name"]
        url = t["url"]
        lang = t["language"] or "?"
        md = f"[{name}]({url})"
        lines.append(f"| {i} | ⭐{t['stars']} | {lang} | {md} | {t['category']} | {t['score']} |")
    lines.append("")

    lines.append("---")
    lines.append(f"*报告由 github_scout.py 自动生成 | {now}*")
    return "\n".join(lines)


def save_state(tools, filename="scout_state.json"):
    """保存扫描状态，用于检测新项目"""
    state = {
        "last_scan": datetime.now().isoformat(),
        "repos": {t["full_name"]: t["stars"] for t in tools},
    }
    path = Path(CONFIG["data_dir"]) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False))
    return state


def load_state(filename="scout_state.json"):
    """加载上次扫描状态"""
    path = Path(CONFIG["data_dir"]) / filename
    if path.exists():
        return json.loads(path.read_text())
    return {"repos": {}, "last_scan": None}


def detect_new_tools(tools, old_state):
    """检测新项目"""
    old_repos = old_state.get("repos", {})
    new_tools = []
    star_changes = []

    for t in tools:
        name = t["full_name"]
        if name not in old_repos:
            new_tools.append(t)
        else:
            old_stars = old_repos[name]
            gain = t["stars"] - old_stars
            if gain > 100:
                star_changes.append({"tool": t, "gain": gain})

    return new_tools, star_changes


def cron_report(new_tools, star_changes):
    """生成 cron 精简报告"""
    lines = [
        f"## 📡 Slowbuild 工具监控 ({datetime.now().strftime('%m-%d %H:%M')})",
        "",
    ]
    if new_tools:
        lines.append(f"### 🆕 新发现 {len(new_tools)} 个工具")
        for t in sorted(new_tools, key=lambda x: x["stars"], reverse=True)[:10]:
            lines.append(f"- ⭐{t['stars']} [{t['full_name']}]({t['url']}) — {t.get('description','')[:80]}")
        lines.append("")
    else:
        lines.append("### 🆕 无新工具发现")
        lines.append("")

    if star_changes:
        lines.append(f"### 📈 Stars 增长显著（>100）")
        for sc in sorted(star_changes, key=lambda x: x["gain"], reverse=True)[:10]:
            t = sc["tool"]
            lines.append(f"- +{sc['gain']} ⭐ [{t['full_name']}]({t['url']}) (现 ⭐{t['stars']})")
        lines.append("")

    return "\n".join(lines)


def run_full_scan():
    """执行完整扫描"""
    print("=" * 60)
    print("🔍 Slowbuild GitHub 工具挖掘 - 完整扫描")
    print("=" * 60)

    all_repos = []

    # 1. 抓取新热门项目
    print("\n📡 1/6 扫描最近一年的高星项目...")
    time.sleep(1)
    hot = fetch_new_hot_repos(CONFIG["min_stars_rising"], CONFIG["max_age_days"])
    all_repos.extend(hot)
    print(f"   获取 {len(hot)} 个项目")

    # 2. 按语言搜索
    for lang in ["Python", "Go", "TypeScript"]:
        print(f"\n📡 按语言扫描 {lang}...")
        time.sleep(2)
        repos = fetch_trending_by_language(lang, CONFIG["min_stars"])
        all_repos.extend(repos)
        print(f"   获取 {len(repos)} 个项目")

    # 3. 按类别搜索
    category_queries = {
        "PDF工具": ["pdf", "tool"],
        "图片处理": ["image", "processing", "tool"],
        "文件转换": ["file", "converter"],
        "视频处理": ["video", "subtitle", "tool"],
        "OCR": ["ocr", "tool"],
        "TTS": ["tts", "text-to-speech"],
        "电子书": ["ebook", "converter"],
    }

    for cat_name, kw in category_queries.items():
        print(f"\n📡 类别搜索: {cat_name}...")
        time.sleep(2)
        repos = search_tool_category(kw, 200)
        all_repos.extend(repos)
        print(f"   获取 {len(repos)} 个项目")

    # 4. 过滤
    print(f"\n🔬 过滤分析（共 {len(all_repos)} 个原始项目）...")
    passed, excluded = filter_tools(all_repos)
    print(f"   ✅ 通过: {len(passed)}")
    print(f"   ❌ 排除: {len(excluded)}")

    # 排除原因统计
    reason_count = {}
    for e in excluded:
        for r in e["reason"]:
            reason_count[r] = reason_count.get(r, 0) + 1
    for reason, count in sorted(reason_count.items(), key=lambda x: -x[1])[:5]:
        print(f"      - {reason}: {count}")

    # 5. 评分排序
    print(f"\n📊 评分排序...")
    ranked = prioritize_tools(passed)
    print(f"   最终推荐: {len(ranked)} 个工具")

    # 6. 检测变化
    print(f"\n📈 对比上次扫描...")
    old_state = load_state()
    new_tools, star_changes = detect_new_tools(ranked, old_state)
    print(f"   新发现: {len(new_tools)} 个")
    print(f"   增长显著: {len(star_changes)} 个")

    # 保存状态
    save_state(ranked)
    print(f"\n💾 状态已保存到 {CONFIG['data_dir']}/scout_state.json")

    return ranked, new_tools, star_changes


def main():
    parser = argparse.ArgumentParser(
        description="Slowbuild GitHub 工具挖掘脚本"
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="快速扫描（仅前 3 步）"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="报告输出路径（默认 ../TOOL-SCOUT-REPORT.md）"
    )
    parser.add_argument(
        "--cron", action="store_true",
        help="Cron 模式：仅输出新发现和变化"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅打印，不保存状态"
    )
    args = parser.parse_args()

    # 执行扫描
    if args.quick:
        print("⚡ 快速扫描模式")
        all_repos = fetch_new_hot_repos(500, 30)
        passed, _ = filter_tools(all_repos)
        ranked = prioritize_tools(passed)
        new_tools, star_changes = [], []
    else:
        ranked, new_tools, star_changes = run_full_scan()

    # 输出
    if args.cron:
        report = cron_report(new_tools, star_changes)
        print("\n" + report)
    else:
        report = generate_report(ranked)

    output_path = args.output or str(Path(__file__).parent.parent / "TOOL-SCOUT-REPORT.md")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(report, encoding="utf-8")
    print(f"\n📄 报告已写入: {output_path}")

    # 打印摘要
    print(f"\n{'='*60}")
    print(f"🏆 Top 10 推荐工具:")
    for i, t in enumerate(ranked[:10], 1):
        emoji = "🆕" if t in new_tools else "  "
        print(f"  {i:2}. {emoji} ⭐{t['stars']:<6} [{t['category']}] {t['full_name']} (评分: {t['score']})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
