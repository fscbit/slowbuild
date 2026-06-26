#!/usr/bin/env python3
"""Redesign homepage: categorized tools on homepage + shop physical only"""
import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ════════════════════════════════════════
# 1. Add CSS for category tabs
# ════════════════════════════════════════
tab_css = """
    /* Category tabs */
    .cat-tabs{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
    .cat-tab{padding:6px 14px;border:1px solid var(--border);border-radius:20px;font-size:.78rem;cursor:pointer;background:transparent;color:var(--muted);font-family:inherit;transition:all .15s}
    .cat-tab:hover{border-color:var(--accent);color:var(--text)}
    .cat-tab.active{background:var(--text);color:#fff;border-color:var(--text)}
    .cat-tab.bundle-tab{background:linear-gradient(135deg,#e87d4b,#d94a4a);color:#fff;border:none;font-weight:600}
    /* Tool list items */
    .tool-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border:1px solid var(--border);border-radius:8px;margin-bottom:6px;background:var(--surface);transition:all .15s}
    .tool-item:hover{border-color:var(--accent)}
    .tool-item .ti-icon{font-size:1.2rem;width:28px;text-align:center;flex-shrink:0}
    .tool-item .ti-name{flex:1;font-size:.82rem;font-weight:500}
    .tool-item .ti-desc{font-size:.72rem;color:var(--muted);flex:2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .tool-item .ti-price{font-weight:700;color:var(--accent);font-size:.85rem;min-width:55px;text-align:right}
    .tool-item .ti-btn{padding:5px 14px;border:1px solid var(--accent);border-radius:6px;font-size:.75rem;cursor:pointer;background:transparent;color:var(--accent);font-family:inherit;transition:all .15s;white-space:nowrap}
    .tool-item .ti-btn:hover{background:var(--accent);color:#fff}
    .tool-item .ti-badge{font-size:.65rem;padding:2px 6px;border-radius:4px;font-weight:600}
    .ti-badge.best{background:#fef8e7;color:#e87d4b}
    """

# Insert before the first occurrence of .modal-overlay
html = html.replace('    .modal-overlay{', tab_css + '\n    .modal-overlay{', 1)

# ════════════════════════════════════════
# 2. Replace the right column "My Tools" + scriptGrid with full categorized tools
# ════════════════════════════════════════

old_right_col = '''    <h2 class="sec-title">📦 <span data-i18n="sec_scripts">My Tools</span></h2>
    <p class="sec-sub" data-i18n="scripts_desc">Standalone EXE files — no install, no Python, just run.</p>

    <!-- Bundle Deal -->
    <div style="background:linear-gradient(135deg,#1e1e1e,#333);border-radius:12px;padding:24px;margin-bottom:24px;color:#fff;text-align:center">
      <span style="background:#e87d4b;padding:2px 12px;border-radius:12px;font-size:.75rem;font-weight:700">🔥 BEST VALUE</span>
      <h3 style="font-size:1.3rem;margin:12px 0 6px" data-i18n="bundle_title">All 6 Tools Bundle</h3>
      <p style="font-size:.88rem;opacity:.85;max-width:600px;margin:0 auto 14px" data-i18n="bundle_desc">Word→PDF + Duplicate Remover + Image Finder + File2Excel + Excel Splitter + XLS Converter.</p>
      <div style="display:flex;align-items:center;justify-content:center;gap:12px;flex-wrap:wrap">
        <span style="text-decoration:line-through;opacity:.6;font-size:.95rem">$29.94</span>
        <span style="font-size:2rem;font-weight:800">$22.00</span>
        <a href="https://link.payoneer.com/Token?t=6DA42646128B4562913488D8DABA0DC3&src=pl" target="_blank" style="display:inline-block;padding:12px 32px;background:#e87d4b;color:#fff;border-radius:8px;font-size:.95rem;font-weight:700;text-decoration:none;transition:opacity .2s" data-i18n="buy_bundle">Buy Bundle</a>
      </div>
      <p style="font-size:.75rem;opacity:.6;margin-top:8px" data-i18n="bundle_save">Save 27%</p>
    </div>

    <div class="tool-grid" id="scriptGrid"><!-- filled by JS --></div>'''

