# -*- coding: utf-8 -*-
"""
文件名与 Excel 核对 —— 核心逻辑（纯函数，与 GUI / Web 解耦）

从桌面版 v2.0 移植，修复了以下问题：
  · cell_to_str: 纯日期(datetime 0点) 只返回日期部分，避免跟文件名 YYYYMMDD 对不上
  · 主字段文本比对走 normalize（去空格/横杠/下划线/转大写）
  · 副字段支持日期容差
"""

import os
import re
from datetime import datetime

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None


EXTRACT_METHODS = [
    '取前N个字',
    '取后N个字',
    '按分隔符取第N段',
    '取开头连续数字字母横杠',
    '关键词后',
    '正则表达式',
    '不提取(仅用于副字段留空)',
]


# ═══════════════════════════════════════════
#  通用工具
# ═══════════════════════════════════════════

def cell_to_str(v):
    if v is None:
        return ''
    if isinstance(v, datetime):
        if v.hour == 0 and v.minute == 0 and v.second == 0:
            return v.strftime('%Y-%m-%d')
        return v.strftime('%Y-%m-%d %H:%M')
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def normalize_text(s):
    """归一化: 去空格、去横杠、去下划线、去中圆点、转大写，用于宽松比对"""
    return re.sub(r'[\s\-_·\u3000]+', '', str(s or '')).upper()


def date8_from_value(v):
    if v is None or v == '':
        return None
    if isinstance(v, datetime):
        return v.strftime('%Y%m%d')
    s = str(v).strip()
    if not s:
        return None
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M', '%Y/%m/%d',
                '%Y.%m.%d', '%Y%m%d', '%Y年%m月%d日'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y%m%d')
        except ValueError:
            pass
    m = re.search(r'(\d{4})\D?(\d{1,2})\D?(\d{1,2})', s)
    if m:
        y, mo, d = m.groups()
        try:
            return datetime(int(y), int(mo), int(d)).strftime('%Y%m%d')
        except ValueError:
            pass
    digits = re.sub(r'\D', '', s)
    if len(digits) >= 8:
        try:
            return datetime.strptime(digits[:8], '%Y%m%d').strftime('%Y%m%d')
        except ValueError:
            pass
    return None


def date_diff_days(d8a, d8b):
    try:
        a = datetime.strptime(d8a, '%Y%m%d')
        b = datetime.strptime(d8b, '%Y%m%d')
        return abs((a - b).days)
    except Exception:
        return None


def read_excel_rows(path):
    """读取 Excel：返回 (headers, rows)
    rows: [(行号, {列名: 值}), ...]
    """
    if openpyxl is None:
        raise RuntimeError('缺少 openpyxl 依赖')
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    headers = []
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
        if i == 1:
            for j, c in enumerate(row):
                h = str(c).strip() if c is not None else ''
                if not h:
                    h = '列' + str(j + 1)
                base, k = h, 2
                while h in headers:
                    h = base + '_' + str(k)
                    k += 1
                headers.append(h)
            continue
        if not any(v is not None and str(v).strip() for v in row):
            continue
        d = {}
        for j, h in enumerate(headers):
            d[h] = row[j] if j < len(row) else None
        rows.append((i, d))
    wb.close()
    return headers, rows


def resolve_column(sel, headers):
    """根据下拉值或列序号定位列名；返回列名或 None"""
    sel = (sel or '').strip()
    if not sel:
        return None
    if sel in headers:
        return sel
    if sel.isdigit():
        idx = int(sel) - 1
        if 0 <= idx < len(headers):
            return headers[idx]
    low = sel.lower()
    for h in headers:
        if h.lower() == low:
            return h
    return None


# ═══════════════════════════════════════════
#  字段提取器
# ═══════════════════════════════════════════

def extract_field(name, method, param):
    """从文件名中按指定方式提取字段"""
    base = os.path.splitext(os.path.basename(name))[0]
    param = (param or '').strip()

    if method == '取前N个字':
        try:
            n = int(param)
        except Exception:
            return ''
        return base[:n] if n > 0 else ''

    if method == '取后N个字':
        try:
            n = int(param)
        except Exception:
            return ''
        return base[-n:] if n > 0 else ''

    if method == '按分隔符取第N段':
        if ':' in param:
            sep, idx_s = param.split(':', 1)
        else:
            sep, idx_s = param, '1'
        if not sep:
            sep = '_'
        try:
            idx = int(idx_s)
        except Exception:
            idx = 1
        parts = base.split(sep)
        if 1 <= idx <= len(parts):
            return parts[idx - 1].strip()
        return ''

    if method == '取开头连续数字字母横杠':
        m = re.match(r'^[0-9A-Za-z\-]+', base)
        return m.group(0) if m else ''

    if method == '关键词后':
        kw = param
        if kw and kw in base:
            return base.split(kw, 1)[1].strip()
        return ''

    if method == '正则表达式':
        try:
            m = re.search(param, base)
        except re.error:
            return ''
        if not m:
            return ''
        return m.group(1) if m.groups() else m.group(0)

    return ''


