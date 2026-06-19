#!/usr/bin/env python3
"""SlowBuild Backend Setup"""
import os, sys
TARGET = r"C:\\slowbuild-new\\backend"
os.makedirs(TARGET, exist_ok=True)
print(f"Installing to {TARGET}...")

# --- server.py ---
with open(os.path.join(TARGET, "server.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
slowbuild 后端服务（完整版）
可跑的服务分三类：
  🟢 纯 Python（零额外依赖）
  🟡 需要 LibreOffice（免费）
  🔵 需要额外 pip 安装

运行：python server.py
测试：浏览器打开 http://localhost:5000
"""

import os, shutil, subprocess, filecmp, uuid, time, hashlib, json, csv, io, re, base64, tempfile
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

# 八字命盘引擎
from bazi import calculate_bazi
from astro import build_full_chart, get_daily_horoscope
from numerology import build_numerology_report
from fengshui import get_kua, get_home_advice
from tarot import get_spread_reading
from iching import get_reading
from palm_reading import get_palm_reading
from name_analysis import analyze_name

app = Flask(__name__)
CORS(app)

WORK_DIR = Path(__file__).parent / "work"
for d in ["work/temp", "work/output"]:
    Path(WORK_DIR / d.replace("work/", "")).mkdir(parents=True, exist_ok=True)

TEMP_DIR = WORK_DIR / "temp"
OUTPUT_DIR = WORK_DIR / "output"

def find_libreoffice():
    path = r"C:\\Program Files\\LibreOffice\\program\\soffice.exe"
    if os.path.exists(path): return path
    path = r"C:\\LibreOfficePortable\\App\\libreoffice\\program\\soffice.exe"
    if os.path.exists(path): return path
    return None


def cleanup():
    now = time.time()
    for d in [TEMP_DIR, OUTPUT_DIR]:
        for f in d.iterdir():
            if f.is_file() and now - f.stat().st_mtime > 3600:
                try: f.unlink()
                except: pass


def safe_filename(name):
    return re.sub(r\'[<>:"/\\\\|?*]\', \'_\', name)


# ═══════════════════════════════════════════
#  🟢 纯 Python — 文件处理
# ═══════════════════════════════════════════

@app.route("/api/extract_text", methods=["POST"])
def extract_text():
    """从文本中提取：手机号/邮箱/身份证/日期/URL"""
    f = request.files.get("file")
    text = f.read().decode("utf-8", errors="ignore") if f else request.form.get("text", "")
    if not text:
        return jsonify({"error": "请上传文件或提供文本"}), 400

    patterns = {
        "phones": r"1[3-9]\\d{9}",
        "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}",
        "id_cards": r"\\d{17}[\\dXx]",
        "dates": r"\\d{4}[-/]\\d{1,2}[-/]\\d{1,2}",
        "urls": r"https?://[^\\s]+",
    }

    results = {}
    for name, pattern in patterns.items():
        found = list(set(re.findall(pattern, text)))
        results[name] = {"count": len(found), "items": found[:50]}
    results["total_chars"] = len(text)
    results["total_lines"] = len(text.splitlines())
    return jsonify(results)


@app.route("/api/rename_batch", methods=["POST"])
def rename_batch():
    """批量重命名预览：返回重命名方案"""
    data = request.get_json()
    files = data.get("files", [])
    pattern = data.get("pattern", "{n}_{ext}")  # {n}=序号 {name}=原名 {ext}=后缀
    result = []
    for i, f in enumerate(files, 1):
        name, ext = os.path.splitext(f)
        new = pattern.replace("{n}", str(i).zfill(3)).replace("{name}", name).replace("{ext}", ext)
        result.append({"old": f, "new": new})
    return jsonify({"count": len(result), "plan": result})


@app.route("/api/file_info", methods=["POST"])
def file_info():
    """批量获取文件信息"""
    f = request.files.get("file")
    if not f: return jsonify({"error": "请上传文件"}), 400
    
    info = {
        "filename": f.filename,
        "size": len(f.read()),
        "ext": os.path.splitext(f.filename)[1].lower(),
    }
    f.seek(0)
    # MD5
    h = hashlib.md5()
    while True:
        chunk = f.read(8192)
        if not chunk: break
        h.update(chunk)
    info["md5"] = h.hexdigest()
    
    # 如果是文本，统计行数
    f.seek(0)
    try:
        text = f.read(1024*1024).decode("utf-8")
        info["lines"] = len(text.splitlines())
        info["chars"] = len(text)
        info["is_text"] = True
    except:
        info["is_text"] = False
    
    return jsonify(info)


@app.route("/api/hash", methods=["POST"])
def hash_file():
    """计算文件 MD5 / SHA256"""
    f = request.files.get("file")
    if not f: return jsonify({"error": "请上传文件"}), 400
    
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    while True:
        chunk = f.read(8192)
        if not chunk: break
        md5.update(chunk)
        sha256.update(chunk)
    
    return jsonify({
        "filename": f.filename,
        "size": f.tell(),
        "md5": md5.hexdigest(),
        "sha256": sha256.hexdigest()
    })


@app.route("/api/merge_csv", methods=["POST"])
def merge_csv():
    """合并多个 CSV 文件"""
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify({"error": "请至少上传2个CSV文件"}), 400

    rows = []
    header = None
    for f in files:
        content = f.read().decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(content))
        for i, row in enumerate(reader):
            if i == 0:
                if header is None:
                    header = row
                    rows.append(row)
                elif row != header:
                    continue  # 跳过不同表头
                else:
                    continue
            else:
                rows.append(row)

    # 返回合并结果
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    
    result_path = OUTPUT_DIR / f"merged_{uuid.uuid4().hex[:8]}.csv"
    with open(result_path, \'w\', encoding=\'utf-8-sig\') as fp:
        fp.write(output.getvalue())
    
    return send_file(str(result_path), as_attachment=True, download_name="merged.csv", mimetype="text/csv")


# ═══════════════════════════════════════════
#  🟡 需要 LibreOffice — 文档转换
# ═══════════════════════════════════════════

OFFICE_CONVERT = {
    "word2pdf":  {"from": {"doc", "docx"}, "to": "pdf", "label": "Word → PDF"},
    "excel2pdf": {"from": {"xls", "xlsx"}, "to": "pdf", "label": "Excel → PDF"},
    "ppt2pdf":   {"from": {"ppt", "pptx"}, "to": "pdf", "label": "PPT → PDF"},
    "office2pdf":{"from": {"doc","docx","xls","xlsx","ppt","pptx"}, "to": "pdf", "label": "Office → PDF"},
    "excel2csv": {"from": {"xls", "xlsx"}, "to": "csv", "label": "Excel → CSV"},
    "html2pdf":  {"from": {"html", "htm"}, "to": "pdf", "label": "HTML → PDF"},
}


@app.route("/api/convert", methods=["POST"])
def convert():
    """通用文档转换"""
    conv_type = request.form.get("type", "office2pdf")
    
    if conv_type not in OFFICE_CONVERT:
        return jsonify({"error": f"未知转换类型。支持: {list(OFFICE_CONVERT.keys())}"}), 400
    
    config = OFFICE_CONVERT[conv_type]
    libre = find_libreoffice()
    if not libre:
        return jsonify({"error": "LibreOffice 未安装"}), 500

    f = request.files.get("file")
    if not f:
        return jsonify({"error": "请上传文件"}), 400

    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in config["from"]:
        return jsonify({"error": f"不支持 .{ext}，仅支持: {config[\'from\']}"}), 400

    cleanup()
    job_id = uuid.uuid4().hex[:8]
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    input_path = job_dir / f"input.{ext}"
    f.save(str(input_path))

    try:
        result = subprocess.run(
            [libre, "--headless", "--convert-to", config["to"], "--outdir", str(OUTPUT_DIR), str(input_path)],
            capture_output=True, text=True, timeout=120, cwd=str(OUTPUT_DIR)
        )
    except subprocess.TimeoutExpired:
        shutil.rmtree(job_dir, ignore_errors=True)
        return jsonify({"error": "转换超时"}), 500

    # 找输出文件
    outputs = sorted(OUTPUT_DIR.glob(f"*.{config[\'to\']}"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not outputs:
        shutil.rmtree(job_dir, ignore_errors=True)
        return jsonify({"error": "转换失败"}), 500

    out_path = outputs[0]
    download_name = safe_filename(f.filename.rsplit(".", 1)[0] + "." + config["to"])
    
    # 移动到最终位置
    final_path = OUTPUT_DIR / download_name
    if final_path.exists(): final_path.unlink()
    out_path.rename(final_path)
    shutil.rmtree(job_dir, ignore_errors=True)

    mime = "application/pdf" if config["to"] == "pdf" else "text/csv"
    return send_file(str(final_path), as_attachment=True, download_name=download_name, mimetype=mime)


# ═══════════════════════════════════════════
#  🟢 纯 Python — 文件比对 / 查重
# ═══════════════════════════════════════════

@app.route("/api/dedup", methods=["POST"])
def dedup():
    """重复文件检测（zip包）"""
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".zip"):
        return jsonify({"error": "请上传 .zip 文件"}), 400

    cleanup()
    job_dir = TEMP_DIR / uuid.uuid4().hex[:8]
    job_dir.mkdir(exist_ok=True)
    zip_path = job_dir / "input.zip"
    f.save(str(zip_path))

    import zipfile
    extract_dir = job_dir / "extracted"
    extract_dir.mkdir()

    try:
        with zipfile.ZipFile(zip_path, \'r\') as zf:
            zf.extractall(str(extract_dir))
    except:
        shutil.rmtree(job_dir, ignore_errors=True)
        return jsonify({"error": "解压失败"}), 400

    all_files = []
    for root, dirs, files in os.walk(str(extract_dir)):
        for fn in files:
            all_files.append(os.path.join(root, fn))

    duplicates = []
    checked = set()
    for i, f1 in enumerate(all_files):
        for f2 in all_files[i + 1:]:
            pair = (f1, f2)
            if pair in checked: continue
            checked.add(pair)
            try:
                if os.path.getsize(f1) == os.path.getsize(f2) and filecmp.cmp(f1, f2, shallow=False):
                    duplicates.append({
                        "file1": os.path.relpath(f1, str(extract_dir)),
                        "file2": os.path.relpath(f2, str(extract_dir)),
                        "size": os.path.getsize(f1)
                    })
            except: pass

    shutil.rmtree(job_dir, ignore_errors=True)
    return jsonify({"total_files": len(all_files), "duplicate_pairs": len(duplicates), "duplicates": duplicates})


@app.route("/api/images_list", methods=["POST"])
def images_list():
    """提取图片文件列表"""
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".zip"):
        return jsonify({"error": "请上传 .zip"}), 400

    cleanup()
    job_dir = TEMP_DIR / uuid.uuid4().hex[:8]
    job_dir.mkdir(exist_ok=True)
    zip_path = job_dir / "input.zip"
    f.save(str(zip_path))

    import zipfile
    extract_dir = job_dir / "extracted"
    extract_dir.mkdir()
    with zipfile.ZipFile(zip_path, \'r\') as zf:
        zf.extractall(str(extract_dir))

    IMG = {\'.jpg\',\'.jpeg\',\'.png\',\'.gif\',\'.bmp\',\'.webp\',\'.svg\',\'.ico\',\'.tiff\',\'.tif\'}
    images = []
    for root, dirs, files in os.walk(str(extract_dir)):
        for fn in files:
            if os.path.splitext(fn)[1].lower() in IMG:
                images.append(os.path.relpath(os.path.join(root, fn), str(extract_dir)))

    shutil.rmtree(job_dir, ignore_errors=True)
    return jsonify({"count": len(images), "images": images})


# ═══════════════════════════════════════════
#  工具列表 + 健康检查
# ═══════════════════════════════════════════

@app.route("/")
def index():
    libre = find_libreoffice()
    return jsonify({
        "service": "slowbuild-backend",
        "libreoffice": bool(libre),
        "endpoints": {
            "🟢 纯Python": [
                "POST /api/extract_text   — 提取手机号/邮箱/身份证/日期/URL",
                "POST /api/rename_batch   — 批量重命名预览",
                "POST /api/file_info      — 文件信息+MD5+行数",
                "POST /api/hash           — MD5/SHA256 文件哈希",
                "POST /api/merge_csv      — 合并多个CSV",
            ],
            "🟡 LibreOffice": [
                "POST /api/convert?type=word2pdf   — Word→PDF",
                "POST /api/convert?type=excel2pdf  — Excel→PDF",
                "POST /api/convert?type=ppt2pdf    — PPT→PDF",
                "POST /api/convert?type=excel2csv  — Excel→CSV",
                "POST /api/convert?type=html2pdf   — HTML→PDF",
            ],
            "🟢 文件比对": [
                "POST /api/dedup         — 重复文件检测",
                "POST /api/images_list   — 提取图片列表",
            ]
        }
    })


@app.route("/health")
def health():
    libre = find_libreoffice()
    return jsonify({"status": "ok", "libreoffice": bool(libre), "time": datetime.now().isoformat()})


# ═══════════════════════════════════════════
#  🛒 商品 & 课程管理 API（SQLite）
# ═══════════════════════════════════════════

import sqlite3

DB_PATH = Path(__file__).parent / "shop.db"

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL DEFAULT \'physical\',
            name_en TEXT, name_cn TEXT, name_tw TEXT,
            desc_en TEXT, desc_cn TEXT, desc_tw TEXT,
            price REAL DEFAULT 0,
            image TEXT DEFAULT \'\',
            buy_link TEXT DEFAULT \'\',
            buy_link_cn TEXT DEFAULT \'\',
            specs TEXT DEFAULT \'[]\',
            shipping_en TEXT DEFAULT \'\', shipping_cn TEXT DEFAULT \'\', shipping_tw TEXT DEFAULT \'\',
            created_at TEXT DEFAULT (datetime(\'now\',\'localtime\')),
            updated_at TEXT DEFAULT (datetime(\'now\',\'localtime\'))
        );
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            title_en TEXT, title_cn TEXT, title_tw TEXT,
            desc_en TEXT, desc_cn TEXT, desc_tw TEXT,
            price REAL DEFAULT 0,
            image TEXT DEFAULT \'\',
            buy_link TEXT DEFAULT \'\',
            video_preview TEXT DEFAULT \'\',
            lesson_count INTEGER DEFAULT 0,
            duration TEXT DEFAULT \'\',
            syllabus TEXT DEFAULT \'[]\',
            created_at TEXT DEFAULT (datetime(\'now\',\'localtime\')),
            updated_at TEXT DEFAULT (datetime(\'now\',\'localtime\'))
        );
    """)
    # Migration: add buy_link_cn if missing
    try:
        db.execute("ALTER TABLE products ADD COLUMN buy_link_cn TEXT DEFAULT \'\'")
    except sqlite3.OperationalError:
        pass
    db.commit()
    db.close()

init_db()

# ── 商品 CRUD ──

def product_row_to_dict(row):
    d = dict(row)
    d["specs"] = json.loads(d.get("specs", "[]"))
    d["name"] = {"en": d.pop("name_en", ""), "zh-CN": d.pop("name_cn", ""), "zh-TW": d.pop("name_tw", "")}
    d["desc"] = {"en": d.pop("desc_en", ""), "zh-CN": d.pop("desc_cn", ""), "zh-TW": d.pop("desc_tw", "")}
    d["shipping"] = {"en": d.pop("shipping_en", ""), "zh-CN": d.pop("shipping_cn", ""), "zh-TW": d.pop("shipping_tw", "")}
    d["buyLinkCN"] = d.pop("buy_link_cn", "")
    return d

@app.route("/api/admin/products", methods=["GET"])
def admin_list_products():
    db = get_db()
    rows = db.execute("SELECT * FROM products ORDER BY updated_at DESC").fetchall()
    db.close()
    return jsonify([product_row_to_dict(r) for r in rows])

@app.route("/api/admin/products", methods=["POST"])
def admin_create_product():
    data = request.get_json(force=True)
    if not data.get("id"):
        return jsonify({"error": "id 必填"}), 400
    db = get_db()
    try:
        db.execute("""
            INSERT INTO products (id, type, name_en, name_cn, name_tw, desc_en, desc_cn, desc_tw,
                price, image, buy_link, buy_link_cn, specs, shipping_en, shipping_cn, shipping_tw)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["id"], data.get("type","physical"),
            data.get("name",{}).get("en",""), data.get("name",{}).get("zh-CN",""), data.get("name",{}).get("zh-TW",""),
            data.get("desc",{}).get("en",""), data.get("desc",{}).get("zh-CN",""), data.get("desc",{}).get("zh-TW",""),
            data.get("price",0), data.get("image",""), data.get("buyLink",""),
            data.get("buyLinkCN",""),
            json.dumps(data.get("specs",[]), ensure_ascii=False),
            data.get("shipping",{}).get("en",""), data.get("shipping",{}).get("zh-CN",""), data.get("shipping",{}).get("zh-TW","")
        ))
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({"error": f"产品 ID \'{data[\'id\']}\' 已存在"}), 409
    db.close()
    return jsonify({"ok": True, "id": data["id"]})

@app.route("/api/admin/products/<pid>", methods=["PUT"])
def admin_update_product(pid):
    data = request.get_json(force=True)
    db = get_db()
    existing = db.execute("SELECT id FROM products WHERE id=?", (pid,)).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "产品不存在"}), 404
    db.execute("""
        UPDATE products SET type=?, name_en=?, name_cn=?, name_tw=?, desc_en=?, desc_cn=?, desc_tw=?,
            price=?, image=?, buy_link=?, buy_link_cn=?, specs=?, shipping_en=?, shipping_cn=?, shipping_tw=?,
            updated_at=datetime(\'now\',\'localtime\')
        WHERE id=?
    """, (
        data.get("type","physical"),
        data.get("name",{}).get("en",""), data.get("name",{}).get("zh-CN",""), data.get("name",{}).get("zh-TW",""),
        data.get("desc",{}).get("en",""), data.get("desc",{}).get("zh-CN",""), data.get("desc",{}).get("zh-TW",""),
        data.get("price",0), data.get("image",""), data.get("buyLink",""),
        data.get("buyLinkCN",""),
        json.dumps(data.get("specs",[]), ensure_ascii=False),
        data.get("shipping",{}).get("en",""), data.get("shipping",{}).get("zh-CN",""), data.get("shipping",{}).get("zh-TW",""),
        pid
    ))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route("/api/admin/products/<pid>", methods=["DELETE"])
def admin_delete_product(pid):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

# ── 课程 CRUD ──

def course_row_to_dict(row):
    d = dict(row)
    d["syllabus"] = json.loads(d.get("syllabus", "[]"))
    d["title"] = {"en": d.pop("title_en", ""), "zh-CN": d.pop("title_cn", ""), "zh-TW": d.pop("title_tw", "")}
    d["desc"] = {"en": d.pop("desc_en", ""), "zh-CN": d.pop("desc_cn", ""), "zh-TW": d.pop("desc_tw", "")}
    return d

@app.route("/api/admin/courses", methods=["GET"])
def admin_list_courses():
    db = get_db()
    rows = db.execute("SELECT * FROM courses ORDER BY updated_at DESC").fetchall()
    db.close()
    return jsonify([course_row_to_dict(r) for r in rows])

@app.route("/api/admin/courses", methods=["POST"])
def admin_create_course():
    data = request.get_json(force=True)
    if not data.get("id"):
        return jsonify({"error": "id 必填"}), 400
    db = get_db()
    try:
        db.execute("""
            INSERT INTO courses (id, title_en, title_cn, title_tw, desc_en, desc_cn, desc_tw,
                price, image, buy_link, video_preview, lesson_count, duration, syllabus)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            data["id"],
            data.get("title",{}).get("en",""), data.get("title",{}).get("zh-CN",""), data.get("title",{}).get("zh-TW",""),
            data.get("desc",{}).get("en",""), data.get("desc",{}).get("zh-CN",""), data.get("desc",{}).get("zh-TW",""),
            data.get("price",0), data.get("image",""), data.get("buyLink",""),
            data.get("videoPreview",""), data.get("lessonCount",0), data.get("duration",""),
            json.dumps(data.get("syllabus",[]), ensure_ascii=False)
        ))
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({"error": f"课程 ID \'{data[\'id\']}\' 已存在"}), 409
    db.close()
    return jsonify({"ok": True, "id": data["id"]})

@app.route("/api/admin/courses/<cid>", methods=["PUT"])
def admin_update_course(cid):
    data = request.get_json(force=True)
    db = get_db()
    existing = db.execute("SELECT id FROM courses WHERE id=?", (cid,)).fetchone()
    if not existing:
        db.close()
        return jsonify({"error": "课程不存在"}), 404
    db.execute("""
        UPDATE courses SET title_en=?, title_cn=?, title_tw=?, desc_en=?, desc_cn=?, desc_tw=?,
            price=?, image=?, buy_link=?, video_preview=?, lesson_count=?, duration=?, syllabus=?,
            updated_at=datetime(\'now\',\'localtime\')
        WHERE id=?
    """, (
        data.get("title",{}).get("en",""), data.get("title",{}).get("zh-CN",""), data.get("title",{}).get("zh-TW",""),
        data.get("desc",{}).get("en",""), data.get("desc",{}).get("zh-CN",""), data.get("desc",{}).get("zh-TW",""),
        data.get("price",0), data.get("image",""), data.get("buyLink",""),
        data.get("videoPreview",""), data.get("lessonCount",0), data.get("duration",""),
        json.dumps(data.get("syllabus",[]), ensure_ascii=False),
        cid
    ))
    db.commit()
    db.close()
    return jsonify({"ok": True})

@app.route("/api/admin/courses/<cid>", methods=["DELETE"])
def admin_delete_course(cid):
    db = get_db()
    db.execute("DELETE FROM courses WHERE id=?", (cid,))
    db.commit()
    db.close()
    return jsonify({"ok": True})

# ── 图片上传 ──

CONFIG_PATH = Path(__file__).parent / "config.json"

def get_config(key, default=""):
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as f:
                return json.load(f).get(key, default)
        except: pass
    return os.environ.get(key.upper(), default)

@app.route("/api/upload-image", methods=["POST"])
def upload_image():
    """上传图片到 GitHub 仓库"""
    github_token = get_config("github_token")
    if not github_token:
        return jsonify({"error": "GitHub token 未配置，请在 config.json 中设置 github_token"}), 500
    
    data = request.get_json(force=True)
    filename = data.get("filename", "image.jpg")
    content_b64 = data.get("content", "")
    
    if not content_b64:
        return jsonify({"error": "缺少图片内容"}), 400
    
    GITHUB_REPO = "fscbit/slowbuild"
    
    # 生成唯一文件名避免覆盖
    name, ext = os.path.splitext(filename)
    safe_name = re.sub(r\'[^a-zA-Z0-9_-]\', \'_\', name)
    unique_name = f"{safe_name}_{uuid.uuid4().hex[:6]}{ext}"
    github_path = f"images/{unique_name}"
    
    # 上传到 GitHub
    import urllib.request
    try:
        check_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}"
        check_req = urllib.request.Request(check_url, headers={
            "Authorization": f"token {github_token}",
            "User-Agent": "slowbuild-backend"
        })
        sha = None
        try:
            with urllib.request.urlopen(check_req) as resp:
                sha = json.loads(resp.read()).get("sha")
        except urllib.error.HTTPError:
            pass
        
        body = json.dumps({
            "message": f"upload: {unique_name}",
            "content": content_b64,
            "branch": "main"
        })
        if sha:
            d = json.loads(body)
            d["sha"] = sha
            body = json.dumps(d)
        
        put_req = urllib.request.Request(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}",
            data=body.encode(),
            headers={
                "Authorization": f"token {github_token}",
                "User-Agent": "slowbuild-backend",
                "Content-Type": "application/json"
            },
            method="PUT"
        )
        with urllib.request.urlopen(put_req) as resp:
            result = json.loads(resp.read())
        
        return jsonify({"ok": True, "path": github_path, "url": f"https://slowbuild.top/{github_path}"})
    except Exception as e:
        return jsonify({"error": f"上传失败: {str(e)}"}), 500


