# -*- coding: utf-8 -*-
"""
合并多个 CSV/Excel —— 核心逻辑
按列名对齐合并（列取并集，按表头对齐，不是简单首尾拼接）。
"""

from table_utils import cell_to_str


def merge_tables(tables):
    """tables: [(文件名, headers, rows), ...]，rows=[(原行号,{列名:值})]
    返回 (merged_headers, merged_rows_plain, report)
    """
    merged_headers = []
    for _, headers, _ in tables:
        for h in headers:
            if h not in merged_headers:
                merged_headers.append(h)

    merged_rows = []
    report = []
    for fname, headers, rows in tables:
        for _, row in rows:
            merged_rows.append([cell_to_str(row.get(h)) for h in merged_headers])
        report.append({'file': fname, 'rows': len(rows)})

    total = sum(r['rows'] for r in report)
    return merged_headers, merged_rows, report, total
