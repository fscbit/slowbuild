#!/usr/bin/env python3
"""
GitHub 热门项目自动抓取器
每天抓取高星标/高增长的开源工具，生成商品数据供 slowbuild 后台使用
"""

import requests
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ═══ 配置 ═══
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # 可选，设了能多抓
OUTPUT_DIR = Path(__file__).parent / "github-trending"
OUTPUT_FILE = OUTPUT_DIR / "products.json"
MAX_RESULTS = 20
MIN_STARS = 50

# 感兴趣的编程语言（工具类项目居多）
LANGUAGES = ["Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "C#"]

# 关键词过滤（只要工具/应用类，不要框架/库）
KEYWORDS = ["tool", "cli", "app", "generator", "converter", "downloader",
            "manager", "viewer", "editor", "crawler", "scraper", "monitor",
            "dashboard", "automation", "backup", "sync", "organizer"]

# 排除关键词（太专业的框架/库）
EXCLUDE_KEYWORDS = ["framework", "library", "sdk", "api-client", "wrapper",
                    "react", "vue", "component", "plugin", "middleware",
                    "protocol", "package", "binding", "extension"]

# 排除已知大项目（太出名，没必要上架）
EXCLUDE_REPOS = {
    "AutoGPT", "Significant-Gravitas/AutoGPT", "n8n-io/n8n",
    "yt-dlp/yt-dlp", "ytdl-org/youtube-dl", "flutter/flutter",
    "torvalds/linux", "microsoft/vscode", "microsoft/TypeScript",
    "facebook/react", "vuejs/vue", "angular/angular",
    "tensorflow/tensorflow", "pytorch/pytorch", "kubernetes/kubernetes",
    "ohmyzsh/ohmyzsh", "twbs/bootstrap", "django/django",
    "laravel/laravel", "spring-projects/spring-framework",
    "golang/go", "rust-lang/rust", "nodejs/node",
    "denoland/deno", "bun/bun", "supabase/supabase",
    "vercel/next.js", "sveltejs/svelte", "remix-run/remix",
    "tailwindlabs/tailwindcss", "vitejs/vite",
}

# 排除星标太多的项目（>10000 太出名，不新鲜）
MAX_STARS = 10000


def search_github(query, sort="stars", per_page=30):
    """搜索 GitHub 仓库"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    url = f"https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": sort,
        "order": "desc",
        "per_page": per_page
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code == 403:
        print("⚠️ API 限流，等 60 秒重试...")
        import time; time.sleep(60)
        resp = requests.get(url, headers=headers, params=params, timeout=30)

    resp.raise_for_status()
    return resp.json()


def is_tool_repo(repo):
    """判断是不是工具类项目（非框架/库）"""
    name = (repo.get("name", "") + " " + repo.get("description", "")).lower()

    # 有工具关键词
    has_keyword = any(kw in name for kw in KEYWORDS)

    # 没有框架/库关键词
    no_exclude = not any(kw in name for kw in EXCLUDE_KEYWORDS)

    # 有 README 且不太短
    has_readme = repo.get("description") and len(repo["description"]) > 20

    # 不是 archived/disabled
    is_active = not repo.get("archived") and not repo.get("disabled")

    return has_keyword and no_exclude and has_readme and is_active


def calculate_growth(repo):
    """计算增长速度（星星/天）"""
    created = datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ")
    days_old = max((datetime.now() - created).days, 1)
    stars_per_day = repo["stargazers_count"] / days_old
    return round(stars_per_day, 1)


def fetch_trending():
    """抓取热门工具项目"""
    print("=" * 50)
    print(f"🚀 GitHub 热门项目抓取器 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    all_repos = []

    # 按不同维度搜索
    queries = [
        # 本周创建的热门仓库
        f"stars:>{MIN_STARS} created:>{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')}",
        # 总星标最高的工具
        f"stars:>100 pushed:>{(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')}",
        # 近期更新的星标仓库
        f"stars:>{MIN_STARS} pushed:>{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')}",
    ]

    seen = set()
    for q in queries:
        try:
            data = search_github(q, per_page=30)
            print(f"\n🔍 搜索: {q[:60]}... → {data.get('total_count', 0)} 结果")

            for repo in data.get("items", []):
                if not repo or repo.get("id") is None:
                    continue
                if repo["id"] in seen:
                    continue
                if not repo.get("language"):
                    continue  # 跳过无语言的仓库
                seen.add(repo["id"])

                if is_tool_repo(repo):
                    # 排除大项目和黑名单
                    if repo["stargazers_count"] > MAX_STARS:
                        continue
                    if repo["full_name"] in EXCLUDE_REPOS:
                        continue
                    growth = calculate_growth(repo)
                    all_repos.append({
                        "name": repo["full_name"],
                        "url": repo["html_url"],
                        "description": repo.get("description", ""),
                        "stars": repo["stargazers_count"],
                        "forks": repo.get("forks_count", 0),
                        "language": repo.get("language", ""),
                        "topics": repo.get("topics", []),
                        "growth": growth,
                        "updated": repo["updated_at"],
                        "homepage": repo.get("homepage", ""),
                        "license": (repo.get("license") or {}).get("spdx_id", ""),
                    })
        except Exception as e:
            print(f"  ⚠️ 搜索失败: {e}")

    # 按增长速度排序
    all_repos.sort(key=lambda r: r["growth"], reverse=True)
    all_repos = all_repos[:MAX_RESULTS]

    print(f"\n✅ 找到 {len(all_repos)} 个工具类项目\n")

    return all_repos


def generate_products(repos):
    """生成 slowbuild 商品数据格式"""
    products = []

    for i, r in enumerate(repos):
        name = r["name"].split("/")[-1]
        # 生成 ID
        pid = name.lower().replace(" ", "-").replace("_", "-").replace(".", "-")[:30]

        product = {
            "id": f"github-{pid}",
            "type": "digital",
            "price": 4.99,
            "image": "",
            "buyLink": "",
            "buyLinkCN": "",
            "name": {
                "en": name,
                "zh-CN": f"{name} (GitHub {r['stars']}⭐)",
                "zh-TW": f"{name} (GitHub {r['stars']}⭐)"
            },
            "desc": {
                "en": f"{r['description']}\n\n⭐ {r['stars']} stars | 🍴 {r['forks']} forks | 📈 {r['growth']}/day\nLanguage: {r['language']}\nLicense: {r['license']}\nGitHub: {r['url']}",
                "zh-CN": f"{r['description']}\n\n⭐ {r['stars']} 星标 | 🍴 {r['forks']} Fork | 📈 日增 {r['growth']} 星\n语言: {r['language']}\n许可: {r['license']}\nGitHub: {r['url']}",
                "zh-TW": f"{r['description']}\n\n⭐ {r['stars']} 星標 | 🍴 {r['forks']} Fork | 📈 日增 {r['growth']} 星\n語言: {r['language']}\n許可: {r['license']}\nGitHub: {r['url']}"
            },
            "specs": {
                "en": [
                    f"⭐ {r['stars']} GitHub Stars",
                    f"📈 {r['growth']} stars/day growth",
                    f"💻 Language: {r['language']}",
                    f"📜 License: {r['license']}",
                    f"🔗 {r['url']}"
                ],
                "zh-CN": [
                    f"⭐ {r['stars']} GitHub 星标",
                    f"📈 日增 {r['growth']} 星",
                    f"💻 语言: {r['language']}",
                    f"📜 许可: {r['license']}",
                    f"🔗 {r['url']}"
                ],
                "zh-TW": [
                    f"⭐ {r['stars']} GitHub 星標",
                    f"📈 日增 {r['growth']} 星",
                    f"💻 語言: {r['language']}",
                    f"📜 許可: {r['license']}",
                    f"🔗 {r['url']}"
                ]
            },
            "shipping": {
                "en": f"📦 Source code + packaged EXE | ⭐ {r['stars']} GitHub stars",
                "zh-CN": f"📦 源码 + 打包 EXE | ⭐ {r['stars']} GitHub 星标",
                "zh-TW": f"📦 源碼 + 打包 EXE | ⭐ {r['stars']} GitHub 星標"
            }
        }
        products.append(product)

    return products


def print_summary(repos):
    """打印摘要"""
    print("\n" + "=" * 70)
    print(f"{'#':<4} {'项目':<30} {'语言':<12} {'⭐':<8} {'📈/天':<8} {'Forks'}")
    print("-" * 70)
    for i, r in enumerate(repos):
        name = r["name"].split("/")[-1][:28]
        lang = r["language"][:10] if r["language"] else "N/A"
        print(f"{i+1:<4} {name:<30} {lang:<12} {r['stars']:<8} {r['growth']:<8} {r['forks']}")


def main():
    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 抓取
    repos = fetch_trending()

    if not repos:
        print("❌ 没找到符合条件的项目")
        return

    # 打印摘要
    print_summary(repos)

    # 生成产品数据
    products = generate_products(repos)

    # 保存 JSON（供管理员查看/挑选）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    results_file = OUTPUT_DIR / f"trending_{timestamp}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "fetch_time": datetime.now().isoformat(),
            "repos": repos,
            "products": products
        }, f, ensure_ascii=False, indent=2)

    # 保存最新产品列表
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"\n📁 产品数据已保存: {OUTPUT_FILE}")
    print(f"📁 完整报告: {results_file}")
    print(f"\n💡 共 {len(products)} 个产品待上架，查看 JSON 文件选择上架")


if __name__ == "__main__":
    main()
