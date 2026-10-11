# -*- coding: utf-8 -*-
"""
合并多个 CSV/Excel —— 路由
POST /api/merge/run       上传多个文件 → 返回汇总
GET  /api/merge/download/<job_id>  下载合并结果（xlsx 或 csv）
"""

import os
import io
import uuid
import time

from flask import request, jsonify, send_file

from table_utils import read_table, write_xlsx_bytes, write_csv_bytes
from merge_core import merge_tables

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, 'work', 'merge')
os.makedirs(WORK_DIR, exist_ok=True)

JOBS = {}
JOB_TTL = 3600


def register_merge_routes(app):

    @app.route('/api/merge/run', methods=['POST'])
    def merge_run():
        files = [f for f in request.files.getlist('files') if f and f.filename]
        if len(files) < 2:
            return jsonify({'error': '请上传至少 2 个文件'}), 400

        jid = uuid.uuid4().hex[:12]
        tables = []
        for f in files:
            path = os.path.join(WORK_DIR, jid + '_' + uuid.uuid4().hex[:6] +
                                os.path.splitext(f.filename)[1])
            f.save(path)
            try:
                headers, rows = read_table(path)
            except Exception as e:
                return jsonify({'error': '读取 %s 失败: %s' % (f.filename, str(e))}), 400
            tables.append((f.filename, headers, rows))

        merged_headers, merged_rows, report, total = merge_tables(tables)
        JOBS[jid] = {'created': time.time(), 'headers': merged_headers,
                     'rows': merged_rows, 'fmt': 'xlsx'}
        return jsonify({'job_id': jid, 'headers': merged_headers,
                        'total_rows': total, 'report': report})

    @app.route('/api/merge/download/<job_id>', methods=['GET'])
    def merge_download(job_id):
        job = JOBS.get(job_id)
        if not job:
            return jsonify({'error': '没有可下载的结果'}), 400
        fmt = request.args.get('fmt', 'xlsx')
        if fmt == 'csv':
            data = write_csv_bytes(job['headers'], job['rows'])
            name = '合并结果.csv'
            mime = 'text/csv'
        else:
            data = write_xlsx_bytes(job['headers'], job['rows'])
            name = '合并结果.xlsx'
            mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return send_file(io.BytesIO(data), as_attachment=True,
                         download_name=name, mimetype=mime)
