"""
订单模块 — 添加到 server.py
在 server.py 末尾 app.run() 之前导入即可
"""
import sqlite3, uuid, smtplib, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from pathlib import Path
from flask import request, jsonify

# Config
BASE_DIR = Path(__file__).parent
PRODUCTS_FILE = BASE_DIR.parent / "products.json"
DB_FILE = BASE_DIR / "orders.db"
DOWNLOAD_BASE = "https://www.slowbuild.top/downloads"

SMTP_HOST = "smtp.qq.com"
SMTP_PORT = 465
SMTP_USER = "184723392@qq.com"
SMTP_PASS = "tiabxxqucyhzbhbj"
FROM_NAME = "SlowBuild"

def _load_products():
    import json
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _get_db():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def _init_orders():
    conn = _get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
        product_id TEXT NOT NULL, product_name TEXT NOT NULL, product_type TEXT NOT NULL,
        price REAL NOT NULL, currency TEXT NOT NULL DEFAULT 'USD',
        buyer_email TEXT NOT NULL, buyer_name TEXT DEFAULT '', buyer_address TEXT DEFAULT '',
        payment_method TEXT NOT NULL, payment_txid TEXT DEFAULT '',
        payment_amount REAL DEFAULT 0, payment_currency TEXT DEFAULT '',
        download_sent INTEGER DEFAULT 0, notes TEXT DEFAULT '')""")
    conn.execute("""CREATE TABLE IF NOT EXISTS download_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL,
        accessed_at TEXT NOT NULL, ip TEXT DEFAULT '',
        FOREIGN KEY(order_id) REFERENCES orders(id))""")
    conn.commit()
    conn.close()

def _find_product(product_id):
    products = _load_products()
    for p in products:
        if p.get("id") == product_id:
            return p
    return None

def _send_email(to_email, subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, [to_email], msg.as_string())
        return True, "sent"
    except Exception as e:
        return False, str(e)

def _build_download_email(order, product):
    order_id = order["id"]
    product_name = order["product_name"]
    dl_link = None
    if order.get("product_type") == "digital":
        exe = product.get("exeFile", product_name.replace(" ", "_") + ".zip")
        dl_link = f"{DOWNLOAD_BASE}/{order_id}/{exe}"

    html = f"""<div style="max-width:600px;margin:0 auto;font-family:system-ui,sans-serif">
<div style="background:#1a1a1a;padding:32px;border-radius:12px 12px 0 0;text-align:center">
  <h1 style="color:#e87d4b;margin:0">🎉 Payment Confirmed!</h1>
  <p style="color:#aaa;margin:12px 0 0">Thank you for your purchase</p>
</div>
<div style="background:#fff;padding:32px;border-radius:0 0 12px 12px;border:1px solid #e5e5e0;border-top:none">
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="padding:8px 0;color:#888;font-size:14px">Order</td><td style="padding:8px 0;font-weight:600">#{order_id[:8]}</td></tr>
    <tr><td style="padding:8px 0;color:#888;font-size:14px">Product</td><td style="padding:8px 0;font-weight:600">{product_name}</td></tr>
    <tr><td style="padding:8px 0;color:#888;font-size:14px">Price</td><td style="padding:8px 0;font-weight:600;color:#e87d4b">${order['price']:.2f} USD</td></tr>
  </table>"""

    if dl_link:
        html += f"""
  <div style="margin:24px 0;text-align:center">
    <a href="{dl_link}" style="display:inline-block;padding:14px 36px;background:#1a1a1a;color:#fff;border-radius:8px;text-decoration:none;font-size:16px;font-weight:600">📥 Download Now</a>
    <p style="color:#888;font-size:12px;margin-top:8px">Link valid for 30 days · Single-user license</p>
  </div>"""
    else:
        html += """
  <div style="margin:24px 0;padding:16px;background:#fef8e7;border:1px solid #f5d76e;border-radius:8px">
    <p style="margin:0;color:#8a6d3b;font-size:14px">📦 This is a physical product. We'll ship it within 3 business days.</p>
  </div>"""

    html += f"""
  <hr style="border:none;border-top:1px solid #e5e5e0;margin:24px 0">
  <p style="color:#888;font-size:13px">Questions? Reply to this email or visit <a href="https://www.slowbuild.top" style="color:#e87d4b">slowbuild.top</a></p>
  <p style="color:#aaa;font-size:12px">Order ID: {order_id}</p>
