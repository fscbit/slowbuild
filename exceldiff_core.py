# -*- coding: utf-8 -*-
"""
两个 Excel/CSV 对比 —— 核心逻辑
逐单元格比对，输出带高亮的差异表和汇总统计。
"""

from table_utils import cell_to_str, rows_to_plain, write_xlsx_bytes


def compare_tables(headers1, rows1, headers2, rows2):
    """对比两张表
    rows1/rows2: [(原行号, {列名:值}), ...]
    返回 (result, highlight, diff_headers)
    result: list[list] 合并后的对比表（含新增/删除行）
    highlight: dict{(r,c): 'red'|'yellow'|'blue'} 用于导出
    """
    # 统一列（并集，保持两表顺序）
    seen = []
    for h in list(headers1) + list(headers2):
        if h not in seen:
            seen.append(h)
    diff_headers = seen

    # 用 (原行号, 该行文本) 做对齐 —— 这里按行号对齐更直观，但两表行数可能不同
    # 策略：取两表行号并集，同一行号逐列比对；缺失的整行标蓝
    rownums = sorted(set(r[0] for r in rows1) | set(r[0] for r in rows2))
    d1 = {r[0]: r[1] for r in rows1}
    d2 = {r[0]: r[1] for r in rows2}

    result = []
    highlight = {}
    changed = 0
    added_rows = 0
    removed_rows = 0
    r = 2  # 第1行是表头
    for rn in rownums:
        a = d1.get(rn)
        b = d2.get(rn)
        if a is None and b is not None:
            # 表2 新增的行
            result.append([cell_to_str(b.get(h)) for h in diff_headers])
            for c in range(1, len(diff_headers) + 1):
                highlight[(r, c)] = 'blue'
            added_rows += 1
        elif a is not None and b is None:
            # 表1 独有的行（表2 删掉的行）
            result.append([cell_to_str(a.get(h)) for h in diff_headers])
            for c in range(1, len(diff_headers) + 1):
                highlight[(r, c)] = 'red'
            removed_rows += 1
        else:
            row_out = []
            for j, h in enumerate(diff_headers):
                va = cell_to_str(a.get(h))
                vb = cell_to_str(b.get(h))
                if va == vb:
                    row_out.append(va)
                else:
                    row_out.append(va + '  →  ' + vb)
                    highlight[(r, j + 1)] = 'yellow'
                    changed += 1
            result.append(row_out)
        r += 1

    summary = {
        'rows1': len(rows1),
        'rows2': len(rows2),
        'changed_cells': changed,
        'added_rows': added_rows,
        'removed_rows': removed_rows,
        'same': changed == 0 and added_rows == 0 and removed_rows == 0,
    }
    return result, highlight, diff_headers, summary


def build_diff_xlsx(diff_headers, result, highlight):
    return write_xlsx_bytes(diff_headers, result, highlight=highlight)