new_right_col = '''<h2 class="sec-title">🛠️ <span data-i18n="sec_apps">Apps & Tools</span></h2>
    <p class="sec-sub" data-i18n="apps_desc">All premium tools — download, double-click, done. No install needed.</p>

    <!-- Category Tabs -->
    <div class="cat-tabs" id="catTabs">
      <button class="cat-tab active" onclick="showCat('all')" data-i18n="cat_all">All</button>
      <button class="cat-tab" onclick="showCat('pdf')">📄 PDF</button>
      <button class="cat-tab" onclick="showCat('image')">🎨 Image</button>
      <button class="cat-tab" onclick="showCat('media')">🎬 Media</button>
      <button class="cat-tab" onclick="showCat('ecommerce')">🚀 E-Com</button>
      <button class="cat-tab" onclick="showCat('dev')">⚙️ Dev</button>
      <button class="cat-tab" onclick="showCat('utility')">📊 Utility</button>
      <button class="cat-tab bundle-tab" onclick="showCat('bundle')">🎁 Bundles</button>
    </div>

    <div id="appToolList"><!-- filled by JS --></div>'''

html = html.replace(old_right_col, new_right_col)

# Remove old scriptGrid filling JS
old_fill = '''  apiPromise.then(function(data){
    var phtml = '', chtml = '';
    (data.products||[]).forEach(function(p){ phtml += renderProductCard(p); });
    (data.courses||[]).forEach(function(c){ chtml += renderCourseCard(c); });
    pGrid.innerHTML = phtml || '<div class="empty" data-i18n="shop_empty">No products yet.</div>';
    cGrid.innerHTML = chtml || '<div class="empty" data-i18n="shop_empty">No courses yet.</div>';
  }).catch(function(){
    loadShopFromProductsJson();
  });'''

new_fill = '''  apiPromise.then(function(data){
    var products = data.products || [];
    var phtml = '';
    products.forEach(function(p){
      if(p.type==='physical') phtml += renderProductCard(p);
    });
    pGrid.innerHTML = phtml || '<div class="empty" data-i18n="shop_empty">No products yet.</div>';
  }).catch(function(){
    loadShopFromProductsJson();
  });'''

html = html.replace(old_fill, new_fill)

# Also filter physical in loadShopFromProductsJson
old_load = '''        products.forEach(function(p){ html += renderProductCard(p); });'''
new_load = '''        products.forEach(function(p){ if(p.type==='physical') html += renderProductCard(p); });'''
html = html.replace(old_load, new_load)

# Remove script grid rendering JS (the EXE tools now shown in categorized section)
old_sgrid = '''  // Fill script grid from products.json
  loadProductsJson().then(function(products){
    var html = '';
    products.forEach(function(p){
      if(p.type==='digital'){
        html += '<div class="tool-card" style="cursor:default"><div class="icon">💿</div><h3>'+(p.name[lang]||p.name.en)+'</h3><p class="desc">'+(p.desc[lang]||p.desc.en)+'</p><p style="font-size:.72rem;opacity:.5;margin-top:8px" data-i18n="no_req">'+t('no_req')+'</p><div style="margin-top:10px"><span style="font-weight:700;color:var(--accent);font-size:1rem">$'+(p.price||0).toFixed(2)+'</span> <a class="product-buy" style="float:right" href="'+(p.buyLink||'#')+'" target="_blank">'+t('buy_now')+'</a></div></div>';
      }
    });
    document.getElementById('scriptGrid').innerHTML = html || '<div class="empty" data-i18n="shop_empty">No EXE tools yet.</div>';
  });'''

