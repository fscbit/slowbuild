# -*- coding: utf-8 -*-
"""
Word 批量替换 —— 核心逻辑（纯函数，与 GUI / Web 解耦）

从桌面版「Word 批量替换工具（带 GUI）」移植。
关键行为保持与桌面版一致：
  · 只按 run 粒度匹配替换（python-docx 限制，跨 run 的文字不会被替换）
  · occurrence 是全局计数器（按文档流顺序），供「跳过前N/只第N/第N到M」使用
  · 支持特征: all / underline / no_underline / bold / skip_first / only_nth / range
  · 范围: body 只正文 / table 只表格 / all 正文+表格
"""

import io

from docx import Document


# ═══════════════════════════════════════════
#  run 特征判断
# ═══════════════════════════════════════════

def is_underlined(run):
    u = run.underline
    if u is True:
        return True
    if u is None or u is False:
        return False
    return str(u).lower() not in ("none", "false")


def is_bold(run):
    return bool(run.bold)


def match_feature(run, feature, index_in_doc):
    """判断这个 run 是否符合替换特征。
    index_in_doc: 该匹配是文档中第几次出现（从 1 开始）
    feature: dict, 含 type 和参数
    """
    t = feature["type"]
    if t == "all":
        return True
    if t == "underline":
        return is_underlined(run)
    if t == "no_underline":
        return not is_underlined(run)
    if t == "bold":
        return is_bold(run)
    if t == "skip_first":
        return index_in_doc > feature.get("n", 0)
    if t == "only_nth":
        return index_in_doc == feature.get("n", 0)
    if t == "range":
        return feature.get("start", 0) <= index_in_doc <= feature.get("end", 0)
    return True


def iter_table_paragraphs(table):
    """递归遍历表格内所有段落（含嵌套表格）"""
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                yield p
            for t in cell.tables:
                yield from iter_table_paragraphs(t)


# ═══════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════

def _replace_in_doc(doc, old, new, feature, scope):
    """对 Document 对象执行替换，返回替换次数"""
    count = 0

    paragraphs = []
    if scope in ("body", "all"):
        paragraphs.extend(doc.paragraphs)
    if scope in ("table", "all"):
        for table in doc.tables:
            paragraphs.extend(iter_table_paragraphs(table))

    occurrence = 0  # 全局出现计数器（按文档流顺序）

    for p in paragraphs:
        for run in p.runs:
            txt = run.text or ""
            if old not in txt:
                continue

            substrings = txt.split(old)
            n_in_run = len(substrings) - 1
            if n_in_run <= 0:
                continue

            new_parts = [substrings[0]]
            changed = False
            for i in range(n_in_run):
                occurrence += 1
                if match_feature(run, feature, occurrence):
                    new_parts.append(new)
                    count += 1
                    changed = True
                else:
                    new_parts.append(old)
                new_parts.append(substrings[i + 1])

            if changed:
                run.text = "".join(new_parts)

    return count


def process_docx_to_bytes(path, old, new, feature, scope):
    """处理单个 docx，返回 (替换次数, 修改后的bytes或None)。
    不修改原文件，改动写进内存返回，供 Web 端打包下载。
    """
    doc = Document(path)
    count = _replace_in_doc(doc, old, new, feature, scope)

    if count > 0:
        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        return count, buf.getvalue()
    return count, None