# ═══════════════════════════════════════════
#  核对主流程
# ═══════════════════════════════════════════

def guess_key_col(headers):
    """自动猜主核对列：优先含「编号/序号/ID」字样的列，否则第一列"""
    if not headers:
        return None
    for kw in ('编号', '序号', 'ID', 'id', '编号', '编码', '代码'):
        for h in headers:
            if kw in h:
                return h
    return headers[0]


def run_check(headers, rows, file_names, key_col, key_method, key_param,
              sub_col=None, sub_method='', sub_param='', tol=0):
    """执行核对
    file_names: 文件名列表（basename）
    返回 dict: {rows, extra, stats}
    """
    key_col = resolve_column(key_col, headers)
    sub_col = resolve_column(sub_col, headers) if sub_col else None
    use_sub = bool(sub_col)

    file_infos = []
    for name in file_names:
        file_infos.append({
            'name': name,
            'key': extract_field(name, key_method, key_param),
            'sub': extract_field(name, sub_method, sub_param) if use_sub else '',
        })

    try:
        tol = int(tol or 0)
    except Exception:
        tol = 0

    row_results = []
    used_files = set()
    n_ok = n_warn = n_err = 0

    for rownum, row in rows:
        key_raw = cell_to_str(row.get(key_col))
        key_norm = normalize_text(key_raw)
        sub_raw = cell_to_str(row.get(sub_col)) if sub_col else ''
        sub_date = date8_from_value(row.get(sub_col)) if sub_col else None

        if not key_norm:
            row_results.append({
                'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'err',
                'status': '主字段为空', 'file': '', 'note': 'Excel 该行没有主字段值',
            })
            n_err += 1
            continue

        cand = [fi for fi in file_infos if normalize_text(fi['key']) == key_norm]
        if not cand:
            row_results.append({
                'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'err',
                'status': '未找到对应文件', 'file': '', 'note': '文件夹中无此文件',
            })
            n_err += 1
            continue

        for fi in cand:
            used_files.add(fi['name'])

        if len(cand) > 1:
            names = '、'.join(fi['name'] for fi in cand[:5])
            if len(cand) > 5:
                names += ' 等共 ' + str(len(cand)) + ' 个'
            row_results.append({
                'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'warn',
                'status': '找到 ' + str(len(cand)) + ' 个匹配文件', 'file': names,
                'note': '请人工确认',
            })
            n_warn += 1
            continue

        fi = cand[0]

        if not use_sub:
            row_results.append({
                'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'ok',
                'status': '匹配', 'file': fi['name'], 'note': '',
            })
            n_ok += 1
            continue

        # 副字段核对
        if not sub_date:
            if normalize_text(fi['sub']) == normalize_text(sub_raw):
                row_results.append({
                    'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'ok',
                    'status': '匹配', 'file': fi['name'], 'note': '',
                })
                n_ok += 1
            else:
                row_results.append({
                    'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'warn',
                    'status': '副字段不符', 'file': fi['name'],
                    'note': 'Excel: ' + sub_raw + ' / 文件: ' + fi['sub'],
                })
                n_warn += 1
        else:
            fdate = date8_from_value(fi['sub'])
            if not fdate:
                row_results.append({
                    'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'warn',
                    'status': '文件名副字段无日期', 'file': fi['name'], 'note': '',
                })
                n_warn += 1
            elif fdate == sub_date:
                row_results.append({
                    'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'ok',
                    'status': '匹配', 'file': fi['name'], 'note': '',
                })
                n_ok += 1
            else:
                dd = date_diff_days(fdate, sub_date)
                if dd is not None and dd <= tol:
                    msg = '日期差 ' + str(dd) + ' 天(容差内)'
                else:
                    msg = ('日期不符(差 ' + str(dd) + ' 天)') if dd is not None else '日期不符'
                row_results.append({
                    'rownum': rownum, 'key': key_raw, 'sub': sub_raw, 'tag': 'warn',
                    'status': msg, 'file': fi['name'],
                    'note': 'Excel: ' + str(sub_date) + ' / 文件: ' + str(fdate),
                })
                n_warn += 1

    extra_files = []
    for fi in file_infos:
        if fi['name'] not in used_files:
            extra_files.append({
                'name': fi['name'],
                'key': fi['key'] or '无',
                'sub': fi['sub'] or '无',
                'note': 'Excel 中无对应记录',
            })

    stats = {
        'excel_rows': len(rows),
        'files_total': len(file_infos),
        'ok': n_ok,
        'warn': n_warn,
        'err': n_err,
        'extra': len(extra_files),
        'rate': round(n_ok / len(rows) * 100, 2) if rows else 0.0,
    }

    return {'rows': row_results, 'extra': extra_files, 'stats': stats}