new_sgrid = '''  // Fill categorized app tool list
  var allTools = [];
  var curCat = 'all';
  var catIcons = {pdf:'📄',image:'🎨',media:'🎬',ecommerce:'🚀',dev:'⚙️',utility:'📊',bundle:'🎁'};
  var catNames = {pdf:'PDF Tools',image:'Image Tools',media:'Media Tools',ecommerce:'E-Commerce Tools',dev:'Developer Tools',utility:'Utility Tools',bundle:'Bundles'};
  var catNamesCN = {pdf:'PDF工具',image:'图片工具',media:'影音工具',ecommerce:'电商工具',dev:'开发工具',utility:'常用工具',bundle:'超值套装'};
  var catNamesTW = {pdf:'PDF工具',image:'圖片工具',media:'影音工具',ecommerce:'電商工具',dev:'開發工具',utility:'常用工具',bundle:'超值套裝'};

  loadProductsJson().then(function(products){
    allTools = products.filter(function(p){ return p.type==='digital'; });
    renderAppTools();
  });

  function renderAppTools(){
    var tools = curCat==='all' ? allTools : allTools.filter(function(p){ return p.category===curCat; });
    var el = document.getElementById('appToolList');
    if(!tools.length){ el.innerHTML = '<div class="empty" data-i18n="shop_empty">No tools in this category.</div>'; return; }
    // Sort: bundles first, then by price
    tools.sort(function(a,b){
      var aB = a.id.indexOf('bundle')>=0 ? 0 : 1;
      var bB = b.id.indexOf('bundle')>=0 ? 0 : 1;
      if(aB!==bB) return aB - bB;
      return (a.price||0) - (b.price||0);
    });
    var catName = lang==='zh-CN' ? (catNamesCN[curCat]||'全部工具') : lang==='zh-TW' ? (catNamesTW[curCat]||'全部工具') : (catNames[curCat]||'All Tools');
    if(curCat==='all') catName = lang==='zh-CN'?'全部工具':lang==='zh-TW'?'全部工具':'All Tools';
    var html = '';
    tools.forEach(function(p){
      var icon = catIcons[p.category] || '🛠️';
      var isBundle = p.id.indexOf('bundle')>=0;
      var badge = '';
      if(p.id==='exe-ultimate-bundle') badge = '<span class="ti-badge best">BEST</span>';
      else if(p.id==='exe-bundle') badge = '<span class="ti-badge best">POPULAR</span>';
      var name = (p.name[lang]||p.name.en).replace('(EXE)','').replace('(Bundle)','').trim();
      if(name.length>40) name = name.substring(0,38)+'...';
      var desc = (p.desc[lang]||p.desc.en)||'';
      if(desc.length>60) desc = desc.substring(0,58)+'...';
      html += '<div class="tool-item" style="'+(isBundle?'border-color:#e87d4b;background:#fef8f0':'')+'">'+
        '<span class="ti-icon">'+icon+'</span>'+
        '<span class="ti-name">'+name+badge+'</span>'+
        '<span class="ti-desc" style="display:none" class="desc-hide">'+desc+'</span>'+
        '<span class="ti-price">$'+(p.price||0).toFixed(2)+'</span>'+
        '<button class="ti-btn" onclick="openOrder(\\''+p.id+'\\',\\''+name.replace(/'/g,'').replace(/\\\\/g,'')+'\\','+(p.price||0)+',\\'digital\\')">'+t('buy_now')+'</button>'+
        '</div>';
    });
    el.innerHTML = html;
  }

  window.showCat = function(cat){
    curCat = cat;
    document.querySelectorAll('.cat-tab').forEach(function(b){ b.classList.remove('active'); });
    document.querySelector('.cat-tab[onclick*=\"'+cat+'\"]')?.classList.add('active');
    renderAppTools();
  };

  // Make showCat global
  window.showCat = showCat;'''

html = html.replace(old_sgrid, new_sgrid)

# ════════════════════════════════════════
# 3. Add i18n strings
# ════════════════════════════════════════

# EN
html = html.replace("    order_scan_qr: 'Scan to pay, then note your Order ID:',",
    """    order_scan_qr: 'Scan to pay, then note your Order ID:',
    sec_apps: 'Apps & Tools', apps_desc: 'All premium tools — download, double-click, done. No install needed.',
    cat_all: 'All',""")

# zh-CN
html = html.replace("    order_scan_qr: '扫码支付后，备注您的订单号：',",
    """    order_scan_qr: '扫码支付后，备注您的订单号：',
    sec_apps: '应用工具', apps_desc: '所有高级工具 — 下载、双击、直接使用，无需安装。',
    cat_all: '全部',""")

# zh-TW
html = html.replace("    order_scan_qr: '掃碼付款後，備註您的訂單號：',",
    """    order_scan_qr: '掃碼付款後，備註您的訂單號：',
    sec_apps: '應用工具', apps_desc: '所有高級工具 — 下載、雙擊、直接使用，無需安裝。',
    cat_all: '全部',""")


with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('✅ index.html redesigned: categorized tools on homepage + physical-only shop')
