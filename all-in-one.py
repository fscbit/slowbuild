#!/usr/bin/env python3
"""
slowbuild 灵感全聚合 — 从服务器直发 184723392@qq.com
国内热搜 + 海外趋势 + 站点监控 + 工具发现
每天早8点一封汇总邮件
"""

import requests, smtplib, json, re, time, html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

EMAIL = {"smtp": "smtp.qq.com", "port": 465, "sender": "184723392@qq.com",
         "pw": "tiabxxqucyhzbhbj", "to": "184723392@qq.com"}
UA = "Mozilla/5.0 (compatible; slowbuild-bot/1.0)"
T = 20  # timeout


def send(subject, html):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject; msg["From"] = EMAIL["sender"]; msg["To"] = EMAIL["to"]
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL(EMAIL["smtp"], EMAIL["port"]) as s:
            s.login(EMAIL["sender"], EMAIL["pw"])
            s.sendmail(EMAIL["sender"], [EMAIL["to"]], msg.as_string())
        return True
    except Exception as e:
        print(f"  ❌ 邮件: {e}")
        return False


def http(url, **kw):
    kw.setdefault("headers", {"User-Agent": UA}); kw.setdefault("timeout", T)
    return requests.get(url, **kw)


# ══════════════════════════════════════════
# 国内热搜
# ══════════════════════════════════════════

def fetch_baidu():
    items = []
    try:
        r = http("https://top.baidu.com/board?tab=realtime")
        m = re.search(r'<!--s-data:(.*?)-->', r.text, re.DOTALL)
        if m:
            data = json.loads(m.group(1))
            for card in data.get("data", {}).get("cards", []):
                for item in card.get("content", []):
                    items.append({"title": item.get("word", ""), "url": item.get("url", f"https://www.baidu.com/s?wd={item.get('word','')}"), "info": str(item.get("hotScore", ""))})
        return items[:12]
    except:
        return []


def fetch_weibo():
    items = []
    try:
        r = http("https://weibo.com/ajax/side/hotSearch", headers={"User-Agent": UA, "Referer": "https://weibo.com/"})
        for item in r.json().get("data", {}).get("realtime", [])[:12]:
            word = item.get("word", "").strip()
            if word:
                items.append({"title": word, "url": f"https://s.weibo.com/weibo?q={word}", "info": str(item.get("num", item.get("raw_hot", "")))})
        return items
    except:
        return []


def fetch_zhihu():
    items = []
    try:
        r = http("https://api.zhihu.com/topstory/hot-list")
        for item in r.json().get("data", []):
            t = item.get("target", {})
            qid = t.get("id", "")
            items.append({
                "title": t.get("title", ""),
                "url": f"https://www.zhihu.com/question/{qid}",
                "info": item.get("detail_text", "")  # detail_text 在 target 外面
            })
        return items[:12]
    except:
        return []


