#!/usr/bin/env python3
"""
slowbuild 核心监控 - 存活 + 死链
每天早8点跑一次，挂了立刻告警，死链报告
"""

import requests, smtplib, json, re, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

EMAIL = {
    "smtp": "smtp.qq.com", "port": 465,
    "sender": "184723392@qq.com", "pw": "tiabxxqucyhzbhbj",
    "to": "184723392@qq.com",
}

MONITOR = [
    ("slowbuild 主站", "https://slowbuild.top"),
    ("order 点单", "https://order.slowbuild.top"),
]

SCAN_PAGES = [
    "https://slowbuild.top",
    "https://slowbuild.top/fortune.html",
    "https://slowbuild.top/admin.html",
]

TIMEOUT = 15


def send_email(subject, html):
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = EMAIL["sender"]
        msg["To"] = EMAIL["to"]
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL(EMAIL["smtp"], EMAIL["port"]) as s:
            s.login(EMAIL["sender"], EMAIL["pw"])
            s.sendmail(EMAIL["sender"], [EMAIL["to"]], msg.as_string())
        print("  📧 邮件已发送")
        return True
    except Exception as e:
        print(f"  ❌ 邮件失败: {e}")
        return False


def check_uptime():
    results = []
    for name, url in MONITOR:
        try:
            r = requests.get(url, timeout=TIMEOUT, allow_redirects=True)
            ok = r.status_code == 200
            results.append({"name": name, "url": url, "ok": ok, "code": r.status_code, "ms": round(r.elapsed.total_seconds() * 1000)})
        except:
            results.append({"name": name, "url": url, "ok": False, "code": 0, "ms": 0})
    # 挂了立即告警
    down = [r for r in results if not r["ok"]]
    if down:
        body = "⚠️ 站点故障！\n\n" + "\n".join(f"• {d['name']} {d['url']}" for d in down)
        send_email("🚨 站点故障告警！", f"<pre>{body}</pre>")
    return results


def scan_dead():
    dead, seen = [], set()
    for url in SCAN_PAGES:
        try:
            r = requests.get(url, timeout=TIMEOUT)
            if r.status_code >= 400:
                dead.append({"from": url, "to": url, "code": r.status_code})
                continue
            hrefs = re.findall(r'href=["\']([^"\']+)["\']', r.text)
            base = urlparse(url).netloc
            for h in hrefs[:50]:
                # 跳过锚点、JS、空链接
                h = h.strip()
                if not h or h.startswith(("#", "javascript:", "mailto:", "tel:")):
                    continue
                full = urljoin(url, h)
                if urlparse(full).netloc != base or full in seen:
                    continue
                seen.add(full)
                try:
                    # Vercel 不支持 HEAD，用 GET + stream
                    lr = requests.get(full, timeout=10, allow_redirects=True, stream=True)
                    if lr.status_code >= 400:
                        dead.append({"from": url, "to": full, "code": lr.status_code})
                except:
                    dead.append({"from": url, "to": full, "code": 0})
        except Exception as e:
            dead.append({"from": url, "to": url, "code": f"ERR:{e}"})
    return dead


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"📊 slowbuild 监控 - {now}")
    print("=" * 40)

    print("[1/2] 站点存活...")
    uptime = check_uptime()
    for s in uptime:
        print(f"  {'🟢' if s['ok'] else '🔴'} {s['name']} ({s['ms']}ms)")

    print("[2/2] 死链扫描...")
    dead = scan_dead()
    print(f"  → {len(dead)} 个死链" if dead else "  ✅ 无")

    # 构建邮件
    dcount = len(dead)
    dead_rows = ""
    if dead:
        for d in dead[:15]:
            dead_rows += f"<tr><td style='font-size:11px'>{d['from'][:40]}</td><td><a href='{d['to']}' style='color:#d73a49'>{d['to'][:50]}</a></td><td style='text-align:center'>{d['code']}</td></tr>"

    html = f"""
    <html><body style="font-family:Arial;max-width:650px;margin:0 auto;padding:20px">
    <h2>📊 slowbuild 日报 | {now}</h2>
    
    <h3>🌐 站点存活</h3>
    <table style="width:100%;border-collapse:collapse">
    <tr style="background:#f6f8fa"><th></th><th>站点</th><th>状态</th><th>响应</th></tr>"""
    for s in uptime:
        html += f"<tr><td>{'🟢' if s['ok'] else '🔴'}</td><td>{s['name']}</td><td>{'正常' if s['ok'] else '❌挂了'}</td><td>{s['ms']}ms</td></tr>"
    html += "</table>"

    if dead:
        html += f"""<h3 style='color:#d73a49'>🔗 死链 ({dcount}个)</h3>
        <table style='width:100%;font-size:12px;background:#fff5f5'>
        <tr style='background:#ffe0e0'><th>来源页</th><th>死链</th><th>状态</th></tr>{dead_rows}</table>"""
    else:
        html += "<h3>✅ 死链扫描</h3><p>无死链</p>"

    html += "<hr style='border-top:1px solid #eee;margin:20px 0'><p style='color:#999;font-size:12px'>🤖 slowbuild.top 自动监控</p></body></html>"

    send_email(f"slowbuild 日报 - {now}", html)
    print("✅ 完成")


if __name__ == "__main__":
    main()
