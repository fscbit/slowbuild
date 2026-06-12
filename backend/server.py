"""
slowbuild 后端服务
功能：Word→PDF 转换 / 重复文件检测 / 图片提取
依赖：pip install flask flask-cors
运行：python server.py
"""

import os
import shutil
import subprocess
import filecmp
import uuid
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

WORK_DIR = Path(__file__).parent / "work"
WORK_DIR.mkdir(exist_ok=True)
TEMP_DIR = WORK_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR = WORK_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# LibreOffice 路径（安装时默认）
# 如果装了别的版本，改下面这一行
LIBREOFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"
# 备用：便携版
LIBREOFFICE_PORTABLE = r"C:\LibreOfficePortable\App\libreoffice\program\soffice.exe"


def find_libreoffice():
    """自动查找 LibreOffice"""
    for path in [LIBREOFFICE, LIBREOFFICE_PORTABLE]:
        if os.path.exists(path):
            return path
    # 搜 Program Files
    for root, dirs, files in os.walk(r"C:\Program Files"):
        if "soffice.exe" in files:
            return os.path.join(root, "soffice.exe")
    for root, dirs, files in os.walk(r"C:\Program Files (x86)"):
        if "soffice.exe" in files:
            return os.path.join(root, "soffice.exe")
    return None


def cleanup_old_files():
    """删除超过1小时的临时文件"""
    now = time.time()
    for d in [TEMP_DIR, OUTPUT_DIR]:
        for f in d.iterdir():
            if f.is_file() and now - f.stat().st_mtime > 3600:
                try:
                    f.unlink()
                except:
                    pass


