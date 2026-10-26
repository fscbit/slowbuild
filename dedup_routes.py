# -*- coding: utf-8 -*-
"""
按列去重 —— 路由
POST /api/dedup/analyze    上传文件 → 返回表头
POST /api/dedup/run        执行去重
GET  /api/dedup/download/<job_id>  下载去重结果
"""

import os
import io
import uuid
import time

from flask import request, jsonify, send_file

from table_utils import read_table, resolve_column, write_xlsx_bytes
from dedup_core import dedup_rows, rows_plain

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, 'work', 'dedup')
os.makedirs(WORK_DIR, exist_ok=True)

JOBS = {}
JOB_TTL = 3600


def _cleanup():
    now = time.time()
    for jid in list(JOBS.keys()):
        j = JOBS[jid]
        if now - j['created'] > JOB_TTL:
            if os.path.exists(j['path']):
                os.remove(j['path'])
            del JOBS[jid]


def register_dedup_routes(app):

    @app.route('/api/dedup/analyze', methods=['POST'])
    def dedup_analyze():
        _cleanup()
        f = request.files.get('file')
        if not f:
            return jsonify({'error': '请上传文件'}), 400
        jid = uuid.uuid4().hex[:12]
        path = os.path.join(WORK_DIR, jid + os.path.splitext(f.filename)[1])
        f.save(path)
        try:
            headers, rows = read_table(path)
        except Exception as e:
            os.remove(path)
            return jsonify({'error': '读取失败: ' + str(e)}), 400
        JOBS[jid] = {'created': time.time(), 'path': path, 'headers': headers,
                     'rows': rows}
        return jsonify({'job_id': jid, 'headers': headers, 'rows_count': len(rows)})

    @app.route('/api/dedup/run', methods=['POST'])
    def dedup_run():
        data = request.get_json(silent=True) or {}
        job = JOBS.get(data.get('job_id'))
        if not job:
            return jsonify({'error': '会话过期，请重新上传'}), 400
        cols_raw = data.get('cols') or []
        cols = [resolve_column(c, job['headers']) for c in cols_raw]
        cols = [c for c in cols if c]
        if not cols:
            return jsonify({'error': '请选择去重依据列'}), 400

        kept, removed = dedup_rows(job['headers'], job['rows'], cols)
        job['kept'] = rows_plain(job['headers'], kept)
        job['removed'] = rows_plain(job['headers'], removed)
        return jsonify({'kept': len(kept), 'removed': len(removed)})

    @app.route('/api/dedup/download/<job_id>', methods=['GET'])
    def dedup_download(job_id):
        job = JOBS.get(job_id)
        if not job or 'kept' not in job:
            return jsonify({'error': '没有可下载的结果'}), 400
        data = write_xlsx_bytes(job['headers'], job['kept'])
        return send_file(io.BytesIO(data), as_attachment=True,
                         download_name='去重结果.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