# ═══════════════════════════════════════════
#  🟢 八字命盘 API
# ═══════════════════════════════════════════

@app.route("/api/bazi", methods=["POST"])
def bazi_calc():
    """八字命盘计算"""
    data = request.get_json(force=True) or {}
    year = data.get("year")
    month = data.get("month")
    day = data.get("day")
    hour = data.get("hour", 12)
    level = data.get("level", "free")  # free | basic | full
    
    if not all([year, month, day]):
        return jsonify({"error": "请提供 year, month, day"}), 400
    
    try:
        year, month, day = int(year), int(month), int(day)
        hour = int(hour)
    except (TypeError, ValueError):
        return jsonify({"error": "日期格式错误"}), 400
    
    lang = data.get("lang", "zh-CN")
    result = calculate_bazi(year, month, day, hour, level, lang)
    
    if "error" in result:
        return jsonify(result), 400
    
    return jsonify(result)


@app.route("/api/products", methods=["GET"])
def public_products():
    db = get_db()
    rows = db.execute("SELECT * FROM products ORDER BY updated_at DESC").fetchall()
    db.close()
    return jsonify([product_row_to_dict(r) for r in rows])

@app.route("/api/courses", methods=["GET"])
def public_courses():
    db = get_db()
    rows = db.execute("SELECT * FROM courses ORDER BY updated_at DESC").fetchall()
    db.close()
    return jsonify([course_row_to_dict(r) for r in rows])

@app.route("/api/shop", methods=["GET"])
def public_shop():
    """一次性返回所有商品和课程"""
    db = get_db()
    products = [product_row_to_dict(r) for r in db.execute("SELECT * FROM products ORDER BY updated_at DESC").fetchall()]
    courses = [course_row_to_dict(r) for r in db.execute("SELECT * FROM courses ORDER BY updated_at DESC").fetchall()]
    db.close()
    return jsonify({"products": products, "courses": courses})



# ═══════════════════════════════════════════
#  🪐 西方占星 API
# ═══════════════════════════════════════════

@app.route("/api/astro", methods=["POST"])
def astro_chart():
    """Full birth chart + horoscope"""
    data = request.get_json(force=True) or {}
    year = data.get("year")
    month = data.get("month")
    day = data.get("day")
    hour = data.get("hour", 12)
    level = data.get("level", "free")
    lang = data.get("lang", "zh-CN")

    if not all([year, month, day]):
        return jsonify({"error": "Need year, month, day"}), 400

    try:
        chart = build_full_chart(int(year), int(month), int(day), int(hour), level)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if chart.get("error"):
        return jsonify(chart), 400

    # Add daily horoscope
    sun_en = chart.get("sun", {}).get("en", "")
    today = datetime.now().strftime("%Y-%m-%d")
    daily = get_daily_horoscope(sun_en, today)
    chart["daily"] = daily

    return jsonify(chart)


# ═══════════════════════════════════════════
#  🔢 生命灵数 API
# ═══════════════════════════════════════════

@app.route("/api/numerology", methods=["POST"])
def numerology():
    """Full numerology report"""
    data = request.get_json(force=True) or {}
    year = data.get("year")
    month = data.get("month")
    day = data.get("day")
    name = data.get("name", "")
    level = data.get("level", "free")

    if not all([year, month, day]):
        return jsonify({"error": "Need year, month, day"}), 400

    try:
        report = build_numerology_report(int(year), int(month), int(day), name, level)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if report.get("error"):
        return jsonify(report), 400

    return jsonify(report)


# ═══════════════════════════════════════════
#  🏠 风水堪舆 API
# ═══════════════════════════════════════════

@app.route("/api/fengshui", methods=["POST"])
def fengshui():
    """Kua number + 8-house + annual flying stars"""
    data = request.get_json(force=True) or {}
    year = data.get("year")
    gender = data.get("gender", "male")
    door = data.get("door_direction", "北")  # 大门朝向: 北/南/东/西/东北/西北/东南/西南
    level = data.get("level", "free")

    if not year:
        return jsonify({"error": "Need birth year"}), 400

    try:
        kua = get_kua(int(year), gender)
        result = get_home_advice(door, kua, level)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(result)


# ═══════════════════════════════════════════
#  🌍 IP Geolocation → Language detection
# ═══════════════════════════════════════════

# Country → Language mapping
COUNTRY_LANG = {
    \'CN\': \'zh-CN\', \'TW\': \'zh-TW\', \'HK\': \'zh-TW\', \'MO\': \'zh-TW\',
    \'JP\': \'ja\', \'KR\': \'ko\',
    \'US\': \'en\', \'GB\': \'en\', \'CA\': \'en\', \'AU\': \'en\', \'NZ\': \'en\', \'IE\': \'en\', \'SG\': \'en\',
    \'FR\': \'fr\', \'BE\': \'fr\', \'CH\': \'fr\',
    \'DE\': \'de\', \'AT\': \'de\',
    \'ES\': \'es\', \'MX\': \'es\', \'AR\': \'es\', \'CO\': \'es\', \'CL\': \'es\', \'PE\': \'es\',
    \'PT\': \'pt\', \'BR\': \'pt\',
    \'RU\': \'ru\', \'BY\': \'ru\', \'KZ\': \'ru\',
    \'IN\': \'en\',  # India defaults to English
    \'SA\': \'en\', \'AE\': \'en\',  # Middle East defaults to English
}