def fetch_bilibili():
    items = []
    try:
        r = http("https://api.bilibili.com/x/web-interface/popular?ps=12",
                 headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"})
        for item in r.json().get("data", {}).get("list", []):
            items.append({"title": item.get("title", ""), "url": f"https://www.bilibili.com/video/{item.get('bvid','')}", "info": f"{item.get('stat',{}).get('view',0)}播放"})
        return items
    except:
        return []


def fetch_v2ex():
    items = []
    try:
        r = http("https://www.v2ex.com/api/topics/hot.json")
        for item in r.json()[:12]:
            items.append({"title": item.get("title", ""), "url": f"https://www.v2ex.com/t/{item.get('id','')}", "info": f"{item.get('replies',0)}回复"})
        return items
    except:
        return []


# ══════════════════════════════════════════
# 海外趋势
# ══════════════════════════════════════════

def fetch_producthunt():
    """从 Atom Feed 抓取（北京服务器可访问）"""
    items = []
    try:
        r = http("https://www.producthunt.com/feed",
                 headers={"User-Agent": "Mozilla/5.0 (compatible; slowbuild-bot/1.0)"})
        # 解析 Atom XML
        for m in re.finditer(r'<entry>.*?</entry>', r.text, re.DOTALL):
            entry = m.group(0)
            title_m = re.search(r'<title>([^<]+)</title>', entry)
            link_m = re.search(r'<link rel="alternate" type="text/html" href="([^"]+)"', entry)
            desc_m = re.search(r'<content[^>]*>(.*?)</content>', entry, re.DOTALL)
            if title_m and link_m:
                title = title_m.group(1).strip()
                url = link_m.group(1)
                desc = ""
                if desc_m:
                    raw = html.unescape(desc_m.group(1))  # 解码 &lt;p&gt; 等
                    desc = re.sub(r'<[^>]+>', '', raw).strip()[:30]
                items.append({"title": title, "url": url, "info": desc})
            if len(items) >= 10:
                break
    except:
        pass
    return items


def fetch_reddit():
    """Reddit 被 GFW 屏蔽，从北京服务器无法访问"""
    return []


def fetch_hackernews():
    """使用 Algolia HN API，一次请求获取全部（北京服务器友好）"""
    items = []
    try:
        r = http("https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=10")
        for hit in r.json().get("hits", []):
            title = hit.get("title", "")
            url = hit.get("url", f"https://news.ycombinator.com/item?id={hit.get('objectID','')}")
            score = hit.get("points", 0) or 0
            items.append({"title": title, "url": url, "info": f"👍{score}"})
        return items[:10]
    except:
        return []


def fetch_devto():
    items = []
    try:
        r = http("https://dev.to/api/articles?tag=showdev&per_page=10")
        for a in r.json():
            items.append({"title": a.get("title", ""), "url": a.get("url", ""), "info": f"❤️{a.get('positive_reactions_count',0)}"})
        return items[:10]
    except:
        return []


# ══════════════════════════════════════════
# 站点监控
# ══════════════════════════════════════════

def check_sites():
    sites = [("slowbuild主站", "https://slowbuild.top"), ("order点单", "https://order.slowbuild.top")]
    results = []
    for name, url in sites:
        try:
            r = http(url)
            results.append({"name": name, "ok": r.status_code == 200, "ms": round(r.elapsed.total_seconds()*1000)})
        except:
            results.append({"name": name, "ok": False, "ms": 0})
    # 挂了单独告警
    down = [s for s in results if not s["ok"]]
    if down:
        body = "⚠️ 故障:\n" + "\n".join(f"• {s['name']}" for s in down)
        send("🚨 站点故障！", f"<pre>{body}</pre>")
    return results


# ══════════════════════════════════════════
# HTML 邮件
# ══════════════════════════════════════════

def tbl(title, items, color="#0366d6"):
    if not items:
        return f"<h4 style='color:{color}'>{title} <span style='color:#999;font-weight:normal'>(无)</span></h4>"
    rows = "".join(f"<tr><td style='padding:3px 8px;font-size:12px'>{i+1}</td><td style='padding:3px 8px'><a href='{item['url']}' style='color:#0366d6'>{item['title'][:55]}</a></td><td style='padding:3px 8px;font-size:11px;color:#888;white-space:nowrap'>{item.get('info','')}</td></tr>" for i, item in enumerate(items[:12]))
    return f"""<h4 style='color:{color};margin-bottom:4px'>{title} ({len(items)})</h4>
    <table style='width:100%;border-collapse:collapse;font-size:13px;margin-bottom:12px'>
    {rows}</table>"""


def build(now, sites, baidu, weibo, zhihu, bili, v2ex, ph, reddit, hn, devto):
    up = "".join(f"<span style='margin-right:16px'>{'🟢' if s['ok'] else '🔴'} {s['name']} ({s['ms']}ms)</span>" for s in sites)
    total = len(baidu)+len(weibo)+len(zhihu)+len(bili)+len(v2ex)+len(ph)+len(reddit)+len(hn)+len(devto)

    return f"""
    <html><body style="font-family:Arial;max-width:720px;margin:0 auto;padding:16px">
    <h2>🔥 slowbuild 灵感日报 | {now}</h2>
    <p style='color:#888;font-size:13px'>{up}<br>共抓取 <b>{total}</b> 条灵感素材</p>

    <hr style='border:0;border-top:2px solid #e36209;margin:12px 0'>
    <h3 style='color:#e36209'>🇨🇳 国内热搜</h3>
    {tbl("📰 百度热搜", baidu, "#de4c2a")}
    {tbl("💬 微博热搜", weibo, "#e05244")}
    {tbl("🤔 知乎热榜", zhihu, "#0066ff")}
    {tbl("📺 B站热门", bili, "#fb7299")}
    {tbl("💻 V2EX 技术热帖", v2ex, "#334455")}

    <hr style='border:0;border-top:2px solid #0366d6;margin:12px 0'>
    <h3 style='color:#0366d6'>🌍 海外工具趋势</h3>
    {tbl("🔥 Product Hunt", ph, "#da552f")}
    {tbl("💬 Reddit 工具帖", reddit)}
    {tbl("📰 Hacker News", hn, "#ff6600")}
    {tbl("📝 Dev.to Show", devto, "#4b367c")}

    <hr style='margin:12px 0;border-top:1px solid #eee'>
    <p style='color:#666;font-size:12px'>💡 用法：看到跟工具/效率/占卜/转换相关的 → 写博客蹭流量 → 导流 slowbuild.top</p>
    <p style='color:#999;font-size:11px'>🤖 服务器自动 | slowbuild.top</p>
    </body></html>"""


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"🔥 slowbuild 灵感全聚合 - {now}")
    print("=" * 50)

    print("[站点] 存活检查...")
    sites = check_sites()

    print("[国内] 百度...")
    baidu = fetch_baidu()
    print(f"[国内] 微博...")
    weibo = fetch_weibo()
    print(f"[国内] 知乎...")
    zhihu = fetch_zhihu()
    print(f"[国内] B站...")
    bili = fetch_bilibili()
    print(f"[国内] V2EX...")
    v2ex = fetch_v2ex()

    print(f"[海外] ProductHunt...")
    ph = fetch_producthunt()
    print(f"[海外] Reddit...")
    reddit = fetch_reddit()
    print(f"[海外] HN...")
    hn = fetch_hackernews()
    print(f"[海外] Dev.to...")
    devto = fetch_devto()

    html = build(now, sites, baidu, weibo, zhihu, bili, v2ex, ph, reddit, hn, devto)
    ok = send(f"🔥 slowbuild 灵感日报 - {now}", html)
    status = "✅" if ok else "❌"
    print(f"{status} 完成 | 百度{len(baidu)} 微博{len(weibo)} 知乎{len(zhihu)} B站{len(bili)} V2EX{len(v2ex)} | PH{len(ph)} Reddit{len(reddit)} HN{len(hn)} Dev{len(devto)}")


if __name__ == "__main__":
    main()
