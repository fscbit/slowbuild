# -*- coding: utf-8 -*-
"""
Word 批量替换 —— 线上工具（接入 slowbuild 后端）
======================================================
路由:
  POST /api/wordreplace/run            上传 .docx（zip 或多个文件）→ 批量替换
  GET  /api/wordreplace/download/<job> 下载替换后的所有 docx（zip）

前端页面: /wordreplace.html (Vercel 托管)，BACKEND = api.slowbuild.top
"""

import os
import io
import uuid
import time
import zipfile
import shutil

from flask import request, jsonify, send_file

from wordreplace_core import process_docx_to_bytes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, 'work', 'wordreplace')
os.makedirs(WORK_DIR, exist_ok=True)

JOBS = {}
JOB_TTL = 3600  # 1 小时

FEATURE_TYPES = ('all', 'underline', 'no_underline', 'bold',
                 'skip_first', 'only_nth', 'range')
SCOPES = ('body', 'table', 'all')


def _safe_zip_name(name):
    """处理 Windows 打包 zip 的中文文件名乱码（cp437 -> gbk/utf-8）"""
    try:
        return name.encode('cp437').decode('gbk')
    except Exception:
        try:
            return name.encode('cp437').decode('utf-8')
        except Exception:
            return name


def _dedupe(base, used):
    """重名时追加 _1、_2 ..."""
    if base not in used:
        used.add(base)
        return base
    stem, ext = os.path.splitext(base)
    i = 1
    while True:
        cand = '%s_%d%s' % (stem, i, ext)
        if cand not in used:
            used.add(cand)
            return cand
        i += 1


def _collect_docx(zip_file, uploads, dest_dir):
    """收集 .docx 文件到 dest_dir（扁平化到 basename），返回 (文件名列表, 错误)"""
    names = []
    used = set()

    if zip_file and zip_file.filename:
        zip_path = os.path.join(dest_dir, '_input.zip')
        zip_file.save(zip_path)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                for info in zf.infolist():
                    name = _safe_zip_name(info.filename)
                    safe = name.replace('\\', '/').lstrip('/')
                    if '..' in safe.split('/') or info.is_dir():
                        continue
                    if not safe.lower().endswith('.docx'):
                        continue
                    base = _dedupe(os.path.basename(safe), used)
                    target = os.path.join(dest_dir, base)
                    with zf.open(info) as src, open(target, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    names.append(base)
        except zipfile.BadZipFile:
            return None, '文件不是有效的 zip 压缩包'
        except Exception as e:
            return None, '解压失败: ' + str(e)
    else:
        uploads = [f for f in uploads if f and f.filename]
        for f in uploads:
            if not f.filename.lower().endswith('.docx'):
                continue
            base = _dedupe(os.path.basename(f.filename.replace('\\', '/')), used)
            f.save(os.path.join(dest_dir, base))
            names.append(base)

    if not names:
        return None, '没有找到 .docx 文件（请上传 zip 或 .docx）'
    return names, None


def register_wordreplace_routes(app):

    @app.route('/api/wordreplace/run', methods=['POST'])
    def wordreplace_run():
        old = (request.form.get('old') or '').strip()
        new = request.form.get('new') or ''
        feature_type = request.form.get('feature') or 'all'
        scope = request.form.get('scope') or 'all'

        if not old:
            return jsonify({'error': '被替换文字不能为空'}), 400
        if feature_type not in FEATURE_TYPES:
            return jsonify({'error': '无效的替换特征'}), 400
        if scope not in SCOPES:
            return jsonify({'error': '无效的处理范围'}), 400

        feature = {'type': feature_type}
        try:
            if feature_type in ('skip_first', 'only_nth'):
                feature['n'] = int(request.form.get('n') or '0')
            elif feature_type == 'range':
                feature['start'] = int(request.form.get('start') or '0')
                feature['end'] = int(request.form.get('end') or '0')
        except ValueError:
            return jsonify({'error': '参数必须是整数'}), 400

        jid = uuid.uuid4().hex[:12]
        job_dir = os.path.join(WORK_DIR, jid)
        os.makedirs(job_dir, exist_ok=True)

        zip_file = request.files.get('zip')
        uploads = request.files.getlist('files')
        names, err = _collect_docx(zip_file, uploads, job_dir)
        if err:
            shutil.rmtree(job_dir, ignore_errors=True)
            return jsonify({'error': err}), 400

        results = []
        changed_files = []  # (name, bytes)
        total = 0
        for name in names:
            path = os.path.join(job_dir, name)
            try:
                n, data = process_docx_to_bytes(path, old, new, feature, scope)
                total += n
                results.append({'name': name, 'count': n})
                if data is not None:
                    changed_files.append((name, data))
            except Exception as e:
                results.append({'name': name, 'count': -1, 'error': str(e)})

        JOBS[jid] = {
            'created': time.time(),
            'dir': job_dir,
            'changed_files': changed_files,
            'total': total,
        }

        return jsonify({
            'job_id': jid,
            'total': total,
            'changed': len(changed_files),
            'results': results,
        })

    @app.route('/api/wordreplace/download/<job_id>', methods=['GET'])
    def wordreplace_download(job_id):
        job = JOBS.get(job_id)
        if not job:
            return jsonify({'error': '没有可下载的结果'}), 400

        changed = job['changed_files']
        if not changed:
            return jsonify({'error': '没有文件被替换，无需下载'}), 400

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            seen = set()
            for name, data in changed:
                base = _dedupe(name, seen)
                zf.writestr(base, data)
        buf.seek(0)

        return send_file(
            buf, as_attachment=True,
            download_name='替换结果_' + time.strftime('%Y%m%d_%H%M%S') + '.zip',
            mimetype='application/zip',
        )
