# -*- coding: utf-8 -*-
"""
两个 Excel/CSV 对比 —— 路由
POST /api/exceldiff/run       上传两个文件 → 返回汇总
GET  /api/exceldiff/download/<job_id>  下载高亮差异表
"""

import os
import io
import uuid
import time

from flask import request, jsonify, send_file

from table_utils import read_table
from exceldiff_core import compare_tables, build_diff_xlsx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, 'work', 'exceldiff')
os.makedirs(WORK_DIR, exist_ok=True)

JOBS = {}
JOB_TTL = 3600


def register_exceldiff_routes(app):

    @app.route('/api/exceldiff/run', methods=['POST'])
    def exceldiff_run():
        f1 = request.files.get('file1')
        f2 = request.files.get('file2')
        if not f1 or not f2:
            return jsonify({'error': '请上传两个文件'}), 400

        jid = uuid.uuid4().hex[:12]
        p1 = os.path.join(WORK_DIR, jid + '_1' + os.path.splitext(f1.filename)[1])
        p2 = os.path.join(WORK_DIR, jid + '_2' + os.path.splitext(f2.filename)[1])
        f1.save(p1)
        f2.save(p2)
        try:
            h1, r1 = read_table(p1)
            h2, r2 = read_table(p2)
        except Exception as e:
            return jsonify({'error': '读取失败: ' + str(e)}), 400

        result, highlight, diff_headers, summary = compare_tables(h1, r1, h2, r2)
        JOBS[jid] = {'created': time.time(), 'p1': p1, 'p2': p2,
                     'headers': diff_headers, 'result': result,
                     'highlight': highlight, 'summary': summary,
                     'name1': f1.filename, 'name2': f2.filename}
        return jsonify({'job_id': jid, 'summary': summary,
                        'headers': diff_headers})

    @app.route('/api/exceldiff/download/<job_id>', methods=['GET'])
    def exceldiff_download(job_id):
        job = JOBS.get(job_id)
        if not job:
            return jsonify({'error': '没有可下载的结果'}), 400
        data = build_diff_xlsx(job['headers'], job['result'], job['highlight'])
        return send_file(io.BytesIO(data), as_attachment=True,
                         download_name='对比差异.xlsx',
                         mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
