# -*- coding: utf-8 -*-
"""
按列去重 —— 核心逻辑
按指定列（可多列）组合去重，返回去重后的表 + 被删掉的重复行。
"""

from table_utils import cell_to_str


def dedup_rows(headers, rows, cols):
    """按 cols（列名列表）组合去重
    返回 (kept_plain, removed_plain, kept_count, removed_count)
    """
    seen = set()
    kept = []
    removed = []
    for _, row in rows:
        key = tuple(cell_to_str(row.get(c)) for c in cols)
        if key in seen:
            removed.append(row)
        else:
            seen.add(key)
            kept.append(row)
    return kept, removed


def rows_plain(headers, rows):
    return [[cell_to_str(r.get(h)) for h in headers] for r in rows]
