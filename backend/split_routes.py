# -*- coding: utf-8 -*-
"""
Excel/CSV 按列拆分 —— 路由
POST /api/split/analyze    上传文件 → 返回表头
POST /api/split/run        执行拆分
GET  /api/split/download/<job_id>  下载拆分结果（zip 或 xlsx）
"""

import os
import io
import uuid
import time
import shutil

from flask import request, jsonify, send_file

from table_utils import read_table, resolve_column
from split_core import split_by_column, build_split_zip, build_split_sheets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORK_DIR = os.path.join(BASE_DIR, 'work', 'split')
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


def register_split_routes(app):

    @app.route('/api/split/analyze', methods=['POST'])
    def split_analyze():
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

    @app.route('/api/split/run', methods=['POST'])
    def split_run():
        data = request.get_json(silent=True) or {}
        job = JOBS.get(data.get('job_id'))
        if not job:
            return jsonify({'error': '会话过期，请重新上传'}), 400
        col = resolve_column(data.get('col'), job['headers'])
        if not col:
            return jsonify({'error': '请选择拆分列'}), 400
        fmt = data.get('fmt', 'xlsx')
        mode = data.get('mode', 'files')  # files | sheets
        groups = split_by_column(job['headers'], job['rows'], col)
        job['col'] = col
        job['fmt'] = fmt
        job['mode'] = mode
        job['groups'] = groups
        ginfo = [{'value': v, 'count': len(rows)} for v, rows in groups]
        return jsonify({'groups': ginfo, 'group_count': len(groups)})

    @app.route('/api/split/download/<job_id>', methods=['GET'])
    def split_download(job_id):
        job = JOBS.get(job_id)
        if not job or 'groups' not in job:
            return jsonify({'error': '没有可下载的结果'}), 400
        groups = job['groups']
        fmt = job.get('fmt', 'xlsx')
        if job.get('mode') == 'sheets':
            data = build_split_sheets(job['headers'], groups)
            name = '拆分结果_' + job['col'] + '.xlsx'
            mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            data = build_split_zip(job['headers'], groups, fmt)
            name = '拆分结果_' + job['col'] + '.zip'
            mime = 'application/zip'
        return send_file(io.BytesIO(data), as_attachment=True,
                         download_name=name, mimetype=mime)
