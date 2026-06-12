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
