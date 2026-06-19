"""
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

app = Flask(__name__)
CORS(app)

WORK_DIR = Path(__file__).parent / "work"
for d in ["work/temp", "work/output"]:
    Path(WORK_DIR / d.replace("work/", "")).mkdir(parents=True, exist_ok=True)

TEMP_DIR = WORK_DIR / "temp"
OUTPUT_DIR = WORK_DIR / "output"

def find_libreoffice():
    path = r"C:\Program Files\LibreOffice\program\soffice.exe"
    if os.path.exists(path): return path
    path = r"C:\LibreOfficePortable\App\libreoffice\program\soffice.exe"
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
    return re.sub(r'[<>:"/\\|?*]', '_', name)


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
        "phones": r"1[3-9]\d{9}",
        "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "id_cards": r"\d{17}[\dXx]",
        "dates": r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
        "urls": r"https?://[^\s]+",
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
    with open(result_path, 'w', encoding='utf-8-sig') as fp:
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
        return jsonify({"error": f"不支持 .{ext}，仅支持: {config['from']}"}), 400

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
    outputs = sorted(OUTPUT_DIR.glob(f"*.{config['to']}"), key=lambda p: p.stat().st_mtime, reverse=True)
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
        with zipfile.ZipFile(zip_path, 'r') as zf:
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
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(str(extract_dir))

    IMG = {'.jpg','.jpeg','.png','.gif','.bmp','.webp','.svg','.ico','.tiff','.tif'}
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
            type TEXT NOT NULL DEFAULT 'physical',
            name_en TEXT, name_cn TEXT, name_tw TEXT,
            desc_en TEXT, desc_cn TEXT, desc_tw TEXT,
            price REAL DEFAULT 0,
            image TEXT DEFAULT '',
            buy_link TEXT DEFAULT '',
            buy_link_cn TEXT DEFAULT '',
            specs TEXT DEFAULT '[]',
            shipping_en TEXT DEFAULT '', shipping_cn TEXT DEFAULT '', shipping_tw TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            title_en TEXT, title_cn TEXT, title_tw TEXT,
            desc_en TEXT, desc_cn TEXT, desc_tw TEXT,
            price REAL DEFAULT 0,
            image TEXT DEFAULT '',
            buy_link TEXT DEFAULT '',
            video_preview TEXT DEFAULT '',
            lesson_count INTEGER DEFAULT 0,
            duration TEXT DEFAULT '',
            syllabus TEXT DEFAULT '[]',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    # Migration: add buy_link_cn if missing
    try:
        db.execute("ALTER TABLE products ADD COLUMN buy_link_cn TEXT DEFAULT ''")
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
        return jsonify({"error": f"产品 ID '{data['id']}' 已存在"}), 409
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
            updated_at=datetime('now','localtime')
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
        return jsonify({"error": f"课程 ID '{data['id']}' 已存在"}), 409
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
            updated_at=datetime('now','localtime')
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
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
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


if __name__ == "__main__":
    libre = find_libreoffice()
    print("=" * 55)
    print("  slowbuild backend v2.0")
    print(f"  LibreOffice: {'✅ ' + libre if libre else '❌ 未安装'}")
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
