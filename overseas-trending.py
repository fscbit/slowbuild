#!/usr/bin/env python3
"""
海外工具趋势日报 - 从服务器直发 184723392@qq.com
Product Hunt · Reddit工具帖 · Hacker News · GitHub Trending
每天早8点(北京时间)发送
"""

import requests, smtplib, json, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

EMAIL = {
    "smtp": "smtp.qq.com", "port": 465,
    "sender": "184723392@qq.com", "pw": "tiabxxqucyhzbhbj",
    "to": "184723392@qq.com",
}
UA = "Mozilla/5.0 (compatible; slowbuild-bot/1.0)"
TIMEOUT = 20


def send_email(subject, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject; msg["From"] = EMAIL["sender"]; msg["To"] = EMAIL["to"]
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL(EMAIL["smtp"], EMAIL["port"]) as s:
        s.login(EMAIL["sender"], EMAIL["pw"])
        s.sendmail(EMAIL["sender"], [EMAIL["to"]], msg.as_string())
    print("  ✅ 邮件已发送")


# ═══ Product Hunt ═══
def fetch_ph():
    items = []
    try:
        r = requests.get("https://www.producthunt.com/",
                         headers={"User-Agent": UA}, timeout=TIMEOUT)
        seen = set()
        for m in re.finditer(r'data-test="post-name"[^>]*>([^<]+)<', r.text):
            name = m.group(1).strip()
            if name not in seen:
                seen.add(name)
                items.append({"title": name, "url": f"https://www.producthunt.com/search?q={name}", "extra": ""})
                if len(items) >= 10:
                    break
    except:
        pass
    return items


# ═══ Reddit 工具帖 ═══
def fetch_reddit():
    items = []
    subs = [("InternetIsBeautiful", "互联网好物"), ("software", "软件推荐"),
            ("webdev", "Web开发"), ("programming", "编程")]
    for sub, label in subs:
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/top.json?t=week&limit=6&raw_json=1",
                headers={"User-Agent": "python:slowbuild-bot:v1.0"}, timeout=TIMEOUT)
            for post in r.json().get("data", {}).get("children", []):
                d = post["data"]
                url = d.get("url", "")
                if url.startswith("http") and "reddit" not in url:
                    items.append({
                        "title": d.get("title", ""),
                        "url": url,
                        "extra": f"r/{sub} | 👍{d.get('score',0)}",
                    })
        except:
            pass
    return sorted(items, key=lambda x: int(re.search(r'(\d+)', x.get('extra','0')).group(1) if re.search(r'(\d+)', x.get('extra','0')) else 0), reverse=True)[:15]


# ═══ Hacker News ═══
def fetch_hn():
    items = []
    try:
        r = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=TIMEOUT)
        ids = r.json()[:20]
        for story_id in ids:
            try:
                s = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json", timeout=10).json()
                title = s.get("title", "")
                url = s.get("url", f"https://news.ycombinator.com/item?id={story_id}")
                score = s.get("score", 0)
                # 只要跟工具/产品/技术相关的
                if any(k in title.lower() for k in ["show hn", "tool", "app", "launch", "open source"]):
                    items.append({"title": title, "url": url, "extra": f"👍{score}"})
            except:
                pass
        return items[:10]
    except:
        return []


# ═══ GitHub Trending ═══
def fetch_github():
    items = []
    try:
        r = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": f"stars:>100 created:>{(datetime.now()-timedelta(days=7)).strftime('%Y-%m-%d')}",
                    "sort": "stars", "order": "desc", "per_page": 10},
            headers={"Accept": "application/vnd.github.v3+json"}, timeout=TIMEOUT)
        for repo in r.json().get("items", []):
            items.append({
                "title": repo["full_name"],
                "url": repo["html_url"],
                "extra": f"⭐{repo['stargazers_count']} | {repo.get('language','')}",
            })
        return items
    except:
        return []


# ═══ HTML ═══
def build_html(ph, reddit, hn, github):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def table(title, items, sub="", color="#0366d6"):
        if not items:
            return f"<h3 style='color:{color}'>{title}</h3><p style='color:#999'>暂无数据</p>"
        rows = ""
        for i, item in enumerate(items[:12]):
            extra = item.get('extra', '')
            rows += f"<tr><td style='padding:4px 8px'>{i+1}</td><td style='padding:4px 8px'><a href='{item['url']}' style='color:#0366d6'>{item['title'][:70]}</a></td><td style='padding:4px 8px;font-size:12px;color:#666;white-space:nowrap'>{extra}</td></tr>"
        return f"""<h3 style='color:{color}'>{title} ({len(items)})</h3>
        <table style='width:100%;border-collapse:collapse;font-size:14px'>
        <tr style='background:#f6f8fa'><th style='width:30px'>#</th><th>内容</th><th>信息</th></tr>
        {rows}</table>{sub}"""

    return f"""
    <html><body style="font-family:Arial;max-width:700px;margin:0 auto;padding:20px">
    <h2>🌍 海外工具趋势日报 | {now}</h2>
    <p style='color:#888'>覆盖 Product Hunt · Reddit · Hacker News · GitHub | 💡 写博客素材+找上架灵感</p>

    {table("🔥 Product Hunt 今日热门", ph)}

    {table("💬 Reddit 热门工具推荐", reddit, "<p style='color:#888;font-size:12px'>来自 r/InternetIsBeautiful r/software r/webdev r/programming</p>")}

    {table("📰 Hacker News 工具帖", hn)}

    {table("⭐ GitHub 热门新项目", github)}

    <hr style='margin:20px 0;border-top:1px solid #eee'>
    <p style='color:#666;font-size:13px'>💡 怎么用：挑感兴趣的工具 → 写测评/教程博客 → 导流 slowbuild.top → 上架卖 EXE 下载</p>
    <p style='color:#999;font-size:12px'>🤖 服务器自动发送 | slowbuild.top</p>
    </body></html>"""


def main():
    print(f"🌍 海外工具趋势 - {datetime.now()}")
    print("=" * 40)

    print("[1/4] Product Hunt...")
    ph = fetch_ph()
    print(f"  → {len(ph)} 条")

    print("[2/4] Reddit...")
    reddit = fetch_reddit()
    print(f"  → {len(reddit)} 条")

    print("[3/4] Hacker News...")
    hn = fetch_hn()
    print(f"  → {len(hn)} 条")

    print("[4/4] GitHub Trending...")
    github = fetch_github()
    print(f"  → {len(github)} 条")

    html = build_html(ph, reddit, hn, github)
    send_email(f"🌍 海外工具趋势 - {datetime.now().strftime('%m/%d')}", html)
    print("✅ 完成")


if __name__ == "__main__":
    main()
