#!/usr/bin/env python3
"""
把 products.json 的 127 个商品导入 SQLite (shop.db)
用法：python import_products.py
字段映射：products.json → shop.db products 表
"""
import json, sqlite3, os
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = BASE / "shop.db"
PRODUCTS_FILE = BASE / "products.json"

def init_db(db):
    db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL DEFAULT 'physical',
            name_en TEXT, name_cn TEXT, name_tw TEXT,
            desc_en TEXT, desc_cn TEXT, desc_tw TEXT,
            price REAL DEFAULT 0,
            image TEXT DEFAULT '',
            buy_link TEXT DEFAULT '',
            buy_link_cn TEXT DEFAULT '',
            specs TEXT DEFAULT '[]',
            shipping_en TEXT DEFAULT '', shipping_cn TEXT DEFAULT '', shipping_tw TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            title_en TEXT, title_cn TEXT, title_tw TEXT,
            desc_en TEXT, desc_cn TEXT, desc_tw TEXT,
            price REAL DEFAULT 0,
            image TEXT DEFAULT '',
            buy_link TEXT DEFAULT '',
            lesson_count INTEGER DEFAULT 0,
            duration TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    db.commit()

def product_to_row(p):
    name = p.get("name", {}) or {}
    desc = p.get("desc", {}) or {}
    shipping = p.get("shipping", {}) or {}
    specs = p.get("specs") or []
    if isinstance(specs, str):
        specs_json = specs
    else:
        specs_json = json.dumps(specs, ensure_ascii=False)
    return (
        p.get("id", ""),
        p.get("type", "physical"),
        name.get("en", ""), name.get("zh-CN", ""), name.get("zh-TW", ""),
        desc.get("en", ""), desc.get("zh-CN", ""), desc.get("zh-TW", ""),
        float(p.get("price", 0) or 0),
        p.get("image", ""),
        p.get("buyLink", ""),
        p.get("buyLinkCN", ""),
        specs_json,
        shipping.get("en", ""), shipping.get("zh-CN", ""), shipping.get("zh-TW", ""),
    )

def main():
    products = json.load(open(PRODUCTS_FILE, encoding="utf-8"))
    conn = sqlite3.connect(str(DB_PATH))
    init_db(conn)

    # 清空旧数据（避免重复）
    conn.execute("DELETE FROM products")
    conn.commit()

    n = 0
    for p in products:
        try:
            conn.execute("""
                INSERT OR REPLACE INTO products
                (id, type, name_en, name_cn, name_tw, desc_en, desc_cn, desc_tw,
                 price, image, buy_link, buy_link_cn, specs, shipping_en, shipping_cn, shipping_tw)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, product_to_row(p))
            n += 1
        except Exception as e:
            print(f"  跳过 {p.get('id')}: {e}")

    conn.commit()
    cnt = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    print(f"✅ 导入完成：{n}/{len(products)} 个商品，数据库现有 {cnt} 条")

if __name__ == "__main__":
    main()
