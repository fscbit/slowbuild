#!/usr/bin/env python3
"""
国内热搜聚合器 - 百度/微博/知乎/B站/头条 热门话题
每天早8点跑一次，汇总发邮件 → 内容灵感直接拿来用
"""

import requests, smtplib, json, re, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

EMAIL = {
    "smtp": "smtp.qq.com", "port": 465,
    "sender": "184723392@qq.com", "pw": "tiabxxqucyhzbhbj",
    "to": "184723392@qq.com",
}

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def send_email(subject, html):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject; msg["From"] = EMAIL["sender"]; msg["To"] = EMAIL["to"]
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL(EMAIL["smtp"], EMAIL["port"]) as s:
            s.login(EMAIL["sender"], EMAIL["pw"])
            s.sendmail(EMAIL["sender"], [EMAIL["to"]], msg.as_string())
        print("  📧 邮件已发送")
    except Exception as e:
        print(f"  ❌ 邮件失败: {e}")


# ═══ 1. 百度热搜 ═══
def fetch_baidu():
    items = []
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        # 从页面数据提取
        m = re.search(r'<!--s-data:(.*?)-->', r.text, re.DOTALL)
        if m:
            data = json.loads(m.group(1))
            cards = data.get("data", {}).get("cards", [])
            for card in cards:
                for item in card.get("content", []):
                    items.append({
                        "title": item.get("word", item.get("query", "")),
                        "url": item.get("url", f"https://www.baidu.com/s?wd={item.get('word','')}"),
                        "heat": item.get("hotScore", item.get("heat_score", "")),
                        "desc": item.get("desc", ""),
                    })
        return items[:15]
    except:
        return []


# ═══ 2. 微博热搜 ═══
def fetch_weibo():
    items = []
    try:
        r = requests.get(
            "https://weibo.com/ajax/side/hotSearch",
            headers={"User-Agent": UA, "Referer": "https://weibo.com/"},
            timeout=15
        )
        data = r.json()
        realtime = data.get("data", {}).get("realtime", [])
        for item in realtime[:15]:
            word = item.get("word", "").strip()
            if word:
                items.append({
                    "title": word,
                    "url": f"https://s.weibo.com/weibo?q={word}",
                    "heat": item.get("num", item.get("raw_hot", "")),
                    "desc": item.get("category", ""),
                })
        return items
    except:
        return []


# ═══ 3. 知乎热榜 ═══
def fetch_zhihu():
    items = []
    try:
        r = requests.get(
            "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=20",
            headers={"User-Agent": UA},
            timeout=15
        )
        for item in r.json().get("data", []):
            target = item.get("target", {})
            items.append({
                "title": target.get("title", ""),
                "url": f"https://www.zhihu.com/question/{target.get('id','')}",
                "heat": target.get("detail_text", ""),
                "desc": target.get("excerpt", "")[:80],
            })
        return items[:15]
    except:
        return []


# ═══ 4. B站热门 ═══
def fetch_bilibili():
    items = []
    try:
        r = requests.get(
            "https://api.bilibili.com/x/web-interface/popular?ps=15",
            headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"},
            timeout=15
        )
        for item in r.json().get("data", {}).get("list", []):
            items.append({
                "title": item.get("title", ""),
                "url": f"https://www.bilibili.com/video/{item.get('bvid','')}",
                "heat": f"{item.get('stat',{}).get('view',0)} 播放",
                "desc": item.get("desc", "")[:60],
            })
        return items
    except:
        return []


# ═══ 5. 今日头条热榜 ═══
def fetch_toutiao():
    items = []
    try:
        r = requests.get(
            "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
            headers={"User-Agent": UA},
            timeout=15
        )
        m = re.search(r'window\._ROUTER_DATA\s*=\s*({.*?});', r.text, re.DOTALL)
        if not m:
            m = re.search(r'"hotBoardList":(\[.*?\])', r.text, re.DOTALL)
        if m:
            try:
                raw = m.group(1)
                board = json.loads(raw)
                if isinstance(board, dict):
                    board = board.get("list", board.get("data", board.get("hotBoardList", [])))
                for item in board[:15]:
                    items.append({
                        "title": item.get("Title", item.get("title", item.get("word", ""))),
                        "url": f"https://www.toutiao.com/trending/{item.get('ClusterId','')}" if item.get("ClusterId") else "#",
                        "heat": item.get("HotValue", item.get("hot_value", "")),
                        "desc": item.get("Label", item.get("label", "")),
                    })
            except:
                pass
        return items
    except:
        return []


# ═══ HTML 邮件 ═══
def build_html(baidu, weibo, zhihu, bili, toutiao):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(baidu) + len(weibo) + len(zhihu) + len(bili) + len(toutiao)

    def make_table(title, items, color):
        if not items:
            return f"<h3 style='color:{color}'>{title}</h3><p>暂无数据</p>"
        rows = ""
        for i, item in enumerate(items[:12]):
            rows += f"<tr><td style='padding:4px 8px'>{i+1}</td><td style='padding:4px 8px'><a href='{item['url']}' style='color:#0366d6;text-decoration:none'>{item['title'][:50]}</a></td><td style='padding:4px 8px;font-size:12px;color:#666'>{item.get('heat','')}</td></tr>"
        return f"""<h3 style='color:{color}'>{title} ({len(items)}条)</h3>
        <table style='width:100%;border-collapse:collapse;font-size:14px'>
        <tr style='background:#f6f8fa'><th style='text-align:left;width:30px'>#</th><th style='text-align:left'>话题</th><th style='text-align:left'>热度</th></tr>
        {rows}</table>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto;padding:20px">
    <h2>🔥 国内热搜日报 | {now}</h2>
    <p>共抓取 <b>{total}</b> 条热门话题 | 💡 挑相关话题做内容</p>
    
    {make_table("📰 百度热搜", baidu, "#de4c2a")}
    <br>
    {make_table("💬 微博热搜", weibo, "#e05244")}
    <br>
    {make_table("🤔 知乎热榜", zhihu, "#0066ff")}
    <br>
    {make_table("📺 B站热门", bili, "#fb7299")}
    <br>
    {make_table("📱 头条热榜", toutiao, "#ed4040")}
    
    <hr style="margin:20px 0;border-top:1px solid #eee">
    <p style="color:#666;font-size:13px">💡 怎么用：看到跟「工具」「效率」「在线转换」「玄学占卜」相关的话题 → 写文章蹭流量 → 导流 slowbuild.top</p>
    <p style="color:#999;font-size:12px">🤖 slowbuild.top 自动生成</p>
    </body></html>"""


def main():
    now = datetime.now().strftime("%H:%M")
    print(f"🔥 国内热搜聚合 - {now}")
    print("=" * 40)

    print("[1/5] 百度热搜...")
    baidu = fetch_baidu()
    print(f"  → {len(baidu)} 条")

    print("[2/5] 微博热搜...")
    weibo = fetch_weibo()
    print(f"  → {len(weibo)} 条")

    print("[3/5] 知乎热榜...")
    zhihu = fetch_zhihu()
    print(f"  → {len(zhihu)} 条")

    print("[4/5] B站热门...")
    bili = fetch_bilibili()
    print(f"  → {len(bili)} 条")

    print("[5/5] 头条热榜...")
    toutiao = fetch_toutiao()
    print(f"  → {len(toutiao)} 条")

    html = build_html(baidu, weibo, zhihu, bili, toutiao)
    send_email(f"🔥 国内热搜日报 - {datetime.now().strftime('%m/%d')}", html)
    print("✅ 完成")


if __name__ == "__main__":
    main()