</div></div>"""
    return html


PAYONEER_LINK = "https://link.payoneer.com/Token?t=6DA42646128B4562913488D8DABA0DC3&src=pl"
PAYPAL_ME = "https://paypal.me/slowbuild"
PAYPAL_VERIFY_URL = "https://ipnpb.paypal.com/cgi-bin/webscr"


def register_order_routes(app):
    _init_orders()

    @app.route("/api/order", methods=["POST"])
    def create_order():
        data = request.get_json(force=True)
        product_id = data.get("product_id", "").strip()
        email = data.get("email", "").strip().lower()
        payment_method = data.get("payment_method", "payoneer").strip().lower()
        name = data.get("name", "").strip()
        address = data.get("address", "").strip()

        if not product_id or not email:
            return jsonify({"ok": False, "error": "product_id and email required"}), 400
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return jsonify({"ok": False, "error": "invalid email"}), 400

        product = _find_product(product_id)
        if not product:
            return jsonify({"ok": False, "error": f"product not found"}), 404

        order_id = "SLW-" + uuid.uuid4().hex[:12].upper()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        conn = _get_db()
        conn.execute("""INSERT INTO orders (id, created_at, status, product_id, product_name, product_type,
                       price, currency, buyer_email, buyer_name, buyer_address, payment_method)
                       VALUES (?, ?, 'pending', ?, ?, ?, ?, 'USD', ?, ?, ?, ?)""",
                     (order_id, now, product_id, product.get("name", product_id),
                      product.get("type", "digital"), product.get("price", 0),
                      email, name, address, payment_method))
        conn.commit()

        pay_urls = {"payoneer": PAYONEER_LINK, "paypal": PAYPAL_ME}
        redirect_url = pay_urls.get(payment_method)

        if product.get("price", 0) <= 0:
            conn.execute("UPDATE orders SET status='confirmed', payment_txid='free' WHERE id=?", (order_id,))
            conn.commit()
            ok, _ = _send_email(email, f"Your SlowBuild Download — {product.get('name', 'Free Tool')}",
                              _build_download_email(dict(conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()), product))
            conn.execute("UPDATE orders SET download_sent=? WHERE id=?", (1 if ok else 0, order_id))
            conn.commit()
            conn.close()
            return jsonify({"ok": True, "order_id": order_id, "status": "confirmed", "email_sent": ok, "redirect_url": None})

        conn.close()
        return jsonify({"ok": True, "order_id": order_id, "status": "pending", "redirect_url": redirect_url,
                        "message": "Complete payment and we'll email your download link."})

    @app.route("/api/ipn/paypal", methods=["POST"])
    def paypal_ipn():
        import urllib.request
        verify_data = "cmd=_notify-validate&" + request.get_data(as_text=True)
        req = urllib.request.Request(PAYPAL_VERIFY_URL, data=verify_data.encode(),
                                      headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "SlowBuild-IPN/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.read().decode() != "VERIFIED":
                    return "INVALID", 400
        except:
            return "ERROR", 500

        payment_status = request.form.get("payment_status", "")
        txn_id = request.form.get("txn_id", "")
        mc_gross = float(request.form.get("mc_gross", 0))
        mc_currency = request.form.get("mc_currency", "USD")
        payer_email = request.form.get("payer_email", "")
        custom = request.form.get("custom", "")

        if payment_status != "Completed":
            return "OK", 200

        conn = _get_db()
        order = None
        if custom:
            order = conn.execute("SELECT * FROM orders WHERE id=?", (custom,)).fetchone()
        if not order:
            order = conn.execute("SELECT * FROM orders WHERE buyer_email=? AND status='pending' ORDER BY created_at DESC LIMIT 1",
                                 (payer_email,)).fetchone()
        if not order:
            conn.close()
            return "OK", 200

        existing = conn.execute("SELECT id FROM orders WHERE payment_txid=?", (txn_id,)).fetchone()
        if existing:
            conn.close()
            return "OK", 200

        conn.execute("UPDATE orders SET status='confirmed', payment_txid=?, payment_amount=?, payment_currency=? WHERE id=?",
                     (txn_id, mc_gross, mc_currency, order["id"]))
        conn.commit()

        product = _find_product(order["product_id"]) or {}
        ok, _ = _send_email(order["buyer_email"], f"Your SlowBuild Download — {order['product_name']}",
                           _build_download_email(dict(order), product))
        conn.execute("UPDATE orders SET download_sent=? WHERE id=?", (1 if ok else 0, order["id"]))
        conn.commit()
        conn.close()
        return "OK", 200

    @app.route("/api/order/<order_id>/confirm", methods=["POST"])
    def confirm_order(order_id):
        conn = _get_db()
        order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            conn.close()
            return jsonify({"ok": False, "error": "not found"}), 404
        if order["status"] == "confirmed":
            conn.close()
            return jsonify({"ok": True, "message": "already confirmed"})
        data = request.get_json(silent=True) or {}
        txid = data.get("txid", "manual-" + uuid.uuid4().hex[:8])
        conn.execute("UPDATE orders SET status='confirmed', payment_txid=?, payment_amount=? WHERE id=?",
                     (txid, order["price"], order_id))
        conn.commit()
        product = _find_product(order["product_id"]) or {}
        ok, err = _send_email(order["buyer_email"], f"Your SlowBuild Download — {order['product_name']}",
                              _build_download_email(dict(order), product))
        conn.execute("UPDATE orders SET download_sent=? WHERE id=?", (1 if ok else 0, order_id))
        conn.commit()
        conn.close()
        return jsonify({"ok": True, "order_id": order_id, "email_sent": ok, "email_error": err if not ok else None})

    @app.route("/api/order/<order_id>/resend", methods=["POST"])
    def resend_email(order_id):
        conn = _get_db()
        order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            conn.close()
            return jsonify({"ok": False, "error": "not found"}), 404
        product = _find_product(order["product_id"]) or {}
        ok, err = _send_email(order["buyer_email"], f"Your SlowBuild Download — {order['product_name']}",
                              _build_download_email(dict(order), product))
        conn.execute("UPDATE orders SET download_sent=? WHERE id=?", (1 if ok else 0, order_id))
        conn.commit()
        conn.close()
        return jsonify({"ok": ok, "error": err if not ok else None})

    @app.route("/api/orders", methods=["GET"])
    def list_orders():
        status = request.args.get("status", "")
        limit = int(request.args.get("limit", 100))
        conn = _get_db()
        if status:
            rows = conn.execute("SELECT * FROM orders WHERE status=? ORDER BY created_at DESC LIMIT ?",
                                (status, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])

    @app.route("/api/order/<order_id>", methods=["GET"])
    def get_order(order_id):
        conn = _get_db()
        order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not order:
            conn.close()
            return jsonify({"ok": False, "error": "not found"}), 404
        conn.close()
        return jsonify({"order": dict(order)})

    @app.route("/api/order-stats", methods=["GET"])
    def order_stats():
        conn = _get_db()
        total = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM orders WHERE status='pending'").fetchone()[0]
        confirmed = conn.execute("SELECT COUNT(*) FROM orders WHERE status='confirmed'").fetchone()[0]
        revenue = conn.execute("SELECT COALESCE(SUM(price),0) FROM orders WHERE status='confirmed'").fetchone()[0]
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE created_at LIKE ?", (today + "%",)).fetchone()[0]
        conn.close()
        return jsonify({"total_orders": total, "pending": pending, "confirmed": confirmed,
                        "revenue_usd": round(revenue, 2), "today_orders": today_orders})

    print("📋 Order routes registered on /api/order*")
