#!/usr/bin/env python3
"""
fortune.slowbuild.top — 独立命理占卜站
端口 5002，API 代理到 slowbuild 后端 (5000)
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# slowbuild 后端（本机5000端口，所有命理API都在那）
BACKEND = "http://localhost:5000"

# fortune.html 的静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE = os.path.join(STATIC_DIR, "fortune.html")


@app.route("/")
def index():
    """返回 fortune.html，自动替换 BACKEND 为当前域名"""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        html = f.read()
    # 把硬编码的 trycloudflare 替换成相对路径
    html = html.replace(
        "var BACKEND=parent.BACKEND||'https://academy-commented-titles-horizon.trycloudflare.com'",
        "var BACKEND='/'"
    )
    return html


# ═══════════════════════════════════════════
# API 代理：全部转发到 slowbuild 后端
# ═══════════════════════════════════════════

FORTUNE_APIS = ["bazi", "astro", "numerology", "tatrot", "fengshui",
                "iching", "palm", "name_analysis", "geo", "i18n"]


@app.route("/api/<path:path>", methods=["GET", "POST", "OPTIONS"])
def proxy_api(path):
    """代理所有 /api/* 请求到 localhost:5000"""
    target_url = f"{BACKEND}/api/{path}"
    try:
        if request.method == "GET":
            resp = requests.get(target_url, headers=dict(request.headers),
                               params=request.args, timeout=30)
        else:
            resp = requests.post(target_url, headers={"Content-Type": "application/json"},
                                data=request.get_data(), timeout=30)
        return (resp.content, resp.status_code, {"Content-Type": "application/json"})
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "后端服务未启动，请稍后重试"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5002))
    print(f"🔮 fortune.slowbuild.top 启动")
    print(f"   端口: {PORT}")
    print(f"   API代理: {BACKEND}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
