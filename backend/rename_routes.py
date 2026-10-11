# -*- coding: utf-8 -*-
"""
按 Excel 清单批量重命名 —— 路由
POST /api/rename/analyze    上传 Excel + 文件(zip)
POST /api/rename/run        执行重命名
GET  /api/rename/download/<job_id>  下载改名后的文件(zip) + 报告
"""

import os
import io
import uuid
import time
import shutil
import zipfile

from flask import request, jsonify, send_file

from table_utils import read_table, resolve_column
from rename_core import build_rename_map, apply_rename, normalize_key

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, 'work', 'rename')
os.makedirs(WORK_DIR, exist_ok=True)

JOBS = {}
JOB_TTL = 3600


def _safe_zip_name(name):
    try:
        return name.encode('cp437').decode('gbk')
    except Exception:
        try:
            return name.encode('cp437').decode('utf-8')
        except Exception:
            return name


def _cleanup():
    now = time.time()
    for jid in list(JOBS.keys()):
        j = JOBS[jid]
        if now - j['created'] > JOB_TTL:
            shutil.rmtree(j['dir'], ignore_errors=True)
            del JOBS[jid]


def _collect_files(zip_path, dest_dir):
    names = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = _safe_zip_name(info.filename)
            safe = name.replace('\\', '/').lstrip('/')
            if '..' in safe.split('/'):
                continue
            target = os.path.join(dest_dir, safe)
            if info.is_dir():
                os.makedirs(target, exist_ok=True)
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with zf.open(info) as src, open(target, 'wb') as dst:
                shutil.copyfileobj(src, dst)
            if os.path.isfile(target):
                names.append(os.path.basename(name))
    return names


def register_rename_routes(app):

    @app.route('/api/rename/analyze', methods=['POST'])
    def rename_analyze():
        _cleanup()
        excel = request.files.get('excel')
        if not excel:
            return jsonify({'error': '请上传 Excel 清单'}), 400
        jid = uuid.uuid4().hex[:12]
        jdir = os.path.join(WORK_DIR, jid)
        os.makedirs(jdir, exist_ok=True)
        excel_path = os.path.join(jdir, 'list.xlsx')
        excel.save(excel_path)

        zip_file = request.files.get('zip')
        files_dir = os.path.join(jdir, 'files')
        os.makedirs(files_dir, exist_ok=True)
        file_names = []
        if zip_file and zip_file.filename:
            zp = os.path.join(jdir, 'files.zip')
            zip_file.save(zp)
            try:
                file_names = _collect_files(zp, files_dir)
            except zipfile.BadZipFile:
                shutil.rmtree(jdir, ignore_errors=True)
                return jsonify({'error': '文件不是有效的 zip'}), 400
        else:
            uploads = [f for f in request.files.getlist('files') if f and f.filename]
            if not uploads:
                shutil.rmtree(jdir, ignore_errors=True)
                return jsonify({'error': '请上传文件 zip 或选择文件'}), 400
            for f in uploads:
                target = os.path.join(files_dir, os.path.basename(f.filename))
                f.save(target)
                file_names.append(os.path.basename(f.filename))

        try:
            headers, rows = read_table(excel_path)
        except Exception as e:
            shutil.rmtree(jdir, ignore_errors=True)
            return jsonify({'error': '读取 Excel 失败: ' + str(e)}), 400

        JOBS[jid] = {'created': time.time(), 'dir': jdir, 'headers': headers,
                     'rows': rows, 'file_names': sorted(set(file_names))}
        return jsonify({'job_id': jid, 'headers': headers,
                        'rows_count': len(rows),
                        'files_count': len(JOBS[jid]['file_names']),
                        'files': JOBS[jid]['file_names'][:20]})

    @app.route('/api/rename/run', methods=['POST'])
    def rename_run():
        data = request.get_json(silent=True) or {}
        job = JOBS.get(data.get('job_id'))
        if not job:
            return jsonify({'error': '会话过期，请重新上传'}), 400
        old_col = resolve_column(data.get('old_col'), job['headers'])
        new_col = resolve_column(data.get('new_col'), job['headers'])
        if not old_col or not new_col:
            return jsonify({'error': '请选择原文件名列和新文件名列'}), 400

        mapping, dup = build_rename_map(job['headers'], job['rows'], old_col, new_col)
        renamed, missing, skipped = apply_rename(job['file_names'], mapping)

        job['renamed'] = renamed
        job['missing'] = missing
        job['skipped'] = skipped
        job['dup'] = dup

        return jsonify({
            'renamed_count': len(renamed),
            'missing_count': len(missing),
            'skipped_count': len(skipped),
            'dup_count': len(dup),
            'renamed': renamed[:50],
            'missing': missing[:50],
            'dup': dup[:20],
        })

    @app.route('/api/rename/download/<job_id>', methods=['GET'])
    def rename_download(job_id):
        job = JOBS.get(job_id)
        if not job or 'renamed' not in job:
            return jsonify({'error': '没有可下载的结果'}), 400

        files_dir = os.path.join(job['dir'], 'files')
        buf = io.BytesIO()
        used = set()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for old, new in job['renamed']:
                # 防重名
                final = new
                k = 2
                while final in used:
                    base, ext = os.path.splitext(new)
                    final = base + '_' + str(k) + ext
                    k += 1
                used.add(final)
                src = os.path.join(files_dir, old)
                if os.path.isfile(src):
                    with open(src, 'rb') as f:
                        zf.writestr(final, f.read())
            # 报告
            lines = ['原文件名,新文件名,状态']
            for old, new in job['renamed']:
                lines.append('%s,%s,已改名' % (old, new))
            for m in job['missing']:
                lines.append('%s,,未找到' % m)
            for s in job['skipped']:
                lines.append('%s,,无需改名' % s)
            zf.writestr('重命名报告.csv',
                        ('\ufeff' + '\n'.join(lines)).encode('utf-8'))

        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name='重命名结果.zip', mimetype='application/zip')