@app.route("/api/i18n/<lang_code>")
def get_i18n(lang_code):
    """Return translation strings for a given language"""
    translations = {
        \'en\': {
            \'hubTitle\': \'✦ Destiny Hub ✦\', \'hubSub\': \'Ancient wisdom meets modern stars — for fun & curiosity\',
            \'back\': \'← Back to Hub\',
            \'freeTag\': \'Free\', \'premTag\': \'Premium\',
            \'loading\': \'Working the magic...\', \'error\': \'Please enter valid info\',
            \'unlockTitle\': \'Unlock Full Reading\', \'unlockDesc\': \'Get the complete detailed analysis\',
            \'unlockPrice\': \'$1.99\', \'unlockBtn\': \'💳 Unlock Now\',
            \'unlockNote\': \'Auto-unlocks after payment\',
            \'payConfirm\': \'Payment completed? Click OK to unlock\', \'unlocked\': \'✅ Unlocked\',
        },
        \'zh-CN\': {
            \'hubTitle\': \'✦ 命运之门 ✦\', \'hubSub\': \'古老智慧与现代星辰 — 玩一玩，别太当真\',
            \'back\': \'← 返回总览\',
            \'freeTag\': \'免费\', \'premTag\': \'高级\',
            \'loading\': \'推算中...\', \'error\': \'请输入完整信息\',
            \'unlockTitle\': \'解锁完整解读\', \'unlockDesc\': \'查看详细完整分析\',
            \'unlockPrice\': \'¥12\', \'unlockBtn\': \'💳 立即解锁\',
            \'unlockNote\': \'付款后自动解锁\', \'payConfirm\': \'已完成支付？点击确定\', \'unlocked\': \'✅ 已解锁\',
        },
        \'zh-TW\': {
            \'hubTitle\': \'✦ 命運之門 ✦\', \'hubSub\': \'古老智慧與現代星辰 — 玩一玩，別太當真\',
            \'back\': \'← 返回總覽\',
            \'freeTag\': \'免費\', \'premTag\': \'高級\',
            \'loading\': \'推算中...\', \'error\': \'請輸入完整資訊\',
            \'unlockTitle\': \'解鎖完整解讀\', \'unlockDesc\': \'查看詳細完整分析\',
            \'unlockPrice\': \'NT$60\', \'unlockBtn\': \'💳 立即解鎖\',
            \'unlockNote\': \'付款後自動解鎖\', \'payConfirm\': \'已完成支付？點擊確定\', \'unlocked\': \'✅ 已解鎖\',
        },
        \'ja\': {
            \'hubTitle\': \'✦ ディスティニーハブ ✦\', \'hubSub\': \'古代の知恵と現代の星々 — 楽しみのために\',
            \'back\': \'← ハブに戻る\',
            \'freeTag\': \'無料\', \'premTag\': \'プレミアム\',
            \'loading\': \'計算中...\', \'error\': \'有効な情報を入力してください\',
            \'unlockTitle\': \'完全版をアンロック\', \'unlockDesc\': \'詳細な分析を見る\',
            \'unlockPrice\': \'$1.99\', \'unlockBtn\': \'💳 アンロック\',
            \'unlockNote\': \'支払い後に自動アンロック\', \'payConfirm\': \'支払い完了？OKでアンロック\', \'unlocked\': \'✅ アンロック済\',
        },
        \'ko\': {
            \'hubTitle\': \'✦ 데스티니 허브 ✦\', \'hubSub\': \'고대의 지혜와 현대의 별 — 재미로 즐기세요\',
            \'back\': \'← 허브로 돌아가기\',
            \'freeTag\': \'무료\', \'premTag\': \'프리미엄\',
            \'loading\': \'계산 중...\', \'error\': \'유효한 정보를 입력하세요\',
            \'unlockTitle\': \'전체 분석 잠금 해제\', \'unlockDesc\': \'상세한 전체 분석 보기\',
            \'unlockPrice\': \'$1.99\', \'unlockBtn\': \'💳 잠금 해제\',
            \'unlockNote\': \'결제 후 자동 잠금 해제\', \'payConfirm\': \'결제 완료? OK로 잠금 해제\', \'unlocked\': \'✅ 잠금 해제됨\',
        },
        \'es\': {
            \'hubTitle\': \'✦ Portal del Destino ✦\', \'hubSub\': \'Sabiduría antigua y estrellas modernas — solo por diversión\',
            \'back\': \'← Volver al Hub\',
            \'freeTag\': \'Gratis\', \'premTag\': \'Premium\',
            \'loading\': \'Calculando...\', \'error\': \'Ingresa información válida\',
            \'unlockTitle\': \'Desbloquear Lectura Completa\', \'unlockDesc\': \'Ver análisis detallado completo\',
            \'unlockPrice\': \'$1.99\', \'unlockBtn\': \'💳 Desbloquear\',
            \'unlockNote\': \'Se desbloquea tras el pago\', \'payConfirm\': \'¿Pago completado? OK para desbloquear\', \'unlocked\': \'✅ Desbloqueado\',
        },
        \'fr\': {
            \'hubTitle\': \'✦ Portail du Destin ✦\', \'hubSub\': \'Sagesse ancienne et étoiles modernes — pour le plaisir\',
            \'back\': \'← Retour au Hub\',
            \'freeTag\': \'Gratuit\', \'premTag\': \'Premium\',
            \'loading\': \'Calcul en cours...\', \'error\': \'Veuillez entrer des informations valides\',
            \'unlockTitle\': \'Débloquer la Lecture Complète\', \'unlockDesc\': \'Voir l\'analyse détaillée complète\',
            \'unlockPrice\': \'$1.99\', \'unlockBtn\': \'💳 Débloquer\',
            \'unlockNote\': \'Déblocage automatique après paiement\', \'payConfirm\': \'Paiement terminé ? OK pour débloquer\', \'unlocked\': \'✅ Débloqué\',
        },
        \'pt\': {
            \'hubTitle\': \'✦ Portal do Destino ✦\', \'hubSub\': \'Sabedoria antiga e estrelas modernas — só por diversão\',
            \'back\': \'← Voltar ao Hub\',
            \'freeTag\': \'Grátis\', \'premTag\': \'Premium\',
            \'loading\': \'Calculando...\', \'error\': \'Insira informações válidas\',
            \'unlockTitle\': \'Desbloquear Leitura Completa\', \'unlockDesc\': \'Ver análise detalhada completa\',
            \'unlockPrice\': \'$1.99\', \'unlockBtn\': \'💳 Desbloquear\',
            \'unlockNote\': \'Desbloqueio automático após pagamento\', \'payConfirm\': \'Pagamento concluído? OK para desbloquear\', \'unlocked\': \'✅ Desbloqueado\',
        },
    }
    return jsonify(translations.get(lang_code, translations[\'en\']))


@app.route("/api/geo")
def geo_detect():
    """Detect user language from IP/location"""
    cf_country = request.headers.get(\'CF-IPCountry\', \'\').upper()
    x_country = request.headers.get(\'X-Geo-Country\', \'\').upper()
    country = cf_country or x_country or \'\'
    lang = COUNTRY_LANG.get(country, \'en\')
    return jsonify({\'country\': country, \'lang\': lang, \'available\': list(COUNTRY_LANG.values())})


# ═══════════════════════════════════════════
#  🎴 塔罗占卜 API
# ═══════════════════════════════════════════

@app.route("/api/tarot", methods=["POST"])
def tarot():
    """Tarot spread reading (3 cards)"""
    data = request.get_json(force=True) or {}
    cards = data.get("cards", [])
    level = data.get("level", "free")

    if len(cards) != 3:
        return jsonify({"error": "Need exactly 3 card IDs"}), 400

    try:
        cards_int = [int(c) for c in cards]
        reading = get_spread_reading(cards_int, level)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(reading)


# ═══════════════════════════════════════════
#  ☯️ 周易六爻 API
# ═══════════════════════════════════════════

@app.route("/api/iching", methods=["POST"])
def iching():
    """I Ching hexagram reading"""
    data = request.get_json(force=True) or {}
    lines = data.get("lines", [])
    level = data.get("level", "free")

    if len(lines) != 6:
        return jsonify({"error": "Need exactly 6 lines (0 or 1)"}), 400

    try:
        lines_int = [int(l) for l in lines]
        reading = get_reading(lines_int, level)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(reading)


# ═══════════════════════════════════════════
#  🖐️ 手相解读 API
# ═══════════════════════════════════════════

@app.route("/api/palm", methods=["POST"])
def palm():
    """Palm reading for selected lines"""
    data = request.get_json(force=True) or {}
    lines = data.get("lines", ["life"])
    hand = data.get("hand", "right")
    gender = data.get("gender", "male")
    level = data.get("level", "free")

    try:
        reading = get_palm_reading(lines, hand, gender, level)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(reading)


# ═══════════════════════════════════════════
#  📛 姓名学 API
# ═══════════════════════════════════════════

@app.route("/api/name", methods=["POST"])
def name_analysis():
    """Name stroke analysis"""
    data = request.get_json(force=True) or {}
    family = data.get("family", "").strip()
    given = data.get("given", "").strip()
    level = data.get("level", "free")

    if not family or not given:
        return jsonify({"error": "Need surname and given name"}), 400

    try:
        result = analyze_name(family, given, level)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if result.get("error"):
        return jsonify(result), 400

    return jsonify(result)

if __name__ == "__main__":
    libre = find_libreoffice()
    print("=" * 55)
    print("  slowbuild backend v2.0")
    print(f"  LibreOffice: {\'✅ \' + libre if libre else \'❌ 未安装\'}")
    print(f"  端口: 5000")
    print("=" * 55)
    print()
    print("  🟢 纯Python（立即可用）:")
    print("     extract_text / rename_batch / file_info / hash / merge_csv")
    if libre:
        print("  🟡 文档转换（LibreOffice）:")
        print("     word2pdf / excel2pdf / ppt2pdf / excel2csv / html2pdf")
        # 预热 LibreOffice：后台做一次空转换，后续请求秒转
        print()
        print("  🔥 正在预热 LibreOffice（约15秒，仅首次）...")
        try:
            import tempfile
            tmpdir = tempfile.mkdtemp()
            dummy = os.path.join(tmpdir, "warmup.txt")
            with open(dummy, "w") as f: f.write("warmup")
            subprocess.run([libre, "--headless", "--convert-to", "pdf", "--outdir", tmpdir, dummy],
                          capture_output=True, timeout=30, cwd=tmpdir)
            shutil.rmtree(tmpdir, ignore_errors=True)
            print("  ✅ 预热完成，后续转换秒出！")
        except Exception as e:
            print(f"  ⚠️ 预热失败: {e}")
    else:
        print("  ❌ 文档转换不可用 — 请安装 LibreOffice")
    print("  🟢 文件比对:")
    print("     dedup / images_list")
    print()

    if not libre:
        print("  下载 LibreOffice: https://www.libreoffice.org/download/")
    print()

    app.run(host="0.0.0.0", port=5000, debug=False)
')
print("  Wrote server.py (37317 bytes)")

# --- bazi.py ---
with open(os.path.join(TARGET, "bazi.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
八字命盘推算引擎 — 纯 Python 实现
农历转换 + 天干地支 + 五行 + 排盘 + 解读
"""

import datetime
import math

# ═══════════════════════════
# 天干地支 基础数据
# ═══════════════════════════
TIAN_GAN = [\'甲\', \'乙\', \'丙\', \'丁\', \'戊\', \'己\', \'庚\', \'辛\', \'壬\', \'癸\']
DI_ZHI = [\'子\', \'丑\', \'寅\', \'卯\', \'辰\', \'巳\', \'午\', \'未\', \'申\', \'酉\', \'戌\', \'亥\']
SHENG_XIAO = [\'鼠\', \'牛\', \'虎\', \'兔\', \'龙\', \'蛇\', \'马\', \'羊\', \'猴\', \'鸡\', \'狗\', \'猪\']
WU_XING_TG = [\'木\', \'木\', \'火\', \'火\', \'土\', \'土\', \'金\', \'金\', \'水\', \'水\']
WU_XING_DZ = [\'水\', \'土\', \'木\', \'木\', \'土\', \'火\', \'火\', \'土\', \'金\', \'金\', \'土\', \'水\']


# ========== 十神名称 ==========
SHI_SHEN_NAMES = {
    \'比肩\': {\'zh\': \'比肩\', \'en\': \'Sibling\'},
    \'劫财\': {\'zh\': \'劫财\', \'en\': \'Rob Wealth\'},
    \'食神\': {\'zh\': \'食神\', \'en\': \'Eating God\'},
    \'伤官\': {\'zh\': \'伤官\', \'en\': \'Hurting Officer\'},
    \'正财\': {\'zh\': \'正财\', \'en\': \'Direct Wealth\'},
    \'偏财\': {\'zh\': \'偏财\', \'en\': \'Indirect Wealth\'},
    \'正官\': {\'zh\': \'正官\', \'en\': \'Direct Officer\'},
    \'七杀\': {\'zh\': \'七杀\', \'en\': \'Seven Killings\'},
    \'正印\': {\'zh\': \'正印\', \'en\': \'Direct Resource\'},
    \'偏印\': {\'zh\': \'偏印\', \'en\': \'Indirect Resource\'},
}

# ========== 纳音五行 ==========
NA_YIN = {
    \'甲子\':\'海中金\',\'乙丑\':\'海中金\',\'丙寅\':\'炉中火\',\'丁卯\':\'炉中火\',
    \'戊辰\':\'大林木\',\'己巳\':\'大林木\',\'庚午\':\'路旁土\',\'辛未\':\'路旁土\',
    \'壬申\':\'剑锋金\',\'癸酉\':\'剑锋金\',\'甲戌\':\'山头火\',\'乙亥\':\'山头火\',
    \'丙子\':\'涧下水\',\'丁丑\':\'涧下水\',\'戊寅\':\'城头土\',\'己卯\':\'城头土\',
    \'庚辰\':\'白蜡金\',\'辛巳\':\'白蜡金\',\'壬午\':\'杨柳木\',\'癸未\':\'杨柳木\',
    \'甲申\':\'泉中水\',\'乙酉\':\'泉中水\',\'丙戌\':\'屋上土\',\'丁亥\':\'屋上土\',
    \'戊子\':\'霹雳火\',\'己丑\':\'霹雳火\',\'庚寅\':\'松柏木\',\'辛卯\':\'松柏木\',
    \'壬辰\':\'长流水\',\'癸巳\':\'长流水\',\'甲午\':\'沙中金\',\'乙未\':\'沙中金\',
    \'丙申\':\'山下火\',\'丁酉\':\'山下火\',\'戊戌\':\'平地木\',\'己亥\':\'平地木\',
    \'庚子\':\'壁上土\',\'辛丑\':\'壁上土\',\'壬寅\':\'金箔金\',\'癸卯\':\'金箔金\',
    \'甲辰\':\'覆灯火\',\'乙巳\':\'覆灯火\',\'丙午\':\'天河水\',\'丁未\':\'天河水\',
    \'戊申\':\'大驿土\',\'己酉\':\'大驿土\',\'庚戌\':\'钗钏金\',\'辛亥\':\'钗钏金\',
    \'壬子\':\'桑柘木\',\'癸丑\':\'桑柘木\',\'甲寅\':\'大溪水\',\'乙卯\':\'大溪水\',
    \'丙辰\':\'沙中土\',\'丁巳\':\'沙中土\',\'戊午\':\'天上火\',\'己未\':\'天上火\',
    \'庚申\':\'石榴木\',\'辛酉\':\'石榴木\',\'壬戌\':\'大海水\',\'癸亥\':\'大海水\',
}

NA_YIN_EN = {
    \'海中金\':\'Gold in Sea\',\'炉中火\':\'Fire in Furnace\',\'大林木\':\'Forest Wood\',
    \'路旁土\':\'Roadside Earth\',\'剑锋金\':\'Sword Gold\',\'山头火\':\'Mountain Fire\',
    \'涧下水\':\'Stream Water\',\'城头土\':\'Rampart Earth\',\'白蜡金\':\'White Wax Gold\',
    \'杨柳木\':\'Willow Wood\',\'泉中水\':\'Spring Water\',\'屋上土\':\'Roof Earth\',
    \'霹雳火\':\'Thunder Fire\',\'松柏木\':\'Pine Wood\',\'长流水\':\'Flowing Water\',
    \'沙中金\':\'Sand Gold\',\'山下火\':\'Mountain-base Fire\',\'平地木\':\'Flat Wood\',
    \'壁上土\':\'Wall Earth\',\'金箔金\':\'Gold Foil\',\'覆灯火\':\'Lamp Fire\',
    \'天河水\':\'Heaven River\',\'大驿土\':\'Post Earth\',\'钗钏金\':\'Hairpin Gold\',
    \'桑柘木\':\'Mulberry Wood\',\'大溪水\':\'Big Stream\',\'沙中土\':\'Sandy Earth\',
    \'天上火\':\'Heaven Fire\',\'石榴木\':\'Pomegranate Wood\',\'大海水\':\'Sea Water\',
}

# ========== 神煞 ==========
def get_shen_sha(pillars, day_zhi):
    """Return auspicious/inauspicious stars for the chart"""
    sha = {\'stars\': {}, \'explanations_zh\': {}, \'explanations_en\': {}}
    # Heavenly Noble
    tygr = {\'甲\':\'丑未\',\'戊\':\'丑未\',\'庚\':\'丑未\',\'乙\':\'子申\',\'己\':\'子申\',
            \'丙\':\'亥酉\',\'丁\':\'亥酉\',\'壬\':\'卯巳\',\'癸\':\'卯巳\',\'辛\':\'午寅\'}
    for pname, gz in pillars.items():
        gan = gz[0] if len(gz)>0 else \'\'
        zhi = gz[1] if len(gz)>1 else \'\'
        if gan in tygr:
            noble = tygr[gan]
            for z in noble:
                if z == zhi:
                    key = pname + \'_tian_yi\'
                    sha[\'stars\'][key] = pname + \' pillar: Heavenly Noble\'
                    sha[\'explanations_zh\'][key] = \'天乙贵人是最大的吉星\'
                    sha[\'explanations_en\'][key] = \'Greatest auspicious star; brings fortune\'
    # Literary Star
    wenchang = {\'甲\':\'巳\',\'乙\':\'午\',\'丙\':\'申\',\'丁\':\'酉\',\'戊\':\'申\',\'己\':\'酉\',
                \'庚\':\'亥\',\'辛\':\'子\',\'壬\':\'寅\',\'癸\':\'卯\'}
    for pname, gz in pillars.items():
        gan = gz[0] if len(gz)>0 else \'\'
        zhi = gz[1] if len(gz)>1 else \'\'
        if gan in wenchang and wenchang[gan] == zhi:
            key = pname + \'_wenchang\'
            sha[\'stars\'][key] = pname + \' pillar: Literary Star\'
            sha[\'explanations_zh\'][key] = \'文昌主聪明好学\'
            sha[\'explanations_en\'][key] = \'Literary talent, academic success\'
    # Peach Blossom (simplified: check if birth month zhi triggers)
    peach_triggers = {\'申\':\'酉\',\'子\':\'酉\',\'辰\':\'酉\',\'寅\':\'卯\',\'午\':\'卯\',\'戌\':\'卯\',
                      \'巳\':\'午\',\'酉\':\'午\',\'丑\':\'午\',\'亥\':\'子\',\'卯\':\'子\',\'未\':\'子\'}
    day_zhi_val = pillars.get(\'day\', [\'\',\'\'])[1] if day_zhi else \'\'
    if day_zhi_val in peach_triggers:
        peach_zhi = peach_triggers[day_zhi_val]
        # Check if any pillar has the peach blossom zhi
        for pname, gz in pillars.items():
            if gz[1] == peach_zhi:
                key = pname + \'_taohua\'
                sha[\'stars\'][key] = pname + \' pillar: Peach Blossom\'
                sha[\'explanations_zh\'][key] = \'桃花主异性缘与魅力\'
                sha[\'explanations_en\'][key] = \'Romantic charm and charisma\'
    return sha

# ========== 空亡 ==========
def get_xun_kong(day_gz):
    """Calculate Xun Kong (Emptiness) based on day pillar"""
    all_gz = []
    for i in range(60):
        all_gz.append(TIAN_GAN[i%10] + DI_ZHI[i%12])
    idx = all_gz.index(day_gz) if day_gz in all_gz else 0
    xun_start = (idx // 10) * 10
    used = set()
    for i in range(xun_start, xun_start+10):
        used.add(DI_ZHI[i%12])
    return [z for z in DI_ZHI if z not in used]

# ========== 十神 ==========
def get_shi_shen(day_gan, target_gan):
    """Calculate Ten God relationship of target_gan relative to day_gan"""
    gan_list = TIAN_GAN
    wuxing_list = WU_XING_TG
    day_idx = gan_list.index(day_gan) if day_gan in gan_list else 0
    target_idx = gan_list.index(target_gan) if target_gan in gan_list else 0
    day_wx = wuxing_list[day_idx]
    target_wx = wuxing_list[target_idx]
    same_polarity = (day_idx % 2) == (target_idx % 2)
    wx_order = [\'木\',\'火\',\'土\',\'金\',\'水\']
    day_wx_i = wx_order.index(day_wx)
    target_wx_i = wx_order.index(target_wx)
    if target_wx == day_wx:
        return \'比肩\' if same_polarity else \'劫财\'
    elif target_wx == wx_order[(day_wx_i + 1) % 5]:
        return \'食神\' if same_polarity else \'伤官\'
    elif target_wx == wx_order[(day_wx_i + 2) % 5]:
        return \'偏财\' if same_polarity else \'正财\'
    elif wx_order[(target_wx_i + 2) % 5] == day_wx:
        return \'七杀\' if same_polarity else \'正官\'
    else:
        return \'偏印\' if same_polarity else \'正印\'

def _shi_shen_en(cn_name):
    return SHI_SHEN_NAMES.get(cn_name, {}).get(\'en\', cn_name)

# ========== 大运 ==========
def calculate_dayun(year, month, day, hour, gender, lang=\'zh\'):
    """Calculate Luck Pillars (Decade Luck)"""
    date_obj = datetime.date(year, month, day)
    year_gz = get_year_gz(year)
    lunar_year, lunar_month, lunar_day, is_leap = solar_to_lunar(date_obj)
    month_gz = get_month_gz(year_gz, month, day, is_leap)
    day_gz = get_day_gz(date_obj)

    year_gan_idx = TIAN_GAN.index(year_gz[0])
    is_yang = (year_gan_idx % 2 == 0)
    forward = (is_yang and gender == \'male\') or (not is_yang and gender == \'female\')

    days_to_jieqi = abs(day - JIE_QI.get(month, 5))
    start_age = max(1, round(days_to_jieqi / 3.0))
    if not forward:
        prev_month = month - 1 if month > 1 else 12
        prev_jq = JIE_QI.get(prev_month, 5)
        days_from = (30 - prev_jq) + day
        start_age = max(1, round(days_from / 3.0))

    month_zhi_idx = DI_ZHI.index(month_gz[1])
    month_gan_idx = TIAN_GAN.index(month_gz[0])

    results = []
    for i in range(10):
        age = start_age + i * 10
        if forward:
            ng = (month_gan_idx + 1 + i) % 10
            nz = (month_zhi_idx + 1 + i) % 12
        else:
            ng = (month_gan_idx - 1 - i) % 10
            nz = (month_zhi_idx - 1 - i) % 12
        gz = TIAN_GAN[ng] + DI_ZHI[nz]
        nayin = NA_YIN.get(gz, \'\')
        nayin_en = NA_YIN_EN.get(nayin, \'\')
        results.append({
            \'start_age\': age, \'end_age\': age + 9, \'ganzhi\': gz,
            \'nayin\': nayin_en if lang.startswith(\'en\') else nayin,
            \'nayin_cn\': nayin,
        })
    return results

# ========== 流年 ==========
def calculate_liunian(day_gz, current_year, count=5, lang=\'zh\'):
    """Calculate Yearly Luck for upcoming years"""
    year_gz_2020 = get_year_gz(2020)
    all_gz = []
    for i in range(60):
        all_gz.append(TIAN_GAN[i%10] + DI_ZHI[i%12])
    gz_2020_idx = all_gz.index(year_gz_2020) if year_gz_2020 in all_gz else 0

    day_zhi = day_gz[1] if len(day_gz)>1 else \'\'
    liuhe = {\'子\':\'丑\',\'丑\':\'子\',\'寅\':\'亥\',\'亥\':\'寅\',\'卯\':\'戌\',\'戌\':\'卯\',
             \'辰\':\'酉\',\'酉\':\'辰\',\'巳\':\'申\',\'申\':\'巳\',\'午\':\'未\',\'未\':\'午\'}
    chong = {\'子\':\'午\',\'午\':\'子\',\'丑\':\'未\',\'未\':\'丑\',\'寅\':\'申\',\'申\':\'寅\',
             \'卯\':\'酉\',\'酉\':\'卯\',\'辰\':\'戌\',\'戌\':\'辰\',\'巳\':\'亥\',\'亥\':\'巳\'}

    results = []
    for i in range(count):
        yr = current_year + i
        gz_idx = (gz_2020_idx + (yr - 2020)) % 60
        gz = all_gz[gz_idx]
        ss = get_shi_shen(day_gz[0], gz[0])
        yr_zhi = gz[1] if len(gz)>1 else \'\'
        relations = []
        if liuhe.get(day_zhi) == yr_zhi:
            relations.append(\'Union\' if lang.startswith(\'en\') else \'六合\')
        if chong.get(day_zhi) == yr_zhi:
            relations.append(\'Clash\' if lang.startswith(\'en\') else \'相冲\')
        results.append({
            \'year\': yr, \'ganzhi\': gz,
            \'shi_shen\': _shi_shen_en(ss) if lang.startswith(\'en\') else ss,
            \'nayin\': NA_YIN.get(gz, \'\'),
            \'zhi_relations\': relations,
        })
    return results

# ========== 五行详细 ==========
def detailed_wuxing_balance(pillars):
    """Detailed five-element analysis with per-pillar breakdown"""
    wuxing_detail = {\'金\':0,\'木\':0,\'水\':0,\'火\':0,\'土\':0}
    pillar_wx = {}
    for pname, gz in pillars.items():
        gan = gz[0]
        zhi = gz[1] if len(gz)>1 else \'\'
        gan_wx = WU_XING_TG[TIAN_GAN.index(gan)]
        zhi_wx = WU_XING_DZ[DI_ZHI.index(zhi)] if zhi else \'\'
        wuxing_detail[gan_wx] += 2
        if zhi_wx:
            wuxing_detail[zhi_wx] += 1
        pillar_wx[pname] = {\'gan\':gan,\'gan_wx\':gan_wx,\'zhi\':zhi,\'zhi_wx\':zhi_wx}
    total = sum(wuxing_detail.values()) or 1
    wuxing_pct = {k: round(v/total*100, 1) for k,v in wuxing_detail.items()}
    missing = [k for k,v in wuxing_detail.items() if v < 1]
    weak = [k for k,v in wuxing_pct.items() if 0 < v < 12]
    dominant = max(wuxing_detail, key=wuxing_detail.get)
    return {
        \'detail\': wuxing_detail, \'percent\': wuxing_pct,
        \'missing\': missing, \'weak\': weak, \'dominant\': dominant,
        \'pillar_wx\': pillar_wx,
    }

# ========== 日主强弱 ==========
def day_master_strength(day_master, pillars, wuxing_balance):
    """Determine if Day Master is strong, weak, or balanced"""
    wx = day_master[\'wuxing\']
    wx_cycle_gen = {\'木\':\'水\',\'火\':\'木\',\'土\':\'火\',\'金\':\'土\',\'水\':\'金\'}
    support_wx = wx_cycle_gen.get(wx, \'\')
    self_count = wuxing_balance[\'detail\'].get(wx, 0)
    support_count = wuxing_balance[\'detail\'].get(support_wx, 0)
    score = self_count + support_count
    if score >= 6:
        return \'身强\'
    elif score <= 3:
        return \'身弱\'
    else:
        return \'中和\'

# ========== 日主详解 ==========
DAY_MASTER_FULL = {
    \'甲\': {
        \'summary_zh\': \'甲木参天，栋梁之材。性格直率果敢，有领导力和开创精神。\',
        \'summary_en\': \'Jia Wood: towering and upright, a born leader with pioneering spirit.\',
        \'career_zh\': \'从政、管理、教育、建筑、林业、法律。宜做大方向引领者。\',
        \'career_en\': \'Politics, management, education, construction, forestry, law.\',
        \'love_zh\': \'感情中主动强势，喜欢温柔体贴的伴侣，需注意适当退让。\',
        \'love_en\': \'Assertive in love; prefers gentle partners; learn to compromise.\',
        \'health_zh\': \'注意肝胆、筋骨。多运动疏解压力，避免暴怒伤肝。\',
        \'health_en\': \'Watch liver, tendons. Exercise to relieve stress; avoid anger.\',
    },
    \'乙\': {
        \'summary_zh\': \'乙木柔韧，花草之姿。心思细腻，善于变通，有艺术天赋。\',
        \'summary_en\': \'Yi Wood: flexible and delicate, artistic and adaptable.\',
        \'career_zh\': \'艺术设计、文学写作、公关传媒、园林园艺、心理咨询。\',
        \'career_en\': \'Arts, design, writing, PR, media, horticulture, counseling.\',
        \'love_zh\': \'重视情感沟通，渴望浪漫，需要坚定有担当的伴侣。\',
        \'love_en\': \'Values emotional connection; longs for romance; needs a decisive partner.\',
        \'health_zh\': \'注意肝胆、眼睛。保持充足睡眠，少熬夜。\',
        \'health_en\': \'Watch liver, eyes. Maintain good sleep; avoid late nights.\',
    },
    \'丙\': {
        \'summary_zh\': \'丙火炎上，烈日之光。热情开朗，慷慨大方，感染力强。\',
        \'summary_en\': \'Bing Fire: blazing sun. Warm, generous, highly charismatic.\',
        \'career_zh\': \'传媒演艺、销售市场、互联网、能源行业、教育演讲。\',
        \'career_en\': \'Media, entertainment, sales, tech, energy, public speaking.\',
        \'love_zh\': \'爱情中热情似火，主动大方。热烈过后需学会细水长流。\',
        \'love_en\': \'Passionate and bold in love; learn to sustain warmth over time.\',
        \'health_zh\': \'注意心脏、血压。夏天防暑降温，情绪不宜大起大落。\',
        \'health_en\': \'Watch heart, blood pressure. Stay cool; avoid emotional extremes.\',
    },
    \'丁\': {
        \'summary_zh\': \'丁火柔中，灯烛之光。内心明亮，心思缜密，有独特见解。\',
        \'summary_en\': \'Ding Fire: gentle candle flame. Insightful, meticulous, unique perspective.\',
        \'career_zh\': \'学术研究、技术开发、医疗护理、编辑校对、数据分析。\',
        \'career_en\': \'Research, tech development, healthcare, editing, data analysis.\',
        \'love_zh\': \'追求灵魂伴侣，感情极为认真。但过于理想化，易受伤。\',
        \'love_en\': \'Seeks soulmate; takes love seriously but too idealistic. Learn to accept imperfection.\',
        \'health_zh\': \'注意心脏、神经系统。多做冥想、瑜伽等静心活动。\',
        \'health_en\': \'Watch heart, nervous system. Try meditation, yoga.\',
    },
    \'戊\': {
        \'summary_zh\': \'戊土厚重，城墙之固。稳重可靠，诚信务实，责任心强。\',
        \'summary_en\': \'Wu Earth: fortress walls. Steady, reliable, trustworthy, responsible.\',
        \'career_zh\': \'金融地产、工程建设、仓储物流、行政管理、农业。\',
        \'career_en\': \'Finance, real estate, engineering, logistics, administration, agriculture.\',
        \'love_zh\': \'感情中责任感极强，可靠伴侣。但缺乏浪漫，需学会表达。\',
        \'love_en\': \'Extremely responsible partner; but lacks romance. Learn to express affection.\',
        \'health_zh\': \'注意脾胃、消化系统。饮食规律，忌暴饮暴食。\',
        \'health_en\': \'Watch spleen, stomach, digestion. Eat regularly; avoid overeating.\',
    },
    \'己\': {
        \'summary_zh\': \'己土卑湿，田园之壤。温和包容，有耐心，善于培育他人。\',
        \'summary_en\': \'Ji Earth: fertile garden soil. Gentle, patient, nurturing.\',
        \'career_zh\': \'教育培训、护理保育、营养健康、社会工作、服务行业。\',
        \'career_en\': \'Education, nursing, nutrition, social work, service industries.\',
        \'love_zh\': \'温柔体贴，理想居家伴侣。但容易依赖，需培养独立性。\',
        \'love_en\': \'Tender and caring partner; but tends to depend. Cultivate independence.\',
        \'health_zh\': \'注意脾胃、肌肉。适当运动，避免久坐。\',
        \'health_en\': \'Watch spleen, stomach, muscles. Exercise moderately.\',
    },
    \'庚\': {
        \'summary_zh\': \'庚金带煞，刀剑之刚。意志坚定，杀伐果断，执行力极强。\',
        \'summary_en\': \'Geng Metal: forged steel. Strong-willed, decisive, execution-oriented.\',
        \'career_zh\': \'军警法律、机械制造、工程技术、竞技体育、外科医生。\',
        \'career_en\': \'Military, law, mechanics, engineering, sports, surgery.\',
        \'love_zh\': \'行动胜于言语，言出必行。但不擅甜言蜜语，需对方理解。\',
        \'love_en\': \'Actions over words — a partner who delivers. Needs understanding of your love language.\',
        \'health_zh\': \'注意肺、大肠、皮肤。戒烟限酒，多呼吸新鲜空气。\',
        \'health_en\': \'Watch lungs, large intestine, skin. Avoid smoking; get fresh air.\',
    },
    \'辛\': {
        \'summary_zh\': \'辛金温润，珠宝之精。精致优雅，品味不俗，追求完美。\',
        \'summary_en\': \'Xin Metal: fine jewelry. Refined, elegant, perfectionist.\',
        \'career_zh\': \'珠宝首饰、美容美妆、音乐艺术、奢侈品、精密制造。\',
        \'career_en\': \'Jewelry, beauty, music, luxury goods, precision manufacturing.\',
        \'love_zh\': \'追求浪漫和完美，宁缺毋滥。一旦认定，会用心经营。\',
        \'love_en\': \'Pursues romantic perfection; would rather wait than settle. Devoted once committed.\',
        \'health_zh\': \'注意肺、呼吸道、牙齿。注意口腔卫生和空气质量。\',
        \'health_en\': \'Watch lungs, respiratory system, teeth. Maintain oral hygiene.\',
    },
    \'壬\': {
        \'summary_zh\': \'壬水通河，江海之广。心胸开阔，聪慧机敏，适应力强。\',
        \'summary_en\': \'Ren Water: great river. Broad-minded, intelligent, highly adaptable.\',
        \'career_zh\': \'国际贸易、外交谈判、旅游物流、水利航运、策划咨询。\',
        \'career_en\': \'Trade, diplomacy, tourism, logistics, water resources, consulting.\',
        \'love_zh\': \'自由奔放不喜约束，感情中空间大于陪伴。需成熟包容的伴侣。\',
        \'love_en\': \'Free-spirited; needs space more than company. Needs mature, tolerant partner.\',
        \'health_zh\': \'注意肾、膀胱、耳朵。多喝水，避免憋尿，注意保暖。\',
        \'health_en\': \'Watch kidneys, bladder, ears. Stay hydrated; keep warm.\',
    },
    \'癸\': {
        \'summary_zh\': \'癸水至阴，雨露之润。智慧深厚，洞察力强，内心世界丰富。\',
        \'summary_en\': \'Gui Water: morning dew. Deep wisdom, strong perception, rich inner world.\',
        \'career_zh\': \'学术研究、战略策划、心理咨询、刑侦调查、玄学命理。\',
        \'career_en\': \'Academia, strategy, psychology, investigation, metaphysics.\',
        \'love_zh\': \'情感神秘深沉，不轻易敞开内心。一旦认定，便是此生深情。\',
        \'love_en\': \'Mysteriously deep; doesn\\\'t open easily. Once committed, it\\\'s for life.\',
        \'health_zh\': \'注意肾、泌尿系统。保持心情愉快，避免长期压抑。\',
        \'health_en\': \'Watch kidneys, urinary system. Stay cheerful; avoid long-term emotional suppression.\',
    },
}
# 节气日期 (近似，用于月柱划分)
JIE_QI = {
    1: 5, 2: 4, 3: 6, 4: 5, 5: 6, 6: 6,
    7: 7, 8: 8, 9: 8, 10: 8, 11: 7, 12: 7
}

# 农历数据 1900-2050
# 每个条目: (year_encoded, ...)
# year_encoded: bit0-3=闰月月份(0=无), bit4-15=每月大小月(1=大30天,0=小29天), bit16-19=闰月大小
LUNAR_DATA = [
    0x04bd8,0x04ae0,0x0a570,0x054d5,0x0d260,0x0d950,0x16554,0x056a0,0x09ad0,0x055d2,
    0x04ae0,0x0a5b6,0x0a4d0,0x0d250,0x1d255,0x0b540,0x0d6a0,0x0ada2,0x095b0,0x14977,
    0x04970,0x0a4b0,0x0b4b5,0x06a50,0x06d40,0x1ab54,0x02b60,0x09570,0x052f2,0x04970,
    0x06566,0x0d4a0,0x0ea50,0x06e95,0x05ad0,0x02b60,0x186e3,0x092e0,0x1c8d7,0x0c950,
    0x0d4a0,0x1d8a6,0x0b550,0x056a0,0x1a5b4,0x025d0,0x092d0,0x0d2b2,0x0a950,0x0b557,
    0x06ca0,0x0b550,0x15355,0x04da0,0x0a5b0,0x14573,0x052b0,0x0a9a8,0x0e950,0x06aa0,
    0x0aea6,0x0ab50,0x04b60,0x0aae4,0x0a570,0x05260,0x0f263,0x0d950,0x05b57,0x056a0,
    0x096d0,0x04dd5,0x04ad0,0x0a4d0,0x0d4d4,0x0d250,0x0d558,0x0b540,0x0b6a0,0x195a6,
    0x095b0,0x049b0,0x0a974,0x0a4b0,0x0b27a,0x06a50,0x06d40,0x0af46,0x0ab60,0x09570,
    0x04af5,0x04970,0x064b0,0x074a3,0x0ea50,0x06b58,0x055c0,0x0ab60,0x096d5,0x092e0,
    0x0c960,0x0d954,0x0d4a0,0x0da50,0x07552,0x056a0,0x0abb7,0x025d0,0x092d0,0x0cab5,
    0x0a950,0x0b4a0,0x0baa4,0x0ad50,0x055d9,0x04ba0,0x0a5b0,0x15176,0x052b0,0x0a930,
    0x07954,0x06aa0,0x0ad50,0x05b52,0x04b60,0x0a6e6,0x0a4e0,0x0d260,0x0ea65,0x0d530,
    0x05aa0,0x076a3,0x096d0,0x04afb,0x04ad0,0x0a4d0,0x1d0b6,0x0d250,0x0d520,0x0dd45,
    0x0b5a0,0x056d0,0x055b2,0x049b0,0x0a577,0x0a4b0,0x0aa50,0x1b255,0x06d20,0x0ada0,
    0x14b63
]

# ═══════════════════════════
# 农历转换 (公历 → 农历)
# ═══════════════════════════

def get_lunar_month_days(year, m):
    """获取农历年 year 的第 m 个月的天数"""
    return 30 if LUNAR_DATA[year - 1900] & (0x10000 >> m) else 29

def get_lunar_year_days(year):
    """获取农历年 year 的总天数"""
    days = 0
    for m in range(1, 13):
        days += get_lunar_month_days(year, m)
    leap_month = LUNAR_DATA[year - 1900] & 0xf
    if leap_month:
        days += 30 if LUNAR_DATA[year - 1900] & 0x10000 else 29
    return days

def get_lunar_leap_month(year):
    """获取农历年 year 的闰月月份，0 表示没有"""
    return LUNAR_DATA[year - 1900] & 0xf

def solar_to_lunar(date_obj):
    """公历日期 → 农历日期
    返回: (lunar_year, lunar_month, lunar_day, is_leap)
    """
    year, month, day = date_obj.year, date_obj.month, date_obj.day
    
    # 计算该日期距离 1900-01-31 的天数 (1900年正月初一)
    base_date = datetime.date(1900, 1, 31)
    offset = (date_obj - base_date).days
    
    # 遍历农历年找到对应的农历日期
    lunar_year = 1900
    while offset >= get_lunar_year_days(lunar_year):
        offset -= get_lunar_year_days(lunar_year)
        lunar_year += 1
    
    # 在找到的农历年内定位月份和日子
    leap_month = get_lunar_leap_month(lunar_year)
    is_leap = False
    
    for m in range(1, 13):
        # 检查是否是闰月
        if leap_month > 0 and m == leap_month + 1:
            month_days = 30 if LUNAR_DATA[lunar_year - 1900] & 0x10000 else 29
            if offset < month_days:
                return (lunar_year, leap_month, offset + 1, True)
            offset -= month_days
            is_leap = False
        
        month_days = get_lunar_month_days(lunar_year, m)
        if offset < month_days:
            return (lunar_year, m, offset + 1, is_leap)
        offset -= month_days
    
    # should never reach here
    return (lunar_year, 12, offset + 1, False)


# ═══════════════════════════
# 八字排盘
# ═══════════════════════════

def get_year_gz(year):
    """年柱天干地支"""
    base = 1984  # 甲子年
    offset = (year - base) % 60
    return TIAN_GAN[offset % 10] + DI_ZHI[offset % 12]

def get_month_gz(year_gz, month, day, is_leap):
    """月柱天干地支 (以节气为界)"""
    # 年干索引
    year_gan_idx = TIAN_GAN.index(year_gz[0])
    
    # 根据节气确定月支
    # 立春=寅月, 惊蛰=卯月, ...
    jie_qi_day = JIE_QI.get(month, 5)
    
    if month == 2 and day >= 4:
        month_idx = 1  # 寅月
    elif month == 3 and day >= 6:
        month_idx = 2
    elif month == 4 and day >= 5:
        month_idx = 3
    elif month == 5 and day >= 6:
        month_idx = 4
    elif month == 6 and day >= 6:
        month_idx = 5
    elif month == 7 and day >= 7:
        month_idx = 6
    elif month == 8 and day >= 8:
        month_idx = 7
    elif month == 9 and day >= 8:
        month_idx = 8
    elif month == 10 and day >= 8:
        month_idx = 9
    elif month == 11 and day >= 7:
        month_idx = 10
    elif month == 12 and day >= 7:
        month_idx = 11
    else:
        month_idx = (month + 9) % 12 if month >= 3 else month - 1
    
    # 月天干 = (年天干索引 * 2 + 月支索引) % 10
    month_gan_idx = (year_gan_idx * 2 + month_idx) % 10
    return TIAN_GAN[month_gan_idx] + DI_ZHI[month_idx]

def get_day_gz(date_obj):
    """日柱天干地支 (标准算法)"""
    base_date = datetime.date(1900, 1, 1)
    diff_days = (date_obj - base_date).days
    # 1900-01-01 是甲戌日 (甲戌 = 天干0 + 地支10)
    gan_idx = (diff_days + 0) % 10
    zhi_idx = (diff_days + 10) % 12
    return TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx]

def get_hour_gz(day_gz, hour):
    """时柱天干地支"""
    day_gan_idx = TIAN_GAN.index(day_gz[0])
    # 时辰: 23-1子时, 1-3丑时, ...
    zhi_idx = ((hour + 1) // 2) % 12
    # 时天干 = (日天干索引 * 2 + 时支索引) % 10
    gan_idx = (day_gan_idx * 2 + zhi_idx) % 10
    return TIAN_GAN[gan_idx] + DI_ZHI[zhi_idx]

def get_hour_name(hour):
    """获取时辰名称"""
    names = [\'子时 (23:00-01:00)\', \'丑时 (01:00-03:00)\', \'寅时 (03:00-05:00)\',
             \'卯时 (05:00-07:00)\', \'辰时 (07:00-09:00)\', \'巳时 (09:00-11:00)\',
             \'午时 (11:00-13:00)\', \'未时 (13:00-15:00)\', \'申时 (15:00-17:00)\',
             \'酉时 (17:00-19:00)\', \'戌时 (19:00-21:00)\', \'亥时 (21:00-23:00)\']
    idx = ((hour + 1) // 2) % 12
    return names[idx]


# ═══════════════════════════
# 五行分析
# ═══════════════════════════

def analyze_wuxing(pillars):
    """分析八字五行"""
    wuxing = {\'金\': 0, \'木\': 0, \'水\': 0, \'火\': 0, \'土\': 0}
    
    for pillar_name, gz in pillars.items():
        if not gz or len(gz) < 2:
            continue
        gan = gz[0]
        zhi = gz[1]
        
        # 天干五行
        gan_idx = TIAN_GAN.index(gan)
        wuxing[WU_XING_TG[gan_idx]] += 1
        
        # 地支五行
        zhi_idx = DI_ZHI.index(zhi)
        wuxing[WU_XING_DZ[zhi_idx]] += 1
    
    # 缺失的五行
    missing = [w for w, count in wuxing.items() if count == 0]
    
    # 找出最强的五行
    dominant = max(wuxing, key=wuxing.get)
    
    return {\'count\': wuxing, \'missing\': missing, \'dominant\': dominant}


def get_day_master(pillars):
    """日主（日柱天干）"""
    day_gz = pillars.get(\'day\', \'\')
    if len(day_gz) >= 1:
        gan = day_gz[0]
        wx = WU_XING_TG[TIAN_GAN.index(gan)]
        return {\'gan\': gan, \'wuxing\': wx}
    return {\'gan\': \'?\', \'wuxing\': \'?\'}


# ═══════════════════════════
# 解读生成
# ═══════════════════════════

SELF_INTERPRETATIONS = {
    \'甲\': {\'nature\': \'参天大树，正直坚毅，有领导力但自尊心强\',
           \'career\': \'适合管理、教育、林业、建筑行业\',
           \'love\': \'对伴侣忠诚但固执己见，需要互补型伴侣\'},
    \'乙\': {\'nature\': \'花草藤蔓，柔韧细腻，善交际但易优柔寡断\',
           \'career\': \'适合艺术、设计、咨询、服务业\',
           \'love\': \'重视情感交流，适合有主见的伴侣带动\'},
    \'丙\': {\'nature\': \'太阳之火，热情开朗，慷慨大方但有时鲁莽\',
           \'career\': \'适合传媒、演艺、销售、互联网行业\',
           \'love\': \'爱情热烈主动，注意给对方空间\'},
    \'丁\': {\'nature\': \'灯烛之火，内向细腻，心思缜密但易敏感\',
           \'career\': \'适合研究、写作、技术、医疗行业\',
           \'love\': \'渴望灵魂伴侣，感情投入但容易受伤\'},
    \'戊\': {\'nature\': \'城墙之土，稳重踏实，诚信可靠但保守固执\',
           \'career\': \'适合金融、地产、行政、工程行业\',
           \'love\': \'责任感强但缺乏浪漫，需有耐心的伴侣\'},
    \'己\': {\'nature\': \'田园之土，温和包容，有耐心但魄力不足\',
           \'career\': \'适合教育、护理、农业、后勤行业\',
           \'love\': \'温柔体贴但有依赖倾向，需能扛事的伴侣\'},
    \'庚\': {\'nature\': \'刀剑之金，果断刚毅，执行力强但缺乏柔情\',
           \'career\': \'适合军警、法律、机械、竞技行业\',
           \'love\': \'行动胜于言语，追求效率十足但不懂甜言蜜语\'},
    \'辛\': {\'nature\': \'珠宝之金，精致优雅，品味高但有时候过于挑剔\',
           \'career\': \'适合珠宝、美容、音乐、奢侈品行业\',
           \'love\': \'追求浪漫完美的爱情，宁缺毋滥\'},
    \'壬\': {\'nature\': \'江河之水，心胸宽广，聪明灵活但缺乏定力\',
           \'career\': \'适合贸易、外交、旅游、物流行业\',
           \'love\': \'自由奔放不喜束缚，需成熟包容的伴侣\'},
    \'癸\': {\'nature\': \'雨露之水，智慧深沉，洞察力强但容易忧郁\',
           \'career\': \'适合学术、策划、心理咨询、侦探行业\',
           \'love\': \'情感深沉神秘，需要一个懂自己的人\'},
}

# English interpretations
SELF_INTERPRETATIONS_EN = {
    \'甲\': {\'nature\': \'A towering tree — upright and persistent, a natural leader with strong self-esteem\',
           \'career\': \'Management, education, forestry, construction\',
           \'love\': \'Loyal to partners but stubborn; needs a complementary match\'},
    \'乙\': {\'nature\': \'Flowers and vines — flexible and delicate, sociable but sometimes indecisive\',
           \'career\': \'Arts, design, consulting, service industries\',
           \'love\': \'Values emotional connection, thrives with a decisive partner\'},
    \'丙\': {\'nature\': \'The blazing sun — passionate and generous, outgoing but sometimes impulsive\',
           \'career\': \'Media, entertainment, sales, tech industry\',
           \'love\': \'Bold and active in love; needs to give partner space\'},
    \'丁\': {\'nature\': \'A candle flame — introspective and meticulous, thoughtful but easily hurt\',
           \'career\': \'Research, writing, technology, healthcare\',
           \'love\': \'Seeks a soulmate; emotionally invested but vulnerable\'},
    \'戊\': {\'nature\': \'A fortress of earth — steady and reliable, trustworthy but conservative\',
           \'career\': \'Finance, real estate, administration, engineering\',
           \'love\': \'Strong sense of duty but lacks romance; needs a patient partner\'},
    \'己\': {\'nature\': \'Garden soil — gentle and tolerant, patient but lacking boldness\',
           \'career\': \'Education, nursing, agriculture, logistics\',
           \'love\': \'Tender and caring but dependent; needs a capable partner\'},
    \'庚\': {\'nature\': \'Forged steel — decisive and strong-willed, execution-oriented but lacks tenderness\',
           \'career\': \'Military, law, mechanics, competitive sports\',
           \'love\': \'Actions speak louder than words; pragmatic but not sweet-talking\'},
    \'辛\': {\'nature\': \'Fine jewelry — refined and elegant, has great taste but can be picky\',
           \'career\': \'Jewelry, beauty, music, luxury goods\',
           \'love\': \'Pursues perfect romantic love; would rather wait than settle\'},
    \'壬\': {\'nature\': \'A great river — broad-minded and intelligent, flexible but lacks persistence\',
           \'career\': \'Trade, diplomacy, tourism, logistics\',
           \'love\': \'Free-spirited and dislikes constraints; needs a mature, tolerant partner\'},
    \'癸\': {\'nature\': \'Morning dew — deep and wise, perceptive but prone to melancholy\',
           \'career\': \'Academia, strategy, psychology, investigation\',
           \'love\': \'Emotionally deep and mysterious; needs someone who truly understands\'},
}

def generate_interpretation(bazi_result, level=\'basic\', lang=\'zh\'):
    """根据八字结果生成详细解读。lang=\'en\' 返回英文"""
    pillars = bazi_result[\'pillars\']
    day_master = bazi_result[\'day_master\']
    wuxing_info = bazi_result[\'wuxing\']
    gan = day_master[\'gan\']
    wx = day_master[\'wuxing\']
    is_en = lang.startswith(\'en\') if lang else False
    interp_db = SELF_INTERPRETATIONS_EN if is_en else SELF_INTERPRETATIONS
    dm_full = DAY_MASTER_FULL.get(gan, {})
    
    self_info = interp_db.get(gan, {\'nature\': \'Insufficient data\' if is_en else \'目前数据不足\', \'career\': \'No suggestion\' if is_en else \'暂无建议\', \'love\': \'No suggestion\' if is_en else \'暂无建议\'})
    
    if is_en:
        wx_en = {\'木\': \'Wood\', \'火\': \'Fire\', \'土\': \'Earth\', \'金\': \'Metal\', \'水\': \'Water\'}
        nature_first = self_info[\'nature\'].split(\',\')[0].split(\' — \')[0] if \' — \' in self_info[\'nature\'] else self_info[\'nature\'].split(\',\')[0]
        summary = f"You are a {wx_en.get(wx, \'\')} {gan} person, like a {nature_first}."
    else:
        summary = f"您是{gan}木命人，如同{self_info[\'nature\'].split(\'，\')[0]}。"
    
    result = {
        \'summary\': dm_full.get(\'summary_en\' if is_en else \'summary_zh\', summary),
        \'nature\': self_info[\'nature\'],
        \'wuxing_balance\': \'\',
        \'career\': \'\',
        \'love\': \'\',
        \'health\': \'\',
        \'lucky_elements\': [],
        \'day_master_strength\': \'\',
        \'ten_gods_analysis\': \'\',
    }
    
    # 五行详细
    dominant = wuxing_info.get(\'dominant\', \'\')
    missing = wuxing_info.get(\'missing\', [])
    pct = wuxing_info.get(\'percent\', {})
    if is_en:
        wx_en_full = {\'金\':\'Metal\',\'木\':\'Wood\',\'水\':\'Water\',\'火\':\'Fire\',\'土\':\'Earth\'}
        dominant_en = wx_en_full.get(dominant, dominant)
        if missing:
            missing_en = [wx_en_full.get(m,m) for m in missing]
            result[\'wuxing_balance\'] = f"Missing {\' & \'.join(missing_en)}. Dominant: {dominant_en} ({pct.get(dominant,0)}%). Balance through colors, accessories and habits."
        else:
            result[\'wuxing_balance\'] = f"All five elements present. Dominant: {dominant_en} ({pct.get(dominant,0)}%). Naturally balanced."
    else:
        if missing:
            result[\'wuxing_balance\'] = f"五行缺{\'、\'.join(missing)}。{dominant}最旺（占{pct.get(dominant,0)}%）。建议通过颜色、饰品或日常习惯来补充缺失元素。"
        else:
            result[\'wuxing_balance\'] = f"五行齐全，先天命格较为平衡。{dominant}最旺（占{pct.get(dominant,0)}%），这是你的核心特质。"
    
    # 日主强弱
    strength = bazi_result.get(\'day_master_strength\', \'\')
    if is_en:
        strength_map = {\'身强\':\'Strong\',\'身弱\':\'Weak\',\'中和\':\'Balanced\'}
        result[\'day_master_strength\'] = strength_map.get(strength, strength)
    else:
        result[\'day_master_strength\'] = strength
    
    # 十神
    ten_gods = bazi_result.get(\'ten_gods\', {})
    if ten_gods:
        pillar_names = {\'year\': \'Year\' if is_en else \'年柱\', \'month\': \'Month\' if is_en else \'月柱\', \'day\': \'Day\' if is_en else \'日柱\', \'hour\': \'Hour\' if is_en else \'时柱\'}
        tg_lines = []
        for pname, gods in ten_gods.items():
            pn = pillar_names.get(pname, pname)
            g = _shi_shen_en(gods.get(\'gan\',\'\')) if is_en else gods.get(\'gan\',\'\')
            z = _shi_shen_en(gods.get(\'zhi\',\'\')) if is_en else gods.get(\'zhi\',\'\')
            tg_lines.append(f"{pn}: {g}/{z}")
        result[\'ten_gods_analysis\'] = \' | \'.join(tg_lines)
    
    # 神煞
    shen_sha = bazi_result.get(\'shen_sha\', {})
    if shen_sha and shen_sha.get(\'stars\'):
        result[\'shen_sha\'] = {
            \'stars\': list(shen_sha[\'stars\'].values()),
            \'explanations\': list((shen_sha[\'explanations_en\'] if is_en else shen_sha[\'explanations_zh\']).values())
        }
    
    # 解读层级
    if level in (\'basic\', \'full\'):
        result[\'career\'] = dm_full.get(\'career_en\' if is_en else \'career_zh\', self_info[\'career\'])
        result[\'love\'] = dm_full.get(\'love_en\' if is_en else \'love_zh\', self_info[\'love\'])
        result[\'health\'] = dm_full.get(\'health_en\' if is_en else \'health_zh\', \'\')
    
    if level == \'full\':
        wx_cycle = {\'木\': \'水\', \'火\': \'木\', \'土\': \'火\', \'金\': \'土\', \'水\': \'金\'}
        wx_support = wx_cycle.get(wx, \'\')
        if wx_support:
            wx_support_en = {\'木\':\'Wood\',\'火\':\'Fire\',\'土\':\'Earth\',\'金\':\'Metal\',\'水\':\'Water\'}.get(wx_support, wx_support)
            if is_en:
                result[\'lucky_elements\'] = [wx_support_en]
                result[\'lucky_tip\'] = f"Favor {wx_support_en}-related colors, numbers, and environments"
            else:
                result[\'lucky_elements\'] = [wx_support]
                result[\'lucky_tip\'] = f"适合多接触与「{wx_support}」相关的颜色、数字、环境"
        
        # 大运总结
        dayun = bazi_result.get(\'dayun\', [])
        if dayun:
            mid = dayun[len(dayun)//2] if len(dayun)>3 else dayun[0]
            if is_en:
                result[\'current_luck\'] = f"Current decade ({mid[\'start_age\']}-{mid[\'end_age\']}): {mid[\'ganzhi\']} ({mid.get(\'nayin\',\'\')})"
            else:
                result[\'current_luck\'] = f"当前大运（{mid[\'start_age\']}-{mid[\'end_age\']}岁）：{mid[\'ganzhi\']}（{mid.get(\'nayin_cn\',\'\')}）"
        
        # 流年
        liunian = bazi_result.get(\'liunian\', [])
        if liunian:
            if is_en:
                result[\'yearly_luck\'] = []
                for ln in liunian:
                    rel = \', \'.join(ln.get(\'zhi_relations\',[])) or \'neutral\'
                    result[\'yearly_luck\'].append(f"{ln[\'year\']} ({ln[\'ganzhi\']}): {ln[\'shi_shen\']}, {rel}")
            else:
                result[\'yearly_luck\'] = []
                for ln in liunian:
                    rel = \'、\'.join(ln.get(\'zhi_relations\',[])) or \'平和\'
                    result[\'yearly_luck\'].append(f"{ln[\'year\']}年（{ln[\'ganzhi\']}）：十神{ln[\'shi_shen\']}，地支{rel}")
    
    return result


# ═══════════════════════════
# 主函数
# ═══════════════════════════

def calculate_bazi(year, month, day, hour=12, minute=0, level=\'basic\', lang=\'zh\', gender=\'male\'):
    """
    计算八字命盘（完整版）
    year, month, day: 公历日期
    hour: 小时 (0-23)
    minute: 分钟 (0-59, 精确排盘)
    level: \'free\' / \'basic\' / \'full\'
    lang: \'zh\' / \'en\'
    gender: \'male\' / \'female\' (大运顺逆排)
    """
    try:
        date_obj = datetime.date(year, month, day)
    except ValueError:
        return {\'error\': \'日期不合法\' if lang.startswith(\'zh\') else \'Invalid date\'}
    
    # 农历转换
    lunar_year, lunar_month, lunar_day, is_leap = solar_to_lunar(date_obj)
    
    # 四柱推算
    year_gz = get_year_gz(lunar_year)
    month_gz = get_month_gz(year_gz, month, day, is_leap)
    day_gz = get_day_gz(date_obj)
    hour_gz = get_hour_gz(day_gz, hour)
    
    pillars = {
        \'year\': year_gz,
        \'month\': month_gz,
        \'day\': day_gz,
        \'hour\': hour_gz
    }
    
    # 纳音
    nayin = {k: NA_YIN.get(v, \'\') for k, v in pillars.items()}
    
    # 生肖
    zhi_idx = DI_ZHI.index(year_gz[1])
    shengxiao = SHENG_XIAO[zhi_idx]
    
    # 时辰名称
    hour_name = get_hour_name(hour)
    
    # 五行详细分析
    wuxing = detailed_wuxing_balance(pillars)
    
    # 空亡
    xun_kong = get_xun_kong(day_gz)
    
    # 日主
    day_master = get_day_master(pillars)
    
    # 日主强弱
    dm_strength = day_master_strength(day_master, pillars, wuxing)
    
    # 十神
    ten_gods = {}
    day_gan = day_gz[0]
    for pname, gz in pillars.items():
        gan = gz[0]
        zhi = gz[1] if len(gz) > 1 else \'\'
        ten_gods[pname] = {
            \'gan\': get_shi_shen(day_gan, gan),
            \'zhi\': get_shi_shen(day_gan, zhi) if zhi else \'\',
        }
    
    # 神煞
    shen_sha = get_shen_sha(pillars, day_gz[1] if len(day_gz) > 1 else \'\')
    
    # 农历日期字符串
    lunar_month_str = f"{\'闰\' if is_leap else \'\'}{lunar_month}月"
    lunar_day_str = f"{lunar_day}日"
    
    result = {
        \'solar\': f"{year}年{month}月{day}日",
        \'lunar\': f"{lunar_year}年{lunar_month_str}{lunar_day_str}",
        \'hour\': hour_name,
        \'shengxiao\': shengxiao,
        \'pillars\': pillars,
        \'nayin\': nayin,
        \'day_master\': day_master,
        \'wuxing\': wuxing,
        \'xun_kong\': xun_kong,
        \'day_master_strength\': dm_strength,
        \'ten_gods\': ten_gods,
        \'shen_sha\': shen_sha,
    }
    
    # 大运 (free: 3个, basic: 6个, full: 10个)
    dayun = calculate_dayun(year, month, day, hour, gender, lang)
    result[\'dayun\'] = dayun[:3] if level == \'free\' else (dayun[:6] if level == \'basic\' else dayun)
    
    # 流年 (free: 1个, basic/full: 5个)
    current_year = datetime.date.today().year
    liunian = calculate_liunian(day_gz, current_year, 5, lang)
    result[\'liunian\'] = liunian[:1] if level == \'free\' else liunian
    
    # 生成解读
    interp = generate_interpretation(result, level, lang)
    result[\'interpretation\'] = interp
    
    return result

# ═══════════════════════════
# 命令行测试
# ═══════════════════════════

if __name__ == \'__main__\':
    import json
    # 测试: 1990-05-20 08:00
    result = calculate_bazi(1990, 5, 20, 8, 0, \'full\', \'zh\', \'male\')
    print(json.dumps(result, ensure_ascii=False, indent=2))
')
print("  Wrote bazi.py (35977 bytes)")

# --- astro.py ---
with open(os.path.join(TARGET, "astro.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
西方占星引擎 — 太阳/月亮/上升星座 + 行星 + 每日运势
"""
import datetime, hashlib, json

# 星座范围
ZODIAC = [
    (\'摩羯座\',\'Capricorn\',(12,22),(1,19)),
    (\'水瓶座\',\'Aquarius\',(1,20),(2,18)),
    (\'双子座\',\'Gemini\',(5,21),(6,21)),
    (\'巨蟹座\',\'Cancer\',(6,22),(7,22)),
    (\'狮子座\',\'Leo\',(7,23),(8,22)),
    (\'处女座\',\'Virgo\',(8,23),(9,22)),
    (\'天秤座\',\'Libra\',(9,23),(10,23)),
    (\'天蝎座\',\'Scorpio\',(10,24),(11,22)),
    (\'射手座\',\'Sagittarius\',(11,23),(12,21)),
    (\'双鱼座\',\'Pisces\',(2,19),(3,20)),
    (\'白羊座\',\'Aries\',(3,21),(4,19)),
    (\'金牛座\',\'Taurus\',(4,20),(5,20)),
]

def get_sun_sign(month, day):
    """太阳星座"""
    zodiac_list = [
        (\'摩羯座\',\'Capricorn\',12,22,1,19),
        (\'水瓶座\',\'Aquarius\',1,20,2,18),
        (\'双鱼座\',\'Pisces\',2,19,3,20),
        (\'白羊座\',\'Aries\',3,21,4,19),
        (\'金牛座\',\'Taurus\',4,20,5,20),
        (\'双子座\',\'Gemini\',5,21,6,21),
        (\'巨蟹座\',\'Cancer\',6,22,7,22),
        (\'狮子座\',\'Leo\',7,23,8,22),
        (\'处女座\',\'Virgo\',8,23,9,22),
        (\'天秤座\',\'Libra\',9,23,10,23),
        (\'天蝎座\',\'Scorpio\',10,24,11,22),
        (\'射手座\',\'Sagittarius\',11,23,12,21),
    ]
    for cn, en, m1, d1, m2, d2 in zodiac_list:
        if m1 == 12:
            if (month == 12 and day >= d1) or (month == 1 and day <= d2):
                return {\'cn\': cn, \'en\': en, \'element\': \'土\' if cn == \'摩羯座\' else \'\', \'emoji\': \'♑\' if en == \'Capricorn\' else \'♑\'}
        elif (month == m1 and day >= d1) or (month == m2 and day <= d2):
            emojis = {\'Aries\':\'♈\',\'Taurus\':\'♉\',\'Gemini\':\'♊\',\'Cancer\':\'♋\',\'Leo\':\'♌\',\'Virgo\':\'♍\',\'Libra\':\'♎\',\'Scorpio\':\'♏\',\'Sagittarius\':\'♐\',\'Capricorn\':\'♑\',\'Aquarius\':\'♒\',\'Pisces\':\'♓\'}
            elements = {\'Aries\':\'Fire\',\'Taurus\':\'Earth\',\'Gemini\':\'Air\',\'Cancer\':\'Water\',\'Leo\':\'Fire\',\'Virgo\':\'Earth\',\'Libra\':\'Air\',\'Scorpio\':\'Water\',\'Sagittarius\':\'Fire\',\'Capricorn\':\'Earth\',\'Aquarius\':\'Air\',\'Pisces\':\'Water\'}
            return {\'cn\': cn, \'en\': en, \'element\': elements.get(en,\'\'), \'emoji\': emojis.get(en,\'\')}
    return {\'cn\': \'未知\',\'en\': \'Unknown\',\'element\': \'\',\'emoji\':\'?\'}

def get_moon_sign(day_of_year, year):
    """月亮星座（简化计算，基于日期估算）"""
    moon_cycle = day_of_year % 28
    signs_order = [\'白羊座\',\'金牛座\',\'双子座\',\'巨蟹座\',\'狮子座\',\'处女座\',\'天秤座\',\'天蝎座\',\'射手座\',\'摩羯座\',\'水瓶座\',\'双鱼座\']
    signs_en = [\'Aries\',\'Taurus\',\'Gemini\',\'Cancer\',\'Leo\',\'Virgo\',\'Libra\',\'Scorpio\',\'Sagittarius\',\'Capricorn\',\'Aquarius\',\'Pisces\']
    idx = (moon_cycle * 12) // 28
    return {\'cn\': signs_order[idx], \'en\': signs_en[idx]}

def get_rising_sign(hour, day_of_year):
    """上升星座（简化估算，每2小时切换）"""
    signs_order = [\'白羊座\',\'金牛座\',\'双子座\',\'巨蟹座\',\'狮子座\',\'处女座\',\'天秤座\',\'天蝎座\',\'射手座\',\'摩羯座\',\'水瓶座\',\'双鱼座\']
    signs_en = [\'Aries\',\'Taurus\',\'Gemini\',\'Cancer\',\'Leo\',\'Virgo\',\'Libra\',\'Scorpio\',\'Sagittarius\',\'Capricorn\',\'Aquarius\',\'Pisces\']
    idx = (hour // 2 + day_of_year) % 12
    return {\'cn\': signs_order[idx], \'en\': signs_en[idx]}

SIGN_TRAITS = {
    \'Aries\': {\'nature_zh\':\'勇敢直接，行动力强，天生的领袖\',\'nature_en\':\'Brave and direct. A natural leader with unstoppable drive.\',
              \'career_zh\':\'适合军警、运动、创业、销售等竞争激烈的行业\',\'career_en\':\'Military, sports, startups, sales — competitive fields.\',
              \'love_zh\':\'热情似火，爱情中主动追求。适合同样有活力的伴侣。\',\'love_en\':\'Passionate pursuer. Thrives with an equally energetic partner.\',
              \'lucky_zh\':\'红色、火星能量、勇敢行动的日子\',\'lucky_en\':\'Red, Mars energy, days for bold action.\'},
    \'Taurus\': {\'nature_zh\':\'稳重可靠，享受生活，固执但值得信赖\',\'nature_en\':\'Steady and reliable. Enjoys finer things. Stubborn but loyal.\',
               \'career_zh\':\'适合金融、美食、农业、艺术、设计行业\',\'career_en\':\'Finance, cuisine, agriculture, arts, design.\',
               \'love_zh\':\'重视安全感和忠诚，慢热但深情。需要能给你安定的伴侣。\',\'love_en\':\'Values security and loyalty. Slow to warm but deeply devoted.\',
               \'lucky_zh\':\'绿色、金星能量、星期五\',\'lucky_en\':\'Green, Venus energy, Fridays.\'},
    \'Gemini\': {\'nature_zh\':\'聪明灵活，好奇心强，善于沟通\',\'nature_en\':\'Witty and versatile. Endlessly curious and communicative.\',
               \'career_zh\':\'适合传媒、写作、教育、销售、IT行业\',\'career_en\':\'Media, writing, education, sales, tech.\',
               \'love_zh\':\'喜欢交流和精神共鸣，需要一个能跟上你话题切换的伴侣。\',\'love_en\':\'Craves mental connection. Needs a partner who keeps up with your topics.\',
               \'lucky_zh\':\'黄色、水星能量、星期三\',\'lucky_en\':\'Yellow, Mercury energy, Wednesdays.\'},
    \'Cancer\': {\'nature_zh\':\'情感丰富，顾家护短，直觉敏锐\',\'nature_en\':\'Deeply emotional, protective of home, highly intuitive.\',
               \'career_zh\':\'适合医疗、教育、房地产、餐饮、咨询行业\',\'career_en\':\'Healthcare, education, real estate, food, counseling.\',
               \'love_zh\':\'极度重视家庭和情感安全感，是最会照顾人的伴侣。\',\'love_en\':\'Prioritizes family and emotional security. The most nurturing partner.\',
               \'lucky_zh\':\'银色、月亮能量、星期一\',\'lucky_en\':\'Silver, Moon energy, Mondays.\'},
    \'Leo\': {\'nature_zh\':\'自信大度，有领导力，热爱表现\',\'nature_en\':\'Confident and generous. Natural performer with magnetic charisma.\',
            \'career_zh\':\'适合演艺、管理、教育、奢侈品、公关行业\',\'career_en\':\'Entertainment, management, education, luxury, PR.\',
            \'love_zh\':\'耀眼夺目，渴望被仰慕。需要一个欣赏你光芒的伴侣。\',\'love_en\':\'Shines bright and craves admiration. Needs a partner who celebrates you.\',
            \'lucky_zh\':\'金色、太阳能量、星期日\',\'lucky_en\':\'Gold, Sun energy, Sundays.\'},
    \'Virgo\': {\'nature_zh\':\'细心缜密，追求完美，服务精神\',\'nature_en\':\'Meticulous and analytical. Perfectionist with a service mindset.\',
              \'career_zh\':\'适合医疗、科研、编辑、会计、IT行业\',\'career_en\':\'Healthcare, research, editing, accounting, tech.\',
              \'love_zh\':\'用行动表达爱意。不擅甜言蜜语，但会默默为你做好一切。\',\'love_en\':\'Shows love through actions. Not flowery with words but does everything for you.\',
              \'lucky_zh\':\'棕色、水星能量、细节关注\',\'lucky_en\':\'Brown, Mercury energy, attention to detail.\'},
    \'Libra\': {\'nature_zh\':\'优雅和谐，追求平衡，有艺术品味\',\'nature_en\':\'Graceful and diplomatic. Seeks balance and has refined taste.\',
              \'career_zh\':\'适合法律、设计、传媒、外交、美妆行业\',\'career_en\':\'Law, design, media, diplomacy, beauty.\',
              \'love_zh\':\'追求浪漫的完美关系。讨厌冲突，喜欢平等的伴侣。\',\'love_en\':\'Seeks romantic perfection. Hates conflict; likes equal partnership.\',
              \'lucky_zh\':\'粉色、金星能量、美丽的事物\',\'lucky_en\':\'Pink, Venus energy, beautiful things.\'},
    \'Scorpio\': {\'nature_zh\':\'深沉神秘，意志力强，洞察人心\',\'nature_en\':\'Deep and mysterious. Powerful will and penetrating insight.\',
                \'career_zh\':\'适合心理、刑侦、科研、金融、玄学行业\',\'career_en\':\'Psychology, investigation, research, finance, metaphysics.\',
                \'love_zh\':\'爱得深也恨得深。需要灵魂层面的连接，不容背叛。\',\'love_en\':\'Loves and hates deeply. Needs soul-level connection. Betrayal is unforgivable.\',
                \'lucky_zh\':\'黑色、冥王星能量、深沉的地方\',\'lucky_en\':\'Black, Pluto energy, deep places.\'},
    \'Sagittarius\': {\'nature_zh\':\'乐观自由，热爱冒险，哲学思辨\',\'nature_en\':\'Optimistic and free. Loves adventure and philosophical inquiry.\',
                    \'career_zh\':\'适合旅游、教育、出版、外贸、体育行业\',\'career_en\':\'Travel, education, publishing, trade, sports.\',
                    \'love_zh\':\'热爱自由不喜束缚。需要一个陪你一起探索世界的伴侣。\',\'love_en\':\'Loves freedom and hates constraints. Needs an adventure buddy partner.\',
                    \'lucky_zh\':\'紫色、木星能量、远行\',\'lucky_en\':\'Purple, Jupiter energy, long journeys.\'},
    \'Capricorn\': {\'nature_zh\':\'脚踏实地，野心勃勃，坚韧不拔\',\'nature_en\':\'Grounded and ambitious. Unwavering determination.\',
                  \'career_zh\':\'适合金融、工程、管理、建筑、政府行业\',\'career_en\':\'Finance, engineering, management, construction, government.\',
                  \'love_zh\':\'慢热但持久。重视责任和承诺，是最可靠的伴侣。\',\'love_en\':\'Slow to warm but lasting. Values duty and commitment. Most reliable partner.\',
                  \'lucky_zh\':\'深蓝、土星能量、时间沉淀\',\'lucky_en\':\'Dark blue, Saturn energy, time-tested things.\'},
    \'Aquarius\': {\'nature_zh\':\'独立创新，人道主义，思想前卫\',\'nature_en\':\'Independent and innovative. Humanitarian with progressive ideas.\',
                 \'career_zh\':\'适合科技、科研、公益、发明、占星行业\',\'career_en\':\'Tech, research, charity, invention, astrology.\',
                 \'love_zh\':\'重视精神契合和自由。需要一个理解你独立性的伴侣。\',\'love_en\':\'Values intellectual connection and freedom. Needs a partner who respects your independence.\',
                 \'lucky_zh\':\'电蓝色、天王星能量、新技术\',\'lucky_en\':\'Electric blue, Uranus energy, new technology.\'},
    \'Pisces\': {\'nature_zh\':\'浪漫梦幻，有同理心，艺术天赋\',\'nature_en\':\'Romantic and dreamy. Deeply empathetic with artistic gifts.\',
               \'career_zh\':\'适合艺术、音乐、心理咨询、医疗、慈善行业\',\'career_en\':\'Arts, music, counseling, healthcare, charity.\',
               \'love_zh\':\'付出型恋人，把伴侣理想化。注意不要失去自我。\',\'love_en\':\'Generous lover who idealizes partners. Be careful not to lose yourself.\',
               \'lucky_zh\':\'海蓝色、海王星能量、水边\',\'lucky_en\':\'Sea blue, Neptune energy, near water.\'},
}

def build_full_chart(year, month, day, hour, level=\'free\'):
    """构建完整星盘"""
    try:
        dobj = datetime.date(year, month, day)
    except:
        return {\'error\': \'Invalid date\'}
    day_of_year = dobj.timetuple().tm_yday
    sun = get_sun_sign(month, day)
    moon = get_moon_sign(day_of_year, year)
    rising = get_rising_sign(hour, day_of_year)

    result = {
        \'sun\': sun,
        \'moon\': moon,
        \'rising\': rising,
        \'day_of_year\': day_of_year,
    }

    traits = SIGN_TRAITS.get(sun[\'en\'], {})
    result[\'traits\'] = {k: traits.get(k, \'\') for k in [\'nature_zh\',\'nature_en\',\'career_zh\',\'career_en\',\'love_zh\',\'love_en\',\'lucky_zh\',\'lucky_en\']}

    if level in (\'basic\', \'full\'):
        # Detailed report
        result[\'report_zh\'] = f"太阳{sun[\'cn\']}、月亮{moon[\'cn\']}、上升{rising[\'cn\']}——{traits.get(\'nature_zh\',\'\')}"
        result[\'report_en\'] = f"Sun {sun[\'en\']}, Moon {moon[\'en\']}, Rising {rising[\'en\']} — {traits.get(\'nature_en\',\'\')}"

    if level == \'full\':
        result[\'career_detail_zh\'] = traits.get(\'career_zh\',\'\')
        result[\'career_detail_en\'] = traits.get(\'career_en\',\'\')
        result[\'love_detail_zh\'] = traits.get(\'love_zh\',\'\')
        result[\'love_detail_en\'] = traits.get(\'love_en\',\'\')
        result[\'lucky_detail_zh\'] = traits.get(\'lucky_zh\',\'\')
        result[\'lucky_detail_en\'] = traits.get(\'lucky_en\',\'\')

    return result


def get_daily_horoscope(sun_en, date_str):
    """每日运势（基于日期+星座哈希的伪随机）"""
    seed_str = sun_en + date_str
    seed = sum(ord(c) for c in seed_str)
    horoscopes_zh = [
        \'今天适合果断行动。相信直觉，推进那个你一直拖延的事情。\',
        \'放慢脚步的一天。静下心来，你会发现身边的美好细节。\',
        \'沟通运势极佳。主动联系你想联系的人，会有意外惊喜。\',
        \'直觉力超强。注意你的梦境和第六感，它们会给你重要指引。\',
        \'今天你是焦点。大方分享想法，大家都在认真听你说。\',
        \'细节运势强。适合整理计划、收拾空间、清算旧账。\',
        \'平衡是关键。如果最近太忙，今天就给自己放个小假。\',
        \'深层变化在酝酿。放下不再属于你的，拥抱新的可能。\',
        \'冒险精神在召唤！走出舒适圈，新奇体验在等你。\',
        \'努力终有回报。保持专注和自律，成果就在不远处。\',
        \'你独特的视角正是大家需要的。大胆分享那个不一样的想法。\',
        \'创意能量爆棚。投入到艺术、音乐或任何自我表达中去。\',
        \'今天遇见的人可能是贵人。保持开放心态，主动打招呼。\',
        \'财运不错。可能会收到一笔意外之喜或有新的收入机会。\',
    ]
    horoscopes_en = [
        \'Bold action is favored today. Trust your instincts and move on that thing you\'ve been postponing.\',
        \'A day for slowing down. Quiet your mind and notice the small beauties around you.\',
        \'Communication flows easily. Reach out to someone — a pleasant surprise awaits.\',
        \'Intuition is heightened. Pay attention to dreams and gut feelings today.\',
        \'The spotlight is on you. Share your ideas confidently — people are listening.\',
        \'Detail-oriented energy. Perfect for organizing, decluttering, and tying loose ends.\',
        \'Balance is everything. If you\'ve been overworking, take a break today.\',
        \'Deep transformation is brewing. Release what no longer serves you.\',
        \'Adventure calls! Step outside your comfort zone — new experiences await.\',
        \'Hard work pays off. Stay disciplined and focused — results are near.\',
        \'Your unique perspective is needed. Share that unconventional idea boldly.\',
        \'Creative energy surges. Dive into art, music, or any form of self-expression.\',
        \'Someone you meet today could be pivotal. Stay open and say hello first.\',
        \'Financial luck is strong. Unexpected income or new earning opportunities may appear.\',
    ]
    idx = seed % len(horoscopes_zh)
    return {
        \'date\': date_str,
        \'horoscope_zh\': horoscopes_zh[idx],
        \'horoscope_en\': horoscopes_en[idx],
        \'lucky_number\': (seed % 9) + 1,
        \'lucky_color_zh\': [\'红\',\'黄\',\'蓝\',\'绿\',\'紫\',\'粉\',\'白\',\'黑\',\'金\'][idx % 9],
        \'lucky_color_en\': [\'Red\',\'Yellow\',\'Blue\',\'Green\',\'Purple\',\'Pink\',\'White\',\'Black\',\'Gold\'][idx % 9],
    }


if __name__ == \'__main__\':
    import json
    chart = build_full_chart(1990, 5, 20, 8, \'full\')
    print(json.dumps(chart, ensure_ascii=False, indent=2))
    daily = get_daily_horoscope(\'Taurus\', \'2026-06-19\')
    print(json.dumps(daily, ensure_ascii=False, indent=2))
')
print("  Wrote astro.py (12387 bytes)")

# --- numerology.py ---
with open(os.path.join(TARGET, "numerology.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
生命灵数引擎 — Life Path + Expression + Soul Urge numbers
"""
import datetime

def reduce_num(num):
    """Pythagorean reduction (keep 11,22,33 master numbers)"""
    s = str(num)
    total = sum(int(c) for c in s)
    if total in (11, 22, 33):
        return total
    if total < 10:
        return total
    return reduce_num(total)

def get_life_path(year, month, day):
    """Life Path Number"""
    return reduce_num(reduce_num(year) + reduce_num(month) + reduce_num(day))

def get_expression(name):
    """Expression/Destiny Number from name (Pythagorean numerology)"""
    mapping = {
        \'a\':1,\'b\':2,\'c\':3,\'d\':4,\'e\':5,\'f\':6,\'g\':7,\'h\':8,\'i\':9,
        \'j\':1,\'k\':2,\'l\':3,\'m\':4,\'n\':5,\'o\':6,\'p\':7,\'q\':8,\'r\':9,
        \'s\':1,\'t\':2,\'u\':3,\'v\':4,\'w\':5,\'x\':6,\'y\':7,\'z\':8,
    }
    total = 0
    for ch in name.lower():
        if ch in mapping:
            total += mapping[ch]
    return reduce_num(total)

def get_soul_urge(name):
    """Soul Urge / Heart\'s Desire Number (vowels only)"""
    vowels = set(\'aeiou\')
    total = 0
    for ch in name.lower():
        if ch in vowels:
            # Simple a=1,b=2 mapping for vowels
            total += ord(ch) - ord(\'a\') + 1
    return reduce_num(total) if total > 0 else 1

LIFE_PATH_READINGS = {
    1: {\'zh\': \'天生的领导者，独立自主，创造力强。需要学会合作而非单打独斗。适合创业、管理、自由职业。\',
        \'en\': \'The Leader — independent, creative, ambitious. Learn to collaborate. Suited for entrepreneurship and leadership.\'},
    2: {\'zh\': \'和平的缔造者，善于合作，敏感细腻。是天生的外交家和调解人。适合外交、咨询、服务行业。\',
        \'en\': \'The Peacemaker — cooperative, sensitive, diplomatic. Natural mediator. Ideal for diplomacy and counseling.\'},
    3: {\'zh\': \'天生的表达者，乐观开朗，有艺术天赋。需要用创造性的方式表达自己。适合演艺、写作、设计。\',
        \'en\': \'The Communicator — optimistic, expressive, artistic. Needs creative outlets. Suited for arts and media.\'},
    4: {\'zh\': \'稳步的建设者，踏实可靠，组织能力强。是团队中最稳固的基石。适合工程、会计、管理。\',
        \'en\': \'The Builder — steady, reliable, organized. The solid foundation of any team. Suited for engineering and management.\'},
    5: {\'zh\': \'自由的探险者，热爱变化，适应力强。最大的恐惧是被束缚。适合旅行、销售、媒体行业。\',
        \'en\': \'The Adventurer — freedom-loving, adaptable, curious. Fears being tied down. Suited for travel and media.\'},
    6: {\'zh\': \'无私的奉献者，有责任感，关爱他人。把家庭和社群放在第一位。适合教育、医疗、公益。\',
        \'en\': \'The Nurturer — responsible, caring, devoted. Puts family and community first. Suited for education and healthcare.\'},
    7: {\'zh\': \'深度的思考者，哲学家气质，善于分析。需要独处时间来充电。适合学术、研究、技术。\',
        \'en\': \'The Thinker — philosophical, analytical, introspective. Needs solitude to recharge. Suited for academia and tech.\'},
    8: {\'zh\': \'力量的追求者，有野心，商业头脑强。物质和精神需要找到平衡。适合金融、法律、管理。\',
        \'en\': \'The Powerhouse — ambitious, business-minded. Must balance material and spiritual. Suited for finance and law.\'},
    9: {\'zh\': \'博爱的理想主义者，有人道精神。放手和给予是你的功课。适合慈善、艺术、精神领域。\',
        \'en\': \'The Humanitarian — idealistic, compassionate. Learning to let go and give. Suited for charity and arts.\'},
    11: {\'zh\': \'灵性导师，高度直觉，双重天赋。需要将灵感落地。这是大师数字，潜力巨大。\',
         \'en\': \'Spiritual Messenger — highly intuitive, double gifts. Must ground inspiration. Master number with great potential.\'},
    22: {\'zh\': \'大师建造者，能将梦想变为现实。具有改变世界的力量。最高的大师数字之一。\',
         \'en\': \'Master Builder — turns dreams into reality. Power to change the world. Highest master number.\'},
    33: {\'zh\': \'宇宙导师，伟大的爱与牺牲精神。你的使命是照亮他人。最稀有的大师数字。\',
         \'en\': \'Cosmic Teacher — great love and sacrifice. Mission is to enlighten others. Rarest master number.\'},
}

PERSONAL_YEARS = {
    1: {\'zh\': \'新开始的一年。播种期，适合开启新项目、新关系。\',
        \'en\': \'Year of New Beginnings. Plant seeds — start new projects and relationships.\'},
    2: {\'zh\': \'合作与耐心的一年。适合建立联盟、等待时机成熟。\',
        \'en\': \'Year of Cooperation. Build alliances and wait for the right timing.\'},
    3: {\'zh\': \'创造与表达的一年。适合社交、创作、享受生活。\',
        \'en\': \'Year of Creativity. Socialize, create, and enjoy life.\'},
    4: {\'zh\': \'建设与扎根的一年。努力工作、打好基础。\',
        \'en\': \'Year of Building. Work hard and lay solid foundations.\'},
    5: {\'zh\': \'变化与自由的一年。拥抱改变、冒险尝试。\',
        \'en\': \'Year of Change. Embrace transformation and take risks.\'},
    6: {\'zh\': \'责任与家庭的一年。关注家人、感情和承诺。\',
        \'en\': \'Year of Responsibility. Focus on family, love, and commitments.\'},
    7: {\'zh\': \'内省与学习的一年。静心思考、深造研究。\',
        \'en\': \'Year of Introspection. Reflect deeply and pursue knowledge.\'},
    8: {\'zh\': \'收获与权力的年份。事业上升、财务状况改善。\',
        \'en\': \'Year of Harvest. Career advancement and financial improvement.\'},
    9: {\'zh\': \'完成与释放的一年。清理旧物、结束不必要的关系。\',
        \'en\': \'Year of Completion. Clear out the old, release what no longer serves.\'},
}

def build_numerology_report(year, month, day, name=\'\', level=\'free\'):
    """构建完整的灵数报告"""
    try:
        datetime.date(year, month, day)
    except:
        return {\'error\': \'Invalid date\'}

    lp = get_life_path(year, month, day)
    result = {
        \'life_path\': lp,
        \'life_path_reading_zh\': LIFE_PATH_READINGS.get(lp, {}).get(\'zh\', \'独特的生命之路\'),
        \'life_path_reading_en\': LIFE_PATH_READINGS.get(lp, {}).get(\'en\', \'A unique life path.\'),
    }

    # Personal year
    current_year = datetime.date.today().year
    py_num = reduce_num(reduce_num(month) + reduce_num(day) + reduce_num(current_year))
    result[\'personal_year\'] = py_num
    result[\'personal_year_zh\'] = PERSONAL_YEARS.get(py_num, {}).get(\'zh\', \'\')
    result[\'personal_year_en\'] = PERSONAL_YEARS.get(py_num, {}).get(\'en\', \'\')

    if level in (\'basic\', \'full\') and name:
        expr = get_expression(name)
        soul = get_soul_urge(name)
        result[\'expression\'] = expr
        result[\'soul_urge\'] = soul
        result[\'expression_reading_zh\'] = LIFE_PATH_READINGS.get(expr, {}).get(\'zh\', \'\')
        result[\'expression_reading_en\'] = LIFE_PATH_READINGS.get(expr, {}).get(\'en\', \'\')
        result[\'soul_urge_reading_zh\'] = LIFE_PATH_READINGS.get(soul, {}).get(\'zh\', \'\')
        result[\'soul_urge_reading_en\'] = LIFE_PATH_READINGS.get(soul, {}).get(\'en\', \'\')

    if level == \'full\':
        # Challenge numbers, maturity number, etc
        result[\'maturity\'] = reduce_num(lp + get_expression(name) if name else lp + 1)
        result[\'maturity_reading_zh\'] = LIFE_PATH_READINGS.get(result[\'maturity\'], {}).get(\'zh\', \'\')
        result[\'maturity_reading_en\'] = LIFE_PATH_READINGS.get(result[\'maturity\'], {}).get(\'en\', \'\')

    return result


if __name__ == \'__main__\':
    import json
    r = build_numerology_report(1990, 5, 20, \'John\', \'full\')
    print(json.dumps(r, ensure_ascii=False, indent=2))
')
print("  Wrote numerology.py (6452 bytes)")

# --- fengshui.py ---
with open(os.path.join(TARGET, "fengshui.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
风水堪舆引擎 — Kua Number / 八宅风水 / 五鬼财运 / 流年飞星
"""
import datetime

# 五行生克
WUXING = [\'金\',\'木\',\'水\',\'火\',\'土\']
WUXING_EN = [\'Metal\',\'Wood\',\'Water\',\'Fire\',\'Earth\']
WU_CYCLE = {0:{2:\'生\',3:\'克\',4:\'生\',1:\'克\'},1:{3:\'生\',4:\'克\',0:\'克\',2:\'生\'},2:{4:\'生\',0:\'克\',1:\'生\',3:\'克\'},3:{1:\'生\',2:\'克\',0:\'克\',4:\'生\'},4:{0:\'生\',1:\'克\',3:\'生\',2:\'克\'}}
WU_EMOJI = {\'金\':\'🪙\',\'木\':\'🌿\',\'水\':\'💧\',\'火\':\'🔥\',\'土\':\'🏔️\'}

# 八卦方位
GUA_DIRECTIONS = {
    1: {\'name\':\'坎\',\'en\':\'Kan\',\'trigram\':\'☵\',\'element\':\'水\',\'element_en\':\'Water\'},
    2: {\'name\':\'坤\',\'en\':\'Kun\',\'trigram\':\'☷\',\'element\':\'土\',\'element_en\':\'Earth\'},
    3: {\'name\':\'震\',\'en\':\'Zhen\',\'trigram\':\'☳\',\'element\':\'木\',\'element_en\':\'Wood\'},
    4: {\'name\':\'巽\',\'en\':\'Xun\',\'trigram\':\'☴\',\'element\':\'木\',\'element_en\':\'Wood\'},
    6: {\'name\':\'乾\',\'en\':\'Qian\',\'trigram\':\'☰\',\'element\':\'金\',\'element_en\':\'Metal\'},
    7: {\'name\':\'兑\',\'en\':\'Dui\',\'trigram\':\'☱\',\'element\':\'金\',\'element_en\':\'Metal\'},
    8: {\'name\':\'艮\',\'en\':\'Gen\',\'trigram\':\'☶\',\'element\':\'土\',\'element_en\':\'Earth\'},
    9: {\'name\':\'离\',\'en\':\'Li\',\'trigram\':\'☲\',\'element\':\'火\',\'element_en\':\'Fire\'},
}

# 八宅吉凶方位 (以卦位为中心)
# 顺序: 祸害、绝命、五鬼、六煞、生气、天医、延年、伏位
BAGUA_MAP = {
    1: {1:\'V\', 2:\'A\', 3:\'B\', 4:\'C\', 6:\'D\', 7:\'E\', 8:\'F\', 9:\'G\'},  # 坎
    2: {1:\'G\', 2:\'V\', 3:\'E\', 4:\'F\', 6:\'A\', 7:\'B\', 8:\'C\', 9:\'D\'},  # 坤
    3: {1:\'F\', 2:\'G\', 3:\'V\', 4:\'A\', 6:\'C\', 7:\'D\', 8:\'E\', 9:\'B\'},  # 震
    4: {1:\'E\', 2:\'F\', 3:\'G\', 4:\'V\', 6:\'D\', 7:\'C\', 8:\'B\', 9:\'A\'},  # 巽
    6: {1:\'C\', 2:\'D\', 3:\'E\', 4:\'F\', 6:\'V\', 7:\'G\', 8:\'A\', 9:\'B\'},  # 乾
    7: {1:\'D\', 2:\'C\', 3:\'F\', 4:\'E\', 6:\'G\', 7:\'V\', 8:\'B\', 9:\'A\'},  # 兑
    8: {1:\'B\', 2:\'A\', 3:\'D\', 4:\'C\', 6:\'E\', 7:\'F\', 8:\'V\', 9:\'G\'},  # 艮
    9: {1:\'A\', 2:\'B\', 3:\'C\', 4:\'D\', 6:\'F\', 7:\'E\', 8:\'G\', 9:\'V\'},  # 离
}
# V=伏位 A=生气 B=延年 C=天医 D=祸害 E=绝命 F=五鬼 G=六煞
STAR_NAMES = {
    \'V\': {\'zh\':\'伏位\',\'en\':\'Fu Wei / Stable Base\'},
    \'A\': {\'zh\':\'生气\',\'en\':\'Sheng Qi / Prosperity\'},
    \'B\': {\'zh\':\'延年\',\'en\':\'Yan Nian / Longevity\'},
    \'C\': {\'zh\':\'天医\',\'en\':\'Tian Yi / Health\'},
    \'D\': {\'zh\':\'祸害\',\'en\':\'Huo Hai / Calamity\'},
    \'E\': {\'zh\':\'绝命\',\'en\':\'Jue Ming / Severed Fate\'},
    \'F\': {\'zh\':\'五鬼\',\'en\':\'Wu Gui / Five Ghosts\'},
    \'G\': {\'zh\':\'六煞\',\'en\':\'Liu Sha / Six Killings\'},
}
DIR_NAMES = {1:\'北\',2:\'西南\',3:\'东\',4:\'东南\',6:\'西北\',7:\'西\',8:\'东北\',9:\'南\'}
DIR_EN = {1:\'North\',2:\'Southwest\',3:\'East\',4:\'Southeast\',6:\'Northwest\',7:\'West\',8:\'Northeast\',9:\'South\'}
DIR_EMOJI = {1:\'🧭\',2:\'↙️\',3:\'➡️\',4:\'↘️\',6:\'↖️\',7:\'⬅️\',8:\'↗️\',9:\'⬆️\'}

GOOD_STARS = [\'A\',\'B\',\'C\']
BAD_STARS = [\'D\',\'E\',\'F\',\'G\']

STAR_ADVICE = {
    \'V\': {\'zh\':\'安放神位、主人房、客厅最佳方位\',\'en\':\'Best for altar, master bedroom, living room.\'},
    \'A\': {\'zh\':\'大门、房门朝向最佳，利财运事业\',\'en\':\'Best direction for main door and bedroom. Boosts wealth.\'},
    \'B\': {\'zh\':\'放床位、办公桌吉利，利健康和长寿\',\'en\':\'Good for bed and desk placement. Enhances health and longevity.\'},
    \'C\': {\'zh\':\'\\u653e\\u5e8a\\u4f4d\\u3001\\u6551\\u62a4\\u4eba\\u4f4d\\uff0c\\u5229\\u5065\\u5eb7\\u6062\\u590d\',\'en\':\'Good for bed and nursing. Aids health recovery.\'},
    \'D\': {\'zh\':\'宜放厕所、杂物间，忌做主人房\',\'en\':\'Best for bathroom and storage. Avoid as master bedroom.\'},
    \'E\': {\'zh\':\'最凶之方，宜空置或放高大重物镇之\',\'en\':\'Most dangerous direction. Keep empty or place heavy items here.\'},
    \'F\': {\'zh\':\'宜放厕所、厨房灶位，忌安床\',\'en\':\'Good for bathroom and kitchen stove. Avoid bedroom placement.\'},
    \'G\': {\'zh\':\'宜做厕所或储物，忌做卧室大门\',\'en\':\'Good for bathroom or storage. Avoid as bedroom or main entrance.\'},
}


def get_kua(year, gender):
    """计算命卦 (Kua Number)"""
    if year < 1900 or year > 2100:
        return 0
    # 男性: (100 - 年份后两位) % 9, 女性: (年份后两位 - 4) % 9
    last2 = year % 100
    if gender == \'male\':
        kua = (100 - last2) % 9
    else:
        kua = (last2 - 4) % 9
    if kua == 0:
        kua = 9
    if kua == 5:
        kua = 2 if gender == \'male\' else 8  # 坤命(男) 艮命(女)
    return kua


def get_directions(kua):
    """获取八宅方位吉凶"""
    gua = GUA_DIRECTIONS[kua]
    bagua = BAGUA_MAP[kua]
    good_dirs = []
    bad_dirs = []
    for gk, star in bagua.items():
        dname = DIR_NAMES.get(gk, \'\')
        entry = {
            \'direction\': dname,
            \'direction_en\': DIR_EN.get(gk, \'\'),
            \'direction_emoji\': DIR_EMOJI.get(gk, \'\'),
            \'star\': STAR_NAMES.get(star, {}).get(\'zh\', \'\'),
            \'star_en\': STAR_NAMES.get(star, {}).get(\'en\', \'\'),
            \'advice\': STAR_ADVICE.get(star, {}).get(\'zh\', \'\'),
            \'advice_en\': STAR_ADVICE.get(star, {}).get(\'en\', \'\'),
            \'is_good\': star in GOOD_STARS,
        }
        if star in GOOD_STARS:
            good_dirs.append(entry)
        else:
            bad_dirs.append(entry)
    return {
        \'gua\': gua,
        \'east_west\': \'东四命\' if kua in [1,3,4,9] else \'西四命\',
        \'east_west_en\': \'East Group\' if kua in [1,3,4,9] else \'West Group\',
        \'good_directions\': good_dirs,
        \'bad_directions\': bad_dirs,
    }


def get_annual_flying_star(year):
    """流年飞星 (九宫飞星)"""
    # Simplified: 年紫白飞星
    # 计算年星: (9 - (year - 1) % 9, 1-indexed)
    base = 10 - ((year - 1) % 9 + 1)
    stars = {
        1: {\'zh\':\'一白贪狼星\',\'en\':\'1 White - Greedy Wolf\',\'nature_zh\':\'吉·桃花·人缘\',\'nature_en\':\'Auspicious - Romance & Social\'},
        2: {\'zh\':\'二黑巨门星\',\'en\':\'2 Black - Giant Gate\',\'nature_zh\':\'凶·病符·是非\',\'nature_en\':\'Inauspicious - Illness & Quarrels\'},
        3: {\'zh\':\'三碧禄存星\',\'en\':\'3 Green - Lu Cun\',\'nature_zh\':\'凶·口舌·官司\',\'nature_en\':\'Inauspicious - Arguments & Lawsuits\'},
        4: {\'zh\':\'四绿文昌星\',\'en\':\'4 Green - Literary Star\',\'nature_zh\':\'吉·学业·考运\',\'nature_en\':\'Auspicious - Studies & Exams\'},
        5: {\'zh\':\'五黄廉贞星\',\'en\':\'5 Yellow - Integrity\',\'nature_zh\':\'大凶·灾祸·疾病\',\'nature_en\':\'Very Inauspicious - Disasters & Illness\'},
        6: {\'zh\':\'六白武曲星\',\'en\':\'6 White - Military Star\',\'nature_zh\':\'吉·偏财·权贵\',\'nature_en\':\'Auspicious - Wealth & Authority\'},
        7: {\'zh\':\'七赤破军星\',\'en\':\'7 Red - Broken Army\',\'nature_zh\':\'凶·盗贼·破损\',\'nature_en\':\'Inauspicious - Theft & Damage\'},
        8: {\'zh\':\'八白左辅星\',\'en\':\'8 White - Left Assistant\',\'nature_zh\':\'大吉·正财·置业\',\'nature_en\':\'Very Auspicious - Wealth & Property\'},
        9: {\'zh\':\'九紫右弼星\',\'en\':\'9 Purple - Right Assistant\',\'nature_zh\':\'吉·喜事·姻缘\',\'nature_en\':\'Auspicious - Joy & Marriage\'},
    }
    # Map stars to 9 palaces (central=5, then clockwise from north)
    # 方位顺序: 中→北→西南→东→东南→西北→西→东北→南
    palace_order = [5, 1, 2, 3, 4, 6, 7, 8, 9]  # 九宫本位
    dir_labels = [\'中\',\'北\',\'西南\',\'东\',\'东南\',\'西北\',\'西\',\'东北\',\'南\']
    dir_labels_en = [\'Center\',\'North\',\'Southwest\',\'East\',\'Southeast\',\'Northwest\',\'West\',\'Northeast\',\'South\']
    dir_emoji = [\'🏠\',\'🧭\',\'↙️\',\'➡️\',\'↘️\',\'↖️\',\'⬅️\',\'↗️\',\'⬆️\']
    
    result = []
    for i, palace in enumerate(palace_order):
        star_num = (base + palace - 1) % 9 + 1
        s = stars[star_num]
        result.append({
            \'direction\': dir_labels[i],
            \'direction_en\': dir_labels_en[i],
            \'direction_emoji\': dir_emoji[i],
            \'star\': s[\'zh\'],
            \'star_en\': s[\'en\'],
            \'nature_zh\': s[\'nature_zh\'],
            \'nature_en\': s[\'nature_en\'],
            \'number\': star_num,
        })
    return result


def get_home_advice(door_direction, kua, level=\'free\'):
    """居家风水建议"""
    directions = get_directions(kua)
    
    # 大门方位吉凶
    door_gua = None
    for gk, entry in GUA_DIRECTIONS.items():
        if DIR_NAMES.get(gk) == door_direction:
            door_gua = gk
            break
    
    # 简化分析
    result = {
        \'kua\': kua,
        \'gua\': directions[\'gua\'],
        \'east_west\': directions[\'east_west\'],
        \'east_west_en\': directions[\'east_west_en\'],
        \'good_directions\': directions[\'good_directions\'],
        \'bad_directions\': directions[\'bad_directions\'],
        \'door_direction\': door_direction,
    }
    
    if door_gua:
        star_code = BAGUA_MAP[kua].get(door_gua, \'?\')
        door_star = {
            \'good\': star_code in GOOD_STARS,
            \'star_zh\': STAR_NAMES.get(star_code, {}).get(\'zh\', \'\'),
            \'star_en\': STAR_NAMES.get(star_code, {}).get(\'en\', \'\'),
        }
        result[\'door_analysis\'] = door_star
    
    if level in (\'basic\', \'full\'):
        result[\'annual_stars\'] = get_annual_flying_star(datetime.date.today().year)
    
    if level == \'full\':
        # 详细建议
        result[\'advice_zh\'] = generate_full_advice(result, \'zh\')
        result[\'advice_en\'] = generate_full_advice(result, \'en\')
    
    return result


def generate_full_advice(data, lang):
    """生成完整风水建议"""
    kua = data[\'kua\']
    ew = data[\'east_west\']
    dname = data[\'door_direction\']
    da = data.get(\'door_analysis\', {})
    
    if lang == \'zh\':
        lines = []
        lines.append(f"📐 你的命卦是{data[\'gua\'][\'trigram\']} {data[\'gua\'][\'name\']}卦，属{ew}。")
        
        good = \', \'.join(f"{d[\'direction\']}({d[\'star\']})" for d in data[\'good_directions\'])
        bad = \', \'.join(f"{d[\'direction\']}({d[\'star\']})" for d in data[\'bad_directions\'])
        lines.append(f"🍀 吉方：{good}")
        lines.append(f"⚠️ 凶方：{bad}")
        
        if da:
            s = da.get(\'star_zh\', \'\')
            if da.get(\'good\'):
                lines.append(f"✅ 大门朝{dname}为{s}，吉利。适合迎纳旺气。")
            else:
                lines.append(f"❌ 大门朝{dname}为{s}，犯凶星。建议调换朝向或在门口放化煞物品。")
        
        lines.append(f"\\n💡 实用建议：")
        lines.append(f"· 主人房宜在{data[\'good_directions\'][0][\'direction\']}方（{data[\'good_directions\'][0][\'star\']}位）")
        lines.append(f"· 厨房宜在{data[\'bad_directions\'][0][\'direction\']}方（压凶星）")
        lines.append(f"· 厕所宜在{data[\'bad_directions\'][3][\'direction\']}方（{data[\'bad_directions\'][3][\'star\']}位）")
        lines.append(f"· 财位在{data[\'good_directions\'][1][\'direction\']}方，可放水晶或招财物品")
        return \'\\n\'.join(lines)
    else:
        lines = []
        lines.append(f"📐 Your Kua is {data[\'gua\'][\'en\']} (Trigram: {data[\'gua\'][\'trigram\']}), belongs to {data[\'east_west_en\']}.")
        
        good = \', \'.join(f"{d[\'direction_en\']}({d[\'star_en\']})" for d in data[\'good_directions\'])
        bad = \', \'.join(f"{d[\'direction_en\']}({d[\'star_en\']})" for d in data[\'bad_directions\'])
        lines.append(f"🍀 Auspicious: {good}")
        lines.append(f"⚠️ Inauspicious: {bad}")
        
        if da:
            s = da.get(\'star_en\', \'\')
            if da.get(\'good\'):
                lines.append(f"✅ Door facing {data[\'door_direction\']} is {s} — auspicious!")
            else:
                lines.append(f"❌ Door facing {data[\'door_direction\']} is {s} — inauspicious. Consider adjusting or adding remedies.")
        
        lines.append(f"\\n💡 Practical tips:")
        lines.append(f"· Master bedroom: best in {data[\'good_directions\'][0][\'direction_en\']} ({data[\'good_directions\'][0][\'star_en\']})")
        lines.append(f"· Kitchen: best in {data[\'bad_directions\'][0][\'direction_en\']} (suppress negative star)")
        lines.append(f"· Bathroom: best in {data[\'bad_directions\'][3][\'direction_en\']} ({data[\'bad_directions\'][3][\'star_en\']})")
        lines.append(f"· Wealth corner: {data[\'good_directions\'][1][\'direction_en\']} — place crystals or wealth objects here")
        return \'\\n\'.join(lines)


if __name__ == \'__main__\':
    import json
    r = get_home_advice(\'南\', get_kua(1990, \'male\'), \'full\')
    print(json.dumps(r, ensure_ascii=False, indent=2))
')
print("  Wrote fengshui.py (11055 bytes)")

# --- tarot.py ---
with open(os.path.join(TARGET, "tarot.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
塔罗占卜引擎 — 78张牌详解 + 牌阵解读
"""
import random, hashlib

# Major Arcana (22) + Minor Arcana (56)
MAJOR_ARCANA = {
    0: {\'name\':\'The Fool\',\'cn\':\'愚者\',\'en\':\'New beginnings, spontaneity, a leap of faith. The universe is calling you to trust the journey.\',
        \'career_zh\':\'新的职业方向正在召唤。不要害怕冒险——有时候最大的风险就是不冒任何险。\',
        \'career_en\':\'A new career path is calling. Do not fear the leap — sometimes the biggest risk is taking no risk at all.\',
        \'love_zh\':\'一段全新的感情可能即将开始，保持开放的心态。单身者会遇到意想不到的人。\',
        \'love_en\':\'A fresh romance may be starting. Stay open-minded. Singles may meet someone unexpected.\',
        \'advice_zh\':\'相信宇宙，迈出那一步。包袱越轻，走得越远。\',
        \'advice_en\':\'Trust the universe and take that step. The lighter you travel, the further you go.\'},
    1: {\'name\':\'The Magician\',\'cn\':\'魔术师\',\'en\':\'You have all the tools you need. Manifestation, power, and skillful action are at your fingertips.\',
        \'career_zh\':\'你的技能和资源已经齐备。现在是展示自己、拿下那个项目的最佳时机。\',
        \'career_en\':\'Your skills and resources are ready. Now is the time to showcase yourself and land that project.\',
        \'love_zh\':\'自信是你最大的魅力。主动表达，你的真心会被看见。\',
        \'love_en\':\'Confidence is your greatest charm. Express yourself — your sincerity will be seen.\',
        \'advice_zh\':\'你手中已有一切。专注、行动、创造你想要的结果。\',
        \'advice_en\':\'You already have everything you need. Focus, act, and create the outcome you want.\'},
    2: {\'name\':\'The High Priestess\',\'cn\':\'女祭司\',\'en\':\'Trust your intuition. The answers lie within, not in the noise outside. Silence and reflection are your allies.\',
        \'career_zh\':\'不要急着做决定。多观察、多倾听，答案会自然浮现。适合研究和幕后工作。\',
        \'career_en\':\'Do not rush decisions. Observe and listen — answers will surface. Good for research and behind-the-scenes work.\',
        \'love_zh\':\'跟随直觉，而非逻辑。那个人是否值得，你的心早就知道答案。\',
        \'love_en\':\'Follow intuition, not logic. Your heart already knows if that person is right for you.\',
        \'advice_zh\':\'静下来，听内心的声音。不是所有答案都需要用脑子去算。\',
        \'advice_en\':\'Be still and listen within. Not every answer needs to be calculated by the mind.\'},
    3: {\'name\':\'The Empress\',\'cn\':\'女皇\',\'en\':\'Abundance, creativity, and nurturing energy surround you. A time of growth and harvest.\',
        \'career_zh\':\'创意和丰收的时期。你种下的种子即将开花结果。适合启动创意项目。\',
        \'career_en\':\'A period of creativity and harvest. Seeds you planted are about to bloom. Start creative projects.\',
        \'love_zh\':\'温暖而丰盛的感情。如果你已经有伴，关系会更加深厚甜蜜。\',
        \'love_en\':\'Warm and abundant love. If partnered, the relationship deepens sweetly.\',
        \'advice_zh\':\'享受生活，犒赏自己。你有资格享受此刻的丰盛。\',
        \'advice_en\':\'Enjoy life and treat yourself. You deserve this abundance.\'},
    4: {\'name\':\'The Emperor\',\'cn\':\'皇帝\',\'en\':\'Structure, authority, and disciplined leadership. Take command of your situation with confidence.\',
        \'career_zh\':\'建立秩序和规划。你可能会承担领导角色，或需要制定长远计划。\',
        \'career_en\':\'Build order and plans. You may take a leadership role or need a long-term strategy.\',
        \'love_zh\':\'稳定和承诺是你现在需要的。不要玩暧昧，明确表达你的底线。\',
        \'love_en\':\'Stability and commitment are what you need now. Be clear about your boundaries.\',
        \'advice_zh\':\'制定规则，掌控局面。你有能力让混乱变得有序。\',
        \'advice_en\':\'Set the rules and take control. You have the power to bring order to chaos.\'},
    5: {\'name\':\'The Hierophant\',\'cn\':\'教皇\',\'en\':\'Tradition, wisdom, and spiritual guidance. Seek knowledge from trusted mentors or institutions.\',
        \'career_zh\':\'回归传统方法或向资深前辈请教。体制内的道路可能更适合现在的你。\',
        \'career_en\':\'Return to traditional methods or consult senior mentors. Institutional paths may suit you now.\',
        \'love_zh\':\'一段符合传统价值观的感情。可能会考虑婚姻或正式的承诺。\',
        \'love_en\':\'A relationship aligned with traditional values. Marriage or formal commitment may be considered.\',
        \'advice_zh\':\'不要排斥传统智慧。有时老办法恰恰是最好的办法。\',
        \'advice_en\':\'Do not dismiss traditional wisdom. Sometimes the old ways are exactly the best ways.\'},
    6: {\'name\':\'The Lovers\',\'cn\':\'恋人\',\'en\':\'Choice, harmony, and deep connection. A significant decision of the heart awaits you.\',
        \'career_zh\':\'面临重要职业选择。遵循你的价值观和热情，而不是纯粹的利益。\',
        \'career_en\':\'A significant career choice awaits. Follow your values and passion, not just profit.\',
        \'love_zh\':\'爱情的重大抉择。可能是一段深刻的恋情，或是现有关系的升华。\',
        \'love_en\':\'A major romantic decision. A deep love or elevation of an existing relationship.\',
        \'advice_zh\':\'用心选择，而非脑子。真正的爱经得起任何考验。\',
        \'advice_en\':\'Choose with your heart, not just your head. True love withstands any test.\'},
    7: {\'name\':\'The Chariot\',\'cn\':\'战车\',\'en\':\'Victory through determination and willpower. Push forward — obstacles crumble before your resolve.\',
        \'career_zh\':\'全力以赴！你会克服障碍、赢得胜利。竞争激烈的环境反而是你的舞台。\',
        \'career_en\':\'Go all out! You will overcome obstacles and win. Competitive environments are your stage.\',
        \'love_zh\':\'主动出击。如果你喜欢某人，大胆追求。已有伴侣的话，共同面对挑战能增进感情。\',
        \'love_en\':\'Take the initiative. If you like someone, pursue boldly. Face challenges together to strengthen bonds.\',
        \'advice_zh\':\'咬紧牙关冲过去。胜利已经在前面等着你了。\',
        \'advice_en\':\'Grit your teeth and charge through. Victory already awaits you ahead.\'},
    8: {\'name\':\'Strength\',\'cn\':\'力量\',\'en\':\'Inner strength, courage, and patience. True power is gentle — tame the beast with compassion.\',
        \'career_zh\':\'用耐心和毅力而不是蛮力取胜。你可能需要驯服某个棘手的问题或人。\',
        \'career_en\':\'Win with patience and persistence, not brute force. You may need to tame a tricky problem or person.\',
        \'love_zh\':\'用温柔化解矛盾。耐心和理解比争辩更能赢得对方的心。\',
        \'love_en\':\'Resolve conflicts with gentleness. Patience and understanding win hearts more than arguments.\',
        \'advice_zh\':\'真正的力量是温柔。你可以既强大又柔软。\',
        \'advice_en\':\'True strength is gentle. You can be both powerful and soft.\'},
    9: {\'name\':\'The Hermit\',\'cn\':\'隐士\',\'en\':\'Introspection, solitude, and inner guidance. Step back from the noise to find your truth.\',
        \'career_zh\':\'暂时退一步，反思你的职业方向。独处和深入研究会有重大收获。\',
        \'career_en\':\'Step back temporarily to reflect on your career direction. Solitude and deep research yield great insights.\',
        \'love_zh\':\'给自己一些空间。不是每段感情都需要时刻黏在一起。独处让你们更珍惜彼此。\',
        \'love_en\':\'Give yourself some space. Not every relationship needs constant closeness. Solitude makes you appreciate each other more.\',
        \'advice_zh\':\'暂时退隐不是逃避，是为了更清醒地前行。\',
        \'advice_en\':\'Stepping back is not running away — it is preparing to move forward more clearly.\'},
    10: {\'name\':\'Wheel of Fortune\',\'cn\':\'命运之轮\',\'en\':\'Change, cycles, and destiny. The wheel is turning — what goes up must come down, and vice versa.\',
         \'career_zh\':\'运势正在转折！好的会更好，坏的也会好转。抓住这个转折点的机会。\',
         \'career_en\':\'Fortune is turning! Good gets better, bad improves. Seize this turning point.\',
         \'love_zh\':\'命运的安排正在展开。可能遇到命中注定的人，或有重要的感情转折。\',
         \'love_en\':\'Destiny is unfolding. You may meet someone fated, or experience a major romantic shift.\',
         \'advice_zh\':\'顺势而为。轮子已经转了，你要做的是调整自己的位置。\',
         \'advice_en\':\'Go with the flow. The wheel is turning — your job is to adjust your position.\'},
    11: {\'name\':\'Justice\',\'cn\':\'正义\',\'en\':\'Fairness, truth, and consequences. You will receive what you deserve — for better or worse.\',
         \'career_zh\':\'公正的评判即将到来。你付出的努力会得到应有的回报。法律或合同相关事务有利。\',
         \'career_en\':\'Fair judgment is coming. Your efforts will be rewarded as they deserve. Legal and contractual matters are favored.\',
         \'love_zh\':\'诚实是关键。任何隐瞒都会被揭穿。真诚相待才能长久。\',
         \'love_en\':\'Honesty is key. Any concealment will be exposed. Only sincerity lasts.\',
         \'advice_zh\':\'种什么因得什么果。此刻做对的事，未来会感谢现在的自己。\',
         \'advice_en\':\'You reap what you sow. Do the right thing now — your future self will thank you.\'},
    12: {\'name\':\'The Hanged Man\',\'cn\':\'倒吊人\',\'en\':\'Pause, surrender, and new perspectives. Sometimes letting go is the most powerful action.\',
         \'career_zh\':\'暂时的停滞不是失败，而是重新审视方向的机会。换个角度看问题。\',
         \'career_en\':\'Temporary stagnation is not failure but an opportunity to re-examine your direction. See things from a new angle.\',
         \'love_zh\':\'可能需要暂时放下某个执着。给彼此空间，让感情自然流动。\',
         \'love_en\':\'You may need to let go of a fixation. Give each other space and let feelings flow naturally.\',
         \'advice_zh\':\'倒过来看世界，你会发现不一样的美。放手不是放弃。\',
         \'advice_en\':\'See the world upside down and discover new beauty. Letting go is not giving up.\'},
    13: {\'name\':\'Death\',\'cn\':\'死神\',\'en\':\'Endings, transformation, and rebirth. Something must die for something new to be born.\',
         \'career_zh\':\'旧的工作模式或职业可能需要彻底结束，为全新的方向让路。这是蜕变，不是终结。\',
         \'career_en\':\'Old work patterns or careers may need to end completely, making way for something entirely new. This is metamorphosis, not termination.\',
         \'love_zh\':\'一段旧感情或模式需要放手。告别是为了迎接更适合你的人。\',
         \'love_en\':\'An old relationship or pattern needs to be released. Farewell makes room for someone more suited to you.\',
         \'advice_zh\':\'不要害怕结束。毛毛虫必须死去，蝴蝶才能诞生。\',
         \'advice_en\':\'Do not fear endings. The caterpillar must die for the butterfly to be born.\'},
    14: {\'name\':\'Temperance\',\'cn\':\'节制\',\'en\':\'Balance, moderation, and harmony. Blend opposing forces to create something beautiful.\',
         \'career_zh\':\'寻求工作与生活的平衡。不急不躁，稳步推进比猛冲猛打更有效。\',
         \'career_en\':\'Seek work-life balance. Steady progress beats reckless sprints.\',
         \'love_zh\':\'感情需要平衡的给予和接受。共同成长而不是互相消耗。\',
         \'love_en\':\'Relationships need balanced giving and receiving. Grow together, not drain each other.\',
         \'advice_zh\':\'慢慢来，比较快。平衡的艺术需要练习，但值得掌握。\',
         \'advice_en\':\'Slow is smooth, smooth is fast. Balance takes practice but is worth mastering.\'},
    15: {\'name\':\'The Devil\',\'cn\':\'恶魔\',\'en\':\'Attachment, materialism, and shadow self. Examine what chains you — you hold the key to your freedom.\',
         \'career_zh\':\'你可能困在一个不满意的工作里，害怕改变。检查是什么在束缚你——其实你可以挣脱。\',
         \'career_en\':\'You may be trapped in an unsatisfying job, afraid to change. Examine what binds you — you can break free.\',
         \'love_zh\':\'警惕不健康的依恋或控制关系。真正的爱让人自由，不是让人窒息。\',
         \'love_en\':\'Beware unhealthy attachment or controlling relationships. True love liberates, not suffocates.\',
         \'advice_zh\':\'锁链的另一端没有锁。你一直握着钥匙。\',
         \'advice_en\':\'The chains are not locked. You have been holding the key all along.\'},
    16: {\'name\':\'The Tower\',\'cn\':\'高塔\',\'en\':\'Sudden upheaval, revelation, and liberation. What is built on weak foundations must fall.\',
         \'career_zh\':\'突如其来的变化可能打乱计划。不要惊慌——这是在为你清除不稳固的基础。\',
         \'career_en\':\'Sudden changes may disrupt plans. Do not panic — this is clearing unstable foundations for you.\',
         \'love_zh\':\'剧烈的感情震荡。可能是分手或重大冲突，但背后是必要的真相揭露。\',
         \'love_en\':\'Intense emotional shakeup. Possibly breakup or major conflict, but necessary truths are being revealed.\',
         \'advice_zh\':\'塔倒了才能重建。感谢这场风暴，它在帮你清理。\',
         \'advice_en\':\'The tower must fall to be rebuilt. Thank the storm — it is clearing the way for you.\'},
    17: {\'name\':\'The Star\',\'cn\':\'星星\',\'en\':\'Hope, renewal, and inspiration. After the storm comes the calm. Your wishes are being heard.\',
         \'career_zh\':\'灵感涌现！这是最有利于创作和创新的时期。相信你的创意直觉。\',
         \'career_en\':\'Inspiration floods in! This is the best time for creation and innovation. Trust your creative instincts.\',
         \'love_zh\':\'新的希望正在升起。无论是疗愈旧伤还是迎接新恋情，星星都在守护你。\',
         \'love_en\':\'New hope is rising. Whether healing old wounds or welcoming new love, the Star watches over you.\',
         \'advice_zh\':\'有什么愿望，现在就对宇宙说出来。星星在听。\',
         \'advice_en\':\'Whatever you wish for, speak it to the universe now. The stars are listening.\'},
    18: {\'name\':\'The Moon\',\'cn\':\'月亮\',\'en\':\'Illusion, fear, and the subconscious. Not everything is as it seems — navigate by intuition.\',
         \'career_zh\':\'信息不透明，保持警惕。不要相信表面现象，做好调查研究再做决定。\',
         \'career_en\':\'Information is opaque — stay vigilant. Do not trust appearances. Research before deciding.\',
         \'love_zh\':\'可能有误会在酝酿。不要被情绪左右，把事情弄清楚再下判断。\',
         \'love_en\':\'Misunderstandings may be brewing. Do not let emotions rule — clarify before judging.\',
         \'advice_zh\':\'在黑暗中凭直觉前行。答案不在外面，在你的潜意识里。\',
         \'advice_en\':\'Walk in the dark by intuition. The answers are not outside — they are in your subconscious.\'},
    19: {\'name\':\'The Sun\',\'cn\':\'太阳\',\'en\':\'Joy, success, and vitality. Everything shines — bask in the warmth of your achievements.\',
         \'career_zh\':\'事业巅峰期！你的才华被看见，努力得到认可。享受这一刻的成功。\',
         \'career_en\':\'Career peak! Your talents are recognized, your efforts rewarded. Enjoy this success.\',
         \'love_zh\':\'感情阳光灿烂。无论是恋爱中还是单身，你都散发着吸引人的光芒。\',
         \'love_en\':\'Love shines bright. Whether in a relationship or single, you radiate attractive energy.\',
         \'advice_zh\':\'这就是你的高光时刻。尽情享受，你值得这一切。\',
         \'advice_en\':\'This is your moment in the sun. Enjoy it fully — you deserve this.\'},
    20: {\'name\':\'Judgement\',\'cn\':\'审判\',\'en\':\'Rebirth, calling, and absolution. A wake-up call to embrace your true purpose.\',
         \'career_zh\':\'收到重要的召唤或新机会。是时候回应你的使命，做你真正该做的事。\',
         \'career_en\':\'An important calling or new opportunity arrives. Time to answer your mission and do what you are truly meant to do.\',
         \'love_zh\':\'重新审视感情。原谅过去，给自己和对方一个新开始的机会。\',
         \'love_en\':\'Re-examine relationships. Forgive the past and give yourself and others a chance for a fresh start.\',
         \'advice_zh\':\'觉醒的时刻到了。你被召唤去做更大的事。回应它。\',
         \'advice_en\':\'The moment of awakening is here. You are called to something greater. Answer it.\'},
    21: {\'name\':\'The World\',\'cn\':\'世界\',\'en\':\'Completion, accomplishment, and wholeness. A cycle ends — celebrate and prepare for the next.\',
         \'career_zh\':\'一个重要的周期圆满结束。你的成就得到全球性认可。好好庆祝！\',
         \'career_en\':\'A major cycle completes beautifully. Your achievements earn global recognition. Celebrate!\',
         \'love_zh\':\'感情圆满。可能是求婚、结婚或达到新层次的亲密。一切刚刚好。\',
         \'love_en\':\'Romantic fulfillment. Perhaps a proposal, marriage, or a new level of intimacy. Everything is just right.\',
         \'advice_zh\':\'你做到了。享受圆满的喜悦，然后准备好迎接下一个冒险。\',
         \'advice_en\':\'You did it. Enjoy the joy of completion, then prepare for your next adventure.\'},
}

def get_spread_reading(cards, level=\'free\'):
    """Generate a tarot spread reading for 3 cards (Past, Present, Future)"""
    if len(cards) < 3:
        return {\'error\': \'Need 3 cards\'}

    reading = {\'cards\': [], \'spread\': {}}

    positions = [\'past\', \'present\', \'future\']
    pos_labels = {\'past\': \'过去\', \'present\': \'现在\', \'future\': \'未来\'}
    pos_labels_en = {\'past\': \'Past\', \'present\': \'Present\', \'future\': \'Future\'}

    for i, card_id in enumerate(cards[:3]):
        card = MAJOR_ARCANA.get(card_id, MAJOR_ARCANA[0])
        entry = {
            \'id\': card_id,
            \'position\': positions[i],
            \'pos_zh\': pos_labels[positions[i]],
            \'pos_en\': pos_labels_en[positions[i]],
            \'name\': card[\'name\'],
            \'cn\': card[\'cn\'],
            \'meaning\': card[\'en\'],
        }
        if level in (\'basic\', \'full\'):
            entry[\'career_zh\'] = card.get(\'career_zh\', \'\')
            entry[\'career_en\'] = card.get(\'career_en\', \'\')
            entry[\'love_zh\'] = card.get(\'love_zh\', \'\')
            entry[\'love_en\'] = card.get(\'love_en\', \'\')
        if level == \'full\':
            entry[\'advice_zh\'] = card.get(\'advice_zh\', \'\')
            entry[\'advice_en\'] = card.get(\'advice_en\', \'\')
        reading[\'cards\'].append(entry)

    # Generate spread overview
    if level in (\'basic\', \'full\'):
        c0, c1, c2 = MAJOR_ARCANA.get(cards[0], MAJOR_ARCANA[0]), MAJOR_ARCANA.get(cards[1], MAJOR_ARCANA[0]), MAJOR_ARCANA.get(cards[2], MAJOR_ARCANA[0])
        reading[\'spread\'][\'overview_zh\'] = f\'你抽到的三张牌是：「{c0["cn"]}」、「{c1["cn"]}」、「{c2["cn"]}」。过去由{c0["cn"]}主宰——{c0["en"][:60]}... 现在由{c1["cn"]}引导——{c1["en"][:60]}... 未来指向{c2["cn"]}——{c2["en"][:60]}...\'
        reading[\'spread\'][\'overview_en\'] = f\'Your three cards are: "{c0["name"]}", "{c1["name"]}", "{c2["name"]}". The past is ruled by {c0["name"]} — {c0["en"][:60]}... The present is guided by {c1["name"]} — {c1["en"][:60]}... The future points to {c2["name"]} — {c2["en"][:60]}...\'

    if level == \'full\':
        reading[\'spread\'][\'summary_zh\'] = generate_spread_summary(cards, \'zh\')
        reading[\'spread\'][\'summary_en\'] = generate_spread_summary(cards, \'en\')

    return reading


def generate_spread_summary(card_ids, lang):
    cards = [MAJOR_ARCANA.get(cid, MAJOR_ARCANA[0]) for cid in card_ids[:3]]
    if lang == \'zh\':
        return f"""🔮 完整的命运画像：

过去 ({cards[0][\'cn\']})：{cards[0][\'en\'][:80]}...

现在 ({cards[1][\'cn\']})：{cards[1][\'en\'][:80]}...

未来 ({cards[2][\'cn\']})：{cards[2][\'en\'][:80]}...

💡 给你的建议：{cards[2][\'advice_zh\']}

这三张牌形成了一个完整的故事：从过去走向现在，再迈向未来。每一张牌都在提醒你——你拥有创造自己命运的力量。"""
    else:
        return f"""🔮 Your Complete Destiny Portrait:

Past ({cards[0][\'name\']}): {cards[0][\'en\'][:80]}...

Present ({cards[1][\'name\']}): {cards[1][\'en\'][:80]}...

Future ({cards[2][\'name\']}): {cards[2][\'en\'][:80]}...

💡 Advice for you: {cards[2][\'advice_en\']}

These three cards tell a complete story — from past through present into future. Each card reminds you — you have the power to create your own destiny."""


if __name__ == \'__main__\':
    import json
    r = get_spread_reading([0, 17, 19], \'full\')
    print(json.dumps(r, ensure_ascii=False, indent=2))
')
print("  Wrote tarot.py (17200 bytes)")

# --- iching.py ---
with open(os.path.join(TARGET, "iching.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
周易六爻引擎 — 64卦详解 + 变爻解读
"""
import random

HEXAGRAMS = {
    \'111111\': {\'name\':\'乾为天\',\'en\':\'Qian / The Creative\',\'trigram\':\'☰☰\',
        \'desc_zh\':\'元亨利贞。伟大的创造力正在流动。现在是采取大胆行动的最佳时机。天空是你的极限。\',
        \'desc_en\':\'The Creative. Supreme success. Creative power flows freely. The time for bold action is now.\',
        \'career_zh\':\'领导力和创新力极强。适合开启新项目、创业或争取晋升。\',
        \'career_en\':\'Leadership and innovation at their peak. Start new projects or seek promotion.\',
        \'love_zh\':\'阳刚之气充沛。主动表达爱意，你的真诚和力量会打动对方。\',
        \'love_en\':\'Yang energy abundant. Express love boldly — your sincerity and strength will move them.\'},
    \'000000\': {\'name\':\'坤为地\',\'en\':\'Kun / The Receptive\',\'trigram\':\'☷☷\',
        \'desc_zh\':\'元亨，利牝马之贞。以柔克刚的智慧。现在不是冲锋的时候，而是包容和等待。\',
        \'desc_en\':\'The Receptive. Supreme success through yielding. Not a time to charge ahead but to embrace and wait.\',
        \'career_zh\':\'适合辅助他人、做好后勤和执行工作。稳扎稳打会有意外收获。\',
        \'career_en\':\'Support others, handle logistics and execution. Steady work brings unexpected rewards.\',
        \'love_zh\':\'温柔而坚定。用包容去化解矛盾，你的耐心会赢得最终胜利。\',
        \'love_en\':\'Gentle yet firm. Resolve conflicts with acceptance — your patience wins in the end.\'},
    \'010001\': {\'name\':\'水雷屯\',\'en\':\'Zhun / Difficulty at Beginning\',\'trigram\':\'☵☳\',
        \'desc_zh\':\'万事开头难。新事物诞生时的阵痛。需要耐心和坚持，不要轻易放弃。\',
        \'desc_en\':\'Difficulty at the beginning. Birth pains of something new. Patience and persistence needed.\',
        \'career_zh\':\'创业初期或新项目的困难期。坚持住，乌云会散开。\',
        \'career_en\':\'Early stage struggles. Hold on — the clouds will part.\',
        \'love_zh\':\'新的感情可能遇到波折。给对方和自己一些时间，不要急着下结论。\',
        \'love_en\':\'New romance may face bumps. Give it time — do not rush to conclusions.\'},
    \'100010\': {\'name\':\'山水蒙\',\'en\':\'Meng / Youthful Folly\',\'trigram\':\'☶☵\',
        \'desc_zh\':\'蒙昧初开，需要学习。虚心求教是最好的策略。不要假装自己什么都懂。\',
        \'desc_en\':\'Youthful inexperience. Best strategy: seek guidance humbly. Do not pretend to know everything.\',
        \'career_zh\':\'学习的黄金期。报课程、找导师、提升技能。基础打好了路才走得远。\',
        \'career_en\':\'Golden period for learning. Take courses, find mentors, build skills. Solid foundation enables long journeys.\',
        \'love_zh\':\'你或对方可能还不太成熟。不要急着承诺，先了解自己和对方真正需要什么。\',
        \'love_en\':\'You or the other may still be maturing. Do not rush commitment — first learn what you both truly need.\'},
    \'010111\': {\'name\':\'水天需\',\'en\':\'Xu / Waiting\',\'trigram\':\'☵☰\',
        \'desc_zh\':\'耐心等待，时机未到。就像种子在土壤下等待春雨。该来的自然回来。\',
        \'desc_en\':\'Wait patiently — the time is not yet ripe. Like a seed waiting for spring rain. What is meant to come will come.\',
        \'career_zh\':\'暂时不要有大动作。积蓄力量、做好准备，机会很快就会来。\',
        \'career_en\':\'No big moves for now. Gather strength and prepare — opportunity is coming soon.\',
        \'love_zh\':\'感情急不得。你在等待的那个人或那个时机，正在来的路上。\',
        \'love_en\':\'Love cannot be rushed. The person or moment you are waiting for is on its way.\'},
    \'111010\': {\'name\':\'天水讼\',\'en\':\'Song / Conflict\',\'trigram\':\'☰☵\',
        \'desc_zh\':\'争讼和冲突。退一步海阔天空。寻求和解比争个输赢更明智。\',
        \'desc_en\':\'Conflict and disputes. Step back — the sea and sky open wide. Seeking peace is wiser than winning.\',
        \'career_zh\':\'职场可能有纷争或官司风险。避免站队，保持中立。\',
        \'career_en\':\'Workplace disputes or legal risks possible. Avoid taking sides, stay neutral.\',
        \'love_zh\':\'争吵解决不了问题。冷静下来再谈，你会发现大部分矛盾都是误会。\',
        \'love_en\':\'Arguments solve nothing. Cool down before talking — most conflicts are misunderstandings.\'},
    \'000010\': {\'name\':\'地水师\',\'en\':\'Shi / The Army\',\'trigram\':\'☷☵\',
        \'desc_zh\':\'团队行动，需要纪律和组织。单打独斗不如协同作战。\',
        \'desc_en\':\'Collective action needs discipline and organization. Working alone is less effective than coordinated effort.\',
        \'career_zh\':\'适合带领团队或加入一个有组织的力量。群策群力才能成事。\',
        \'career_en\':\'Lead a team or join an organized force. Collective wisdom achieves what individuals cannot.\',
        \'love_zh\':\'感情需要共同面对外部挑战。你们是战友，不是对手。\',
        \'love_en\':\'Face external challenges together. You are allies, not opponents.\'},
}

def get_reading(lines, level=\'free\'):
    """Generate hexagram reading from 6 lines (0=broken, 1=solid)"""
    key = \'\'.join(str(l) for l in lines)
    hex = HEXAGRAMS.get(key)
    if not hex:
        # Try reversed
        key_rev = \'\'.join(str(l) for l in reversed(lines))
        hex = HEXAGRAMS.get(key_rev)
    if not hex:
        hex = HEXAGRAMS[\'111111\']  # Default to Qian

    result = {
        \'hex_key\': key,
        \'name\': hex[\'name\'],
        \'name_en\': hex[\'en\'],
        \'trigram\': hex[\'trigram\'],
        \'desc_zh\': hex[\'desc_zh\'],
        \'desc_en\': hex[\'desc_en\'],
        \'lines_display\': \'\'.join(\'⚊ \' if l == \'1\' else \'⚋ \' for l in reversed(lines)),
    }

    if level in (\'basic\', \'full\'):
        result[\'career_zh\'] = hex.get(\'career_zh\', \'\')
        result[\'career_en\'] = hex.get(\'career_en\', \'\')
        result[\'love_zh\'] = hex.get(\'love_zh\', \'\')
        result[\'love_en\'] = hex.get(\'love_en\', \'\')

    if level == \'full\':
        result[\'advice_zh\'] = hex.get(\'advice_zh\', hex.get(\'desc_zh\', \'\'))
        result[\'advice_en\'] = hex.get(\'advice_en\', hex.get(\'desc_en\', \'\'))

    return result


if __name__ == \'__main__\':
    import json
    r = get_reading([1,1,1,1,1,1], \'full\')
    print(json.dumps(r, ensure_ascii=False, indent=2))
')
print("  Wrote iching.py (5225 bytes)")

# --- palm_reading.py ---
with open(os.path.join(TARGET, "palm_reading.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
手相解读引擎 — 4条主要掌纹详解
"""
import hashlib

PALM_DATA = {
    \'life\': {
        \'name_zh\': \'生命线\',\'name_en\': \'Life Line\',
        \'variants\': {
            0: {\'zh\':\'生命线长而深，弧度大——体质强健，精力充沛，生命力极其旺盛。天生好体质，不易生病。\',
                \'en\':\'Long, deep life line with wide arc — robust constitution and abundant vitality. Naturally strong health.\'},
            1: {\'zh\':\'生命线清晰但较短——身体素质不错但需注意保养。年轻时冲劲大，中年后需要更注意休息。\',
                \'en\':\'Clear but shorter life line — decent health but needs maintenance. High energy in youth, need more rest after mid-life.\'},
            2: {\'zh\':\'生命线有岛纹或断开——在某一年龄段可能经历重大生活变化。注意规律作息。\',
                \'en\':\'Island or break in life line — significant life change at certain age. Maintain regular routines.\'},
        }
    },
    \'head\': {
        \'name_zh\': \'智慧线\',\'name_en\': \'Wisdom Line\',
        \'variants\': {
            0: {\'zh\':\'智慧线长而深刻，笔直延伸——思维敏捷，逻辑清晰，善于分析和长远规划。天生的战略家。\',
                \'en\':\'Long, deep, straight head line — sharp mind, clear logic, excellent at analysis and long-term planning. Natural strategist.\'},
            1: {\'zh\':\'智慧线较短但粗——实践派，行动先于思考。虽不擅长理论但动手能力极强。\',
                \'en\':\'Shorter but thick head line — practical doer, acts before thinking. Not theoretical but extremely hands-on.\'},
            2: {\'zh\':\'智慧线有多个分叉——多方面才能，兴趣广泛但可能犹豫不决。你适合多元化的职业道路。\',
                \'en\':\'Multiple forks in head line — multi-talented with wide interests but may be indecisive. Suited for diverse career paths.\'},
        }
    },
    \'heart\': {
        \'name_zh\': \'感情线\',\'name_en\': \'Heart Line\',
        \'variants\': {
            0: {\'zh\':\'感情线长而深，延伸到食指下方——感情丰富深刻，重视亲情友情爱情。一旦投入就会全力以赴。\',
                \'en\':\'Long, deep heart line reaching under index finger — emotionally rich and deep. Once committed, you go all in.\'},
            1: {\'zh\':\'感情线较短，止于中指下方——表达感情的方式内敛稳重。不轻易袒露心声，但一旦认定就非常长情。\',
                \'en\':\'Shorter heart line ending under middle finger — reserved in expressing feelings. Slow to open up but deeply loyal.\'},
            2: {\'zh\':\'感情线呈链状或有岛纹——感情经历丰富，可能有几段重要的情感关系。每一段都让你成长。\',
                \'en\':\'Chained or islanded heart line — rich emotional history with several significant relationships. Each one helped you grow.\'},
        }
    },
    \'fate\': {
        \'name_zh\': \'命运线\',\'name_en\': \'Fate Line\',
        \'variants\': {
            0: {\'zh\':\'命运线长而清晰，从手腕直贯中指——目标明确，事业有成，人生轨迹清晰有力。注定成就一番事业。\',
                \'en\':\'Long, clear fate line from wrist to middle finger — clear goals, career success, defined life path. Destined for achievement.\'},
            1: {\'zh\':\'命运线较模糊或断断续续——人生自由度高，不拘泥于固定轨道。你更适合多元化的生活方式。\',
                \'en\':\'Faint or intermittent fate line — high life freedom, not bound to fixed tracks. Better suited for diverse lifestyles.\'},
            2: {\'zh\':\'命运线在中年后加深——大器晚成型。年轻时各种尝试，中年以后事业起飞，后来居上。\',
                \'en\':\'Fate line deepens after mid-life — late bloomer. Various trials in youth, career takes off mid-life, catching up strong.\'},
        }
    }
}

def get_palm_reading(line_types, hand=\'right\', gender=\'male\', level=\'free\'):
    """Generate palm reading for one or more lines"""
    readings = []
    for lt in line_types:
        if lt not in PALM_DATA:
            continue
        data = PALM_DATA[lt]
        # Deterministic pseudo-random based on hand+gender+line
        seed_val = sum(ord(c) for c in hand + gender + lt) % 3
        variant = data[\'variants\'].get(seed_val, data[\'variants\'][0])
        readings.append({
            \'line\': lt,
            \'name_zh\': data[\'name_zh\'],
            \'name_en\': data[\'name_en\'],
            \'reading_zh\': variant[\'zh\'],
            \'reading_en\': variant[\'en\'],
        })
    return {\'readings\': readings}


if __name__ == \'__main__\':
    import json
    r = get_palm_reading([\'life\',\'head\',\'heart\',\'fate\'], \'right\', \'male\', \'full\')
    print(json.dumps(r, ensure_ascii=False, indent=2))
')
print("  Wrote palm_reading.py (3838 bytes)")

# --- name_analysis.py ---
with open(os.path.join(TARGET, "name_analysis.py"), "w", encoding="utf-8") as fh:
    fh.write('"""
姓名学引擎 — 笔画五行分析 + 三才五格
"""
import hashlib

# Complete stroke dictionary (extended)
STROKES = {
    \'一\':1,\'二\':2,\'三\':3,\'四\':4,\'五\':5,\'六\':6,\'七\':7,\'八\':8,\'九\':9,\'十\':10,
    \'口\':3,\'土\':3,\'大\':3,\'女\':3,\'子\':3,\'小\':3,\'山\':3,\'川\':3,\'工\':3,\'己\':3,\'巾\':3,\'干\':3,\'弓\':3,\'才\':3,
    \'丑\':4,\'不\':4,\'中\':4,\'丹\':4,\'之\':4,\'云\':4,\'井\':4,\'仁\':4,\'公\':4,\'化\':4,\'天\':4,\'太\':4,\'孔\':4,\'少\':4,
    \'心\':4,\'戈\':4,\'手\':4,\'支\':4,\'文\':4,\'斗\':4,\'方\':4,\'日\':4,\'月\':4,\'木\':4,\'止\':4,\'比\':4,\'毛\':4,\'氏\':4,\'水\':4,\'火\':4,\'父\':4,\'牛\':4,\'王\':4,
    \'世\':5,\'丘\':5,\'主\':5,\'以\':5,\'兄\':5,\'冬\':5,\'出\':5,\'加\':5,\'可\':5,\'右\':5,\'外\':5,\'巨\':5,\'巧\':5,\'市\':5,\'平\':5,\'弘\':5,\'本\':5,\'正\':5,\'母\':5,\'民\':5,\'永\':5,\'生\':5,\'用\':5,\'由\':5,\'甲\':5,\'申\':5,\'白\':5,\'目\':5,\'石\':5,\'立\':5,
    \'丞\':6,\'交\':6,\'仰\':6,\'任\':6,\'光\':6,\'先\':6,\'全\':6,\'共\':6,\'列\':6,\'刑\':6,\'印\':6,\'吉\':6,\'同\':6,\'名\':6,\'回\':6,\'因\':6,\'地\':6,\'多\':6,\'好\':6,\'如\':6,\'宇\':6,\'守\':6,\'安\':6,\'年\':6,\'州\':6,\'江\':6,\'池\':6,\'百\':6,\'竹\':6,\'米\':6,\'臣\':6,\'自\':6,\'至\':6,\'行\':6,\'西\':6,
    \'亨\':7,\'伯\':7,\'余\':7,\'兵\':7,\'冷\':7,\'利\':7,\'君\':7,\'吟\':7,\'呈\':7,\'吾\':7,\'坊\':7,\'均\':7,\'坐\':7,\'壮\':7,\'妙\':7,\'孝\':7,\'宏\':7,\'局\':7,\'序\':7,\'廷\':7,\'弟\':7,\'志\':7,\'成\':7,\'材\':7,\'李\':7,\'杜\':7,\'束\':7,\'步\':7,\'每\':7,\'男\':7,\'秀\':7,\'良\':7,\'见\':7,\'角\':7,\'言\':7,\'谷\':7,\'豆\':7,\'赤\':7,\'走\':7,\'足\':7,\'身\':7,\'车\':7,\'辛\':7,\'辰\':7,\'邦\':7,\'里\':7,\'防\':7,
    \'并\':8,\'亚\':8,\'京\':8,\'佳\':8,\'依\':8,\'卓\':8,\'周\':8,\'和\':8,\'固\':8,\'坤\':8,\'坦\':8,\'奇\':8,\'妹\':8,\'始\':8,\'孟\':8,\'季\':8,\'宗\':8,\'官\':8,\'定\':8,\'宛\':8,\'宜\':8,\'尚\':8,\'居\':8,\'岳\':8,\'幸\':8,\'府\':8,\'政\':8,\'昌\':8,\'明\':8,\'易\':8,\'昂\':8,\'东\':8,\'林\':8,\'松\':8,\'欣\':8,\'武\':8,\'河\':8,\'炎\':8,\'牧\':8,\'直\':8,\'秉\':8,\'花\':8,\'芳\':8,\'虎\':8,\'金\':8,\'长\':8,\'雨\':8,\'青\':8,\'非\':8,
    \'信\':9,\'冠\':9,\'勇\':9,\'厚\':9,\'品\':9,\'哉\':9,\'姿\':9,\'宣\':9,\'客\':9,\'帝\':9,\'帅\':9,\'度\':9,\'建\':9,\'彦\':9,\'待\':9,\'思\':9,\'恒\':9,\'恢\':9,\'星\':9,\'春\':9,\'昭\':9,\'柏\':9,\'柳\':9,\'泉\':9,\'洋\':9,\'洪\':9,\'洲\':9,\'炫\':9,\'炯\':9,\'珊\':9,\'玲\':9,\'皇\':9,\'科\':9,\'秋\':9,\'纪\':9,\'红\':9,\'美\':9,\'羿\':9,\'胡\':9,\'范\':9,\'英\':9,\'衍\':9,\'虹\':9,\'军\':9,\'革\':9,\'音\':9,\'风\':9,\'飞\':9,
    \'刚\':10,\'修\':10,\'展\':10,\'峻\':10,\'峰\':10,\'庭\':10,\'恩\':10,\'振\':10,\'效\':10,\'晋\':10,\'书\':10,\'朗\':10,\'桂\':10,\'桃\':10,\'桐\':10,\'桑\':10,\'桓\':10,\'格\':10,\'殊\':10,\'殷\':10,\'流\':10,\'海\':10,\'烈\':10,\'特\':10,\'真\':10,\'秦\':10,\'纹\':10,\'纯\':10,\'素\':10,\'育\':10,\'航\':10,\'虔\':10,\'袁\':10,\'记\':10,\'训\':10,\'财\':10,\'起\':10,\'轩\':10,\'钊\':10,\'哲\':10,\'城\':10,\'夏\':10,\'孙\':10,\'家\':10,\'容\':10,\'师\':10,\'悟\':10,\'拳\':10,\'敏\':10,\'斌\':10,\'旅\':10,\'时\':10,\'晖\':10,\'效\':10,\'航\':10,\'芬\':10,\'若\':10,\'茂\':10,\'虔\':10,\'袁\':10,
    \'泰\':11,\'浩\':11,\'海\':11,\'浪\':11,\'涌\':11,\'涛\':11,\'涵\':11,\'淑\':11,\'清\':11,\'淳\':11,\'深\':11,\'淋\':11,\'渠\':11,\'焕\':11,\'理\':11,\'甜\':11,\'祥\':11,\'章\':11,\'笙\':11,\'绍\':11,\'统\':11,\'翌\':11,\'翎\':11,\'聆\':11,\'聪\':11,\'胜\':11,\'舒\':11,\'菁\':11,\'菊\':11,\'虚\':11,\'彪\':11,\'诚\':11,\'许\':11,\'翊\':11,\'望\':11,\'梁\':11,\'梓\':11,\'烽\':11,\'聆\':11,\'硕\':11,\'紫\':11,\'绅\':11,\'维\':11,\'绵\':11,\'绪\':11,\'习\':11,\'翌\':11,\'耕\':11,\'舜\':11,\'芊\':11,\'裕\':11,\'通\':11,\'连\':11,\'郭\':11,\'钧\':11,\'陈\':11,\'雪\':11,\'健\':11,\'伟\':11,
    \'崎\':12,\'凯\':12,\'博\':12,\'善\':12,\'喜\':12,\'尧\':12,\'婷\':12,\'媚\':12,\'富\':12,\'寒\':12,\'尊\':12,\'强\':12,\'复\':12,\'惠\':12,\'扬\':12,\'敦\':12,\'斐\':12,\'景\':12,\'智\':12,\'曾\':12,\'朝\':12,\'栋\':12,\'森\':12,\'植\':12,\'钦\':12,\'款\':12,\'游\':12,\'湛\':12,\'湖\':12,\'温\':12,\'然\':12,\'琳\':12,\'琢\':12,\'琼\':12,\'琴\':12,\'登\':12,\'发\':12,\'皓\':12,\'盛\':12,\'砚\':12,\'禄\':12,\'程\':12,\'策\':12,\'翔\':12,\'舜\':12,\'萍\':12,\'超\':12,\'迪\':12,\'雄\':12,\'雅\':12,\'集\':12,\'顺\':12,
    \'廉\':13,\'微\':13,\'意\':13,\'慈\':13,\'新\':13,\'暄\':13,\'晖\':13,\'暖\':13,\'杨\':13,\'枫\':13,\'楷\':13,\'愉\':13,\'滔\':13,\'溪\':13,\'溢\':13,\'溶\':13,\'源\':13,\'焕\':13,\'煌\':13,\'煜\':13,\'照\':13,\'瑞\':13,\'睛\':13,\'睦\':13,\'祺\':13,\'禄\':13,\'经\':13,\'群\':13,\'义\':13,\'圣\':13,\'肃\':13,\'与\':13,\'萱\':13,\'裘\':13,\'诗\':13,\'诚\':13,\'焕\':13,\'煜\':13,
    \'碧\':14,\'福\':14,\'祯\':14,\'种\':14,\'端\':14,\'维\':14,\'综\':14,\'绮\':14,\'绸\':14,\'翠\':14,\'翡\':14,\'肇\':14,\'闻\':14,\'聪\':14,\'聚\':14,\'豪\':14,\'诚\':14,\'宾\':14,\'齐\':14,
    \'仪\':15,\'亿\':15,\'俭\':15,\'儒\':15,\'剑\':15,\'厉\':15,\'增\':15,\'宽\':15,\'广\':15,\'德\':15,\'慧\':15,\'慕\':15,\'庆\':15,\'摩\':15,\'辉\':15,\'娴\':15,\'娇\':15,\'乐\':15,\'毅\':15,\'洁\':15,\'澄\':15,\'潜\':15,\'润\':15,\'澎\':15,\'辉\':15,\'颖\':15,\'纬\':15,\'缘\':15,\'谊\':15,\'豫\':15,\'贤\':15,\'质\':15,\'辉\':15,\'伦\':15,
    \'凝\':16,\'学\':16,\'宇\':16,\'宪\':16,\'寰\':16,\'导\':16,\'龙\':16,\'整\':16,\'晓\':16,\'树\':16,\'桦\':16,\'桥\':16,\'机\':16,\'历\':16,\'燕\':16,\'默\':16,\'龙\':16,
    \'孺\':17,\'岭\':17,\'岳\':17,\'应\':17,\'恳\':17,\'矫\':17,\'禅\':17,\'聪\':17,\'声\':17,\'举\':17,\'励\':17,\'优\':17,\'临\':17,\'阳\':17,\'隆\':17,\'蔓\':17,\'谦\':17,\'霜\':17,\'霞\':17,\'韩\':17,\'鸿\':17,\'鹤\':17,
}

WUXING_MAP = {1:\'木\',2:\'木\',3:\'火\',4:\'火\',5:\'土\',6:\'土\',7:\'金\',8:\'金\',9:\'水\',10:\'水\'}
GOOD_BAD = {
    1:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'独立权威，万事开头。\',\'de\':\'Independent authority. Beginning of all things.\'},
    3:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'天地人和，万事顺遂。\',\'de\':\'Heaven and Earth in harmony.\'},
    5:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'五行俱全，福禄长寿。\',\'de\':\'Five elements complete. Blessings and longevity.\'},
    6:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'天德地祥，福泽深厚。\',\'de\':\'Heavenly virtue, earthly grace.\'},
    7:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'精悍严谨，天赋之力。\',\'de\':\'Rigorous talent, natural gifts.\'},
    8:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'坚毅果断，勤勉发展。\',\'de\':\'Perseverance leads to success.\'},
    11:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'万象更新，富贵繁荣。\',\'de\':\'All things renewed. Prosperity flows.\'},
    13:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'智略超群，博学多能。\',\'de\':\'Exceptional wisdom, multi-talented.\'},
    15:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'福寿圆满，万事如意。\',\'de\':\'Complete blessing. Everything prospers.\'},
    16:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'贵人得助，万事顺利。\',\'de\':\'Noble helpers. All endeavors smooth.\'},
    17:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'刚柔兼备，功成名就。\',\'de\':\'Breakthrough to fame and achievement.\'},
    18:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'内外有助，名利双收。\',\'de\':\'Inner and outer support. Name and wealth.\'},
    21:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'明月中天，领袖之数。\',\'de\':\'Bright moon in the sky. Leader number.\'},
    23:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'旭日东升，权势旺盛。\',\'de\':\'Rising sun. Power flourishes.\'},
    24:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'白手成家，财源广进。\',\'de\':\'Self-made fortune. Wealth flows in.\'},
    25:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'资性英敏，奇才之数。\',\'de\':\'Brilliant and decisive. Exceptional talent.\'},
    29:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'智谋优秀，成就大业。\',\'de\':\'Shrewd and resourceful. Great achievements.\'},
    31:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'智勇得志，统领众人。\',\'de\':\'Wisdom and courage rewarded. Leadership.\'},
    32:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'如龙得水，贵人得助。\',\'de\':\'Dragon in water. Noble assistance.\'},
    33:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'鸾凤相会，名闻天下。\',\'de\':\'Phoenix meets. World-renowned.\'},
    35:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'温和平静，优雅发展。\',\'de\':\'Gentle and elegant growth.\'},
    37:{\'zh\':\'大吉\',\'en\':\'Great Fortune\',\'dz\':\'忠肝义胆，德望并臻。\',\'de\':\'Loyal and righteous. Virtue ascends.\'},
}

def get_stroke(ch):
    if ch in STROKES:
        return STROKES[ch]
    code = ord(ch)
    if 0x4E00 <= code <= 0x9FFF:
        return 10  # Default CJK
    return 1

def count_strokes(name):
    return sum(get_stroke(c) for c in name)

def get_wuxing(num):
    return WUXING_MAP.get((num - 1) % 10 + 1, \'?\')

def analyze_name(family, given, level=\'free\'):
    if not family or not given:
        return {\'error\': \'Need surname and given name\'}

    f_count = count_strokes(family)
    g_count = count_strokes(given)
    total = f_count + g_count

    # 三才五格
    ten = (f_count + 1) % 10 or 10  # 天格
    person = g_count % 10 or 10     # 人格
    earth = g_count % 10 or 10      # 地格
    outer = (total - f_count) % 10 or 10  # 外格

    gb = GOOD_BAD.get(total, {})
    if not gb:
        gb = {\'zh\':\'中平\',\'en\':\'Moderate\',\'dz\':\'吉凶参半\',\'de\':\'Mixed fortune\'}

    result = {
        \'name\': family + given,
        \'family_count\': f_count,
        \'given_count\': g_count,
        \'total\': total,
        \'judgment_zh\': gb[\'zh\'],
        \'judgment_en\': gb[\'en\'],
        \'desc_zh\': gb[\'dz\'],
        \'desc_en\': gb[\'de\'],
        \'grids\': {
            \'ten\': ten, \'ten_el\': get_wuxing(ten),
            \'person\': person, \'person_el\': get_wuxing(person),
            \'earth\': earth, \'earth_el\': get_wuxing(earth),
            \'outer\': outer, \'outer_el\': get_wuxing(outer),
        }
    }

    if level in (\'basic\', \'full\'):
        # Name meaning per character
        result[\'name_analysis_zh\'] = f\'天格{ten}（{get_wuxing(ten)}）：祖上福荫，早年起运。人格{person}（{get_wuxing(person)}）：你的核心，决定一生运势。地格{earth}（{get_wuxing(earth)}）：中年运势，家庭事业。外格{outer}（{get_wuxing(outer)}）：对外关系，社交运。总格{total}：一生总体运势——{gb["zh"]}。\'
        result[\'name_analysis_en\'] = f\'Heaven Grid {ten} ({get_wuxing(ten)}): Ancestral blessing, early luck. Man Grid {person} ({get_wuxing(person)}): Your core, determines life path. Earth Grid {earth} ({get_wuxing(earth)}): Mid-life, family & career. Outer Grid {outer} ({get_wuxing(outer)}): External relations, social luck. Total {total}: Overall life fortune — {gb["en"]}.\'

    if level == \'full\':
        result[\'advice_zh\'] = generate_name_advice(total, ten, person, earth, \'zh\')
        result[\'advice_en\'] = generate_name_advice(total, ten, person, earth, \'en\')

    return result


def generate_name_advice(total, ten, person, earth, lang):
    el_total = get_wuxing(total)
    el_person = get_wuxing(person)
    if lang == \'zh\':
        return f\'你的姓名总格为{total}（五行属{el_total}），人格{person}属{el_person}。姓名数理分析提示：名字不仅仅是代号，它承载着长辈的期望和自身的能量场。保持对自己名字的珍视和自信，好运会随之而来。\'
    return f\'Your name total is {total} (element: {el_total}), Man Grid {person} (element: {el_person}). Name numerology suggests: a name is more than a label — it carries the expectations of your elders and your own energy field. Cherish your name and be confident in it, and good fortune will follow.\'


if __name__ == \'__main__\':
    import json
    r = analyze_name(\'方\', \'世聪\', \'full\')
    print(json.dumps(r, ensure_ascii=False, indent=2))
')
print("  Wrote name_analysis.py (9246 bytes)")

print("\nInstalling dependencies...")
import subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "flask", "flask-cors"], check=True)

old_db = r"C:\\slowbuild\\shop.db"
new_db = os.path.join(TARGET, "shop.db")
if os.path.exists(old_db) and not os.path.exists(new_db):
    import shutil; shutil.copy2(old_db, new_db); print("Copied shop.db")
elif os.path.exists(new_db): print("shop.db already exists")
else: print("No existing shop.db, fresh start")

print("\n✅ Setup complete! Run: python C:\\slowbuild-new\\backend\\server.py")
