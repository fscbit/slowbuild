# -*- coding: utf-8 -*-
"""
按 Excel 清单批量重命名文件 —— 核心逻辑
Excel 两列：A=原文件名，B=新文件名（不含扩展名）；配合 zip 里的文件做批量改名。
"""

import os
import re


def normalize_key(s):
    """归一化文件名用于匹配：去扩展名、去空格/横杠/下划线、转大写"""
    base = os.path.splitext(os.path.basename(s or ''))[0]
    return re.sub(r'[\s\-_·\u3000]+', '', base).upper()


def build_rename_map(headers, rows, old_col, new_col):
    """根据 Excel 两列建立 归一化原文件名 -> 新文件名（不含扩展名） 的映射"""
    mapping = {}
    dup = []
    for _, row in rows:
        old = str(row.get(old_col) or '').strip()
        new = str(row.get(new_col) or '').strip()
        if not old or not new:
            continue
        key = normalize_key(old)
        if key in mapping:
            dup.append(old)
        mapping[key] = new
    return mapping, dup


def apply_rename(file_names, mapping):
    """file_names: 文件名列表（basename）
    返回 (renamed: [(旧名,新名)], missing: [旧名], skipped: [旧名])"""
    renamed = []
    missing = []
    skipped = []
    for fn in file_names:
        key = normalize_key(fn)
        if key not in mapping:
            missing.append(fn)
            continue
        new_base = mapping[key]
        ext = os.path.splitext(fn)[1]
        new_name = new_base + ext
        if new_name == fn:
            skipped.append(fn)
        else:
            renamed.append((fn, new_name))
    return renamed, missing, skipped