def allowed_file(filename, extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in extensions


# ═══════════════════════════════════
#  API 路由
# ═══════════════════════════════════

@app.route("/")
def index():
    return jsonify({
        "service": "slowbuild-backend",
        "version": "1.0",
        "endpoints": [
            "POST /convert/word2pdf",
            "POST /convert/images2list",
            "POST /tools/dedup",
        ]
    })


@app.route("/health")
def health():
    libre = find_libreoffice()
    return jsonify({
        "status": "ok",
        "libreoffice": libre is not None,
        "libreoffice_path": libre,
        "time": datetime.now().isoformat()
    })


# ── Word → PDF ──
@app.route("/convert/word2pdf", methods=["POST"])
def convert_word2pdf():
    libre = find_libreoffice()
    if not libre:
        return jsonify({"error": "LibreOffice 未安装。请下载: https://www.libreoffice.org/"}), 500

    if "file" not in request.files:
        return jsonify({"error": "请上传文件"}), 400

    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename, {"doc", "docx"}):
        return jsonify({"error": "仅支持 .doc / .docx 文件"}), 400

    cleanup_old_files()

    job_id = str(uuid.uuid4())[:8]
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    # 保存上传文件
    ext = file.filename.rsplit(".", 1)[1].lower()
    input_path = job_dir / f"input.{ext}"
    file.save(str(input_path))

    # 调用 LibreOffice 转 PDF
    try:
        result = subprocess.run(
            [libre, "--headless", "--convert-to", "pdf", "--outdir", str(OUTPUT_DIR), str(input_path)],
            capture_output=True, text=True, timeout=120, cwd=str(OUTPUT_DIR)
        )
        print("[word2pdf]", result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        shutil.rmtree(job_dir, ignore_errors=True)
        return jsonify({"error": "转换超时（120秒），文件可能过大"}), 500
    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        return jsonify({"error": f"转换失败: {str(e)}"}), 500

    # 找生成的 PDF
    pdf_name = f"input.pdf"
    pdf_path = OUTPUT_DIR / pdf_name
    if not pdf_path.exists():
        # libreoffice 可能用 input.pdf 也可能用其他名字
        pdfs = list(OUTPUT_DIR.glob("*.pdf"))
        if pdfs:
            pdf_path = sorted(pdfs, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        else:
            shutil.rmtree(job_dir, ignore_errors=True)
            return jsonify({"error": "PDF 生成失败"}), 500

    # 改名为原文件名
    final_name = file.filename.rsplit(".", 1)[0] + ".pdf"
    final_path = OUTPUT_DIR / final_name
    if final_path.exists():
        final_path.unlink()
    pdf_path.rename(final_path)

    shutil.rmtree(job_dir, ignore_errors=True)

    # 返回下载
    return send_file(
        str(final_path),
        as_attachment=True,
        download_name=final_name,
        mimetype="application/pdf"
    )


# ── 图片提取 ──
@app.route("/convert/images2list", methods=["POST"])
def convert_images2list():
    if "file" not in request.files:
        return jsonify({"error": "请上传包含图片的 zip 文件"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".zip"):
        return jsonify({"error": "请上传 .zip 文件"}), 400

    cleanup_old_files()

    job_id = str(uuid.uuid4())[:8]
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    zip_path = job_dir / "input.zip"
    file.save(str(zip_path))

    import zipfile
    extract_dir = job_dir / "extracted"
    extract_dir.mkdir(exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(str(extract_dir))
    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        return jsonify({"error": f"解压失败: {str(e)}"}), 400

    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico', '.tiff', '.tif'}
    images = []

    for root, dirs, files in os.walk(str(extract_dir)):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in IMAGE_EXTS:
                rel_path = os.path.relpath(os.path.join(root, f), str(extract_dir))
                images.append(rel_path)

    shutil.rmtree(job_dir, ignore_errors=True)

    return jsonify({
        "count": len(images),
        "images": images
    })


# ── 重复文件检测 ──
@app.route("/tools/dedup", methods=["POST"])
def dedup():
    if "file" not in request.files:
        return jsonify({"error": "请上传 zip 文件"}), 400

    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".zip"):
        return jsonify({"error": "请上传 .zip 文件"}), 400

    cleanup_old_files()

    job_id = str(uuid.uuid4())[:8]
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    zip_path = job_dir / "input.zip"
    file.save(str(zip_path))

    import zipfile
    extract_dir = job_dir / "extracted"
    extract_dir.mkdir(exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(str(extract_dir))
    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        return jsonify({"error": f"解压失败: {str(e)}"}), 400

    # 收集所有文件
    all_files = []
    for root, dirs, files in os.walk(str(extract_dir)):
        for f in files:
            all_files.append(os.path.join(root, f))

    # 比对重复
    duplicates = []
    checked = set()
    for i, f1 in enumerate(all_files):
        for f2 in all_files[i + 1:]:
            pair = (f1, f2)
            if pair in checked:
                continue
            checked.add(pair)
            try:
                if os.path.getsize(f1) == os.path.getsize(f2) and filecmp.cmp(f1, f2, shallow=False):
                    duplicates.append({
                        "file1": os.path.relpath(f1, str(extract_dir)),
                        "file2": os.path.relpath(f2, str(extract_dir))
                    })
            except:
                pass

    shutil.rmtree(job_dir, ignore_errors=True)

    return jsonify({
        "total_files": len(all_files),
        "duplicate_pairs": len(duplicates),
        "duplicates": duplicates
    })


# ═══════════════════════════════════
#  启动
# ═══════════════════════════════════
if __name__ == "__main__":
    libre = find_libreoffice()
    print("=" * 50)
    print("  slowbuild backend v1.0")
    print(f"  LibreOffice: {'✅ ' + libre if libre else '❌ 未找到'}")
    print(f"  Port: 5000")
    print("=" * 50)

    if not libre:
        print("\n⚠️  LibreOffice 未找到！Word→PDF 功能不可用。")
        print("   请下载安装: https://www.libreoffice.org/download/")
        print("   安装后重启本程序。\n")

    app.run(host="0.0.0.0", port=5000, debug=False)
