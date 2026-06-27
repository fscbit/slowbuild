# Homepage Redesign Spec — slowbuild.top

**版本**: v1.0  
**日期**: 2026-06-27  
**受众**: 打工牛马（办公室白领、职场人）  
**核心主题**: 算命（Fortune）+ 工具（Tools）

---

## 设计原则
1. **首屏即命定**: 首页两大板块（算命/工具）必须首屏可见
2. **言简意赅**: Hero 区一句话说清"这里有什么"
3. **紧凑不拥挤**: 工具区收折，不占据大面积
4. **移动优先**: 办公室白领手机刷站的比例高
5. **不改布局架构**: 只改 index.html，侧边栏/导航/页脚不变

---

## 1. 首页区域 HTML 结构

### 整体结构（从上到下）
```
<main>
  ① Hero（一句话标题 + 副标题 + 两个主入口按钮）
  ② 命运之门 Fortune Gateway（大卡片入口 + 热门命理工具标签）
  ③ 算命文化博客摘要（3-4篇最新博客卡片）
  ④ 在线工具 Online Tools（精选6-8个常用工具图标网格）
  ⑤ 付费工具区 Premium Apps（分类标签折叠 + 从 products.json 加载）
  ⑥ 职场博客 Workplace Blog 入口卡片
  ⑦ Shop 入口卡片（DIY + 电子产品）
  ⑧ 提需求盒子（保留现有 request 区）
</main>
```

### ① Hero 区域
```html
<section class="hero">
  <h1 data-i18n="hero_title">Tools & Fortune for the Daily Grind.</h1>
  <p class="sub" data-i18n="hero_sub">PDF conversion, fortune reading, office gadgets — built for the 9-to-5 warriors.</p>
  <div class="hero-cta">
    <a href="#fortune" class="btn primary" data-i18n="hero_fortune_btn">🔮 Try Fortune</a>
    <a href="#tools" class="btn" data-i18n="hero_tools_btn">🛠️ Browse Tools</a>
  </div>
</section>
```
**改动**: 
- Title 从 "Free micro tools, built slow" → "Tools & Fortune for the Daily Grind"  
- 删除原来的 tags 标签行
- 新增两个 CTA 按钮（锚点跳转到下方板块）

### ② 命运之门 Fortune Gateway
```html
<section id="fortune" class="section fortune-gateway">
  <h2>🔮 <span data-i18n="fortune_head">Fortune Gateway</span></h2>
  <p class="sec-sub" data-i18n="fortune_head_sub">八字 · 塔罗 · 星座 · 易经 — AI-powered destiny reading.</p>
  
  <a href="/fortune.html" class="fortune-hero-card">
    <span class="fortune-icon">🔮</span>
    <div class="fortune-hero-text">
      <strong data-i18n="fortune_title">Fortune Gateway · 命运之门</strong>
      <p data-i18n="fortune_desc">11 systems, 8 languages. AI-powered.</p>
    </div>
    <span class="fortune-arrow">→</span>
  </a>
  
  <div class="fortune-tools">
    <a href="/fortune/bazi.html">🔮 八字算命</a>
    <a href="/fortune/tarot.html">🎴 塔罗占卜</a>
    <a href="/fortune/iching.html">☯️ 易经占卜</a>
    <a href="/fortune/zodiac.html">🪐 生肖运势</a>
    <a href="/fortune/xiaoliuren.html">🖐️ 找东西</a>
    <a href="/fortune/">+ 6 more →</a>
  </div>
</section>
```
**改动**: 
- 整合原来的 fortune gateway card + 热门命理工具标签为一体
- 去掉独立的 almanac 卡片（移到博客区）
- 使用 `h2` 语义标题

### ③ 算命文化博客摘要
```html
<section id="fortune-blog" class="section fortune-blog">
  <h2>📝 <span data-i18n="fortune_blog_head">Fortune Culture</span></h2>
  <p class="sec-sub" data-i18n="fortune_blog_sub">八字命理 · 星座解析 · 风水入门</p>
  
  <div class="blog-cards">
    <!-- 动态加载最新3-4篇博客 -->
    <div class="blog-card-placeholder" id="fortuneBlogCards">
      <p style="color:var(--muted);text-align:center">Loading...</p>
    </div>
  </div>
  
  <a href="/blog/" class="btn" data-i18n="blog_view_all">View All Posts →</a>
</section>
```
**改动**: 
- 新增区域，从 `/blog/` 目录或 JS 获取最新博客标题+摘要
- 每张卡片: 标题 + 日期 + 摘要（1-2行）
- 替代原来底部的 almanac+blog 双卡片区域

### ④ 在线工具 Online Tools (免费)
```html
<section id="tools" class="section">
  <h2>🛠️ <span data-i18n="tools_head">Free Online Tools</span></h2>
  <p class="sec-sub" data-i18n="tools_head_sub">Runs in your browser. No upload. No signup.</p>
  
  <div class="tool-grid-compact" id="freeToolGrid">
    <!-- 精选6-8个最常用工具，显示为紧凑图标网格 -->
    <!-- JS 从 I18N[lang].tools 取最常用的几个 -->
  </div>
  
  <details class="tools-expand">
    <summary data-i18n="tools_show_all">Show all 30+ tools →</summary>
    <div class="tool-grid" id="toolGridFull"><!-- 全部工具 --></div>
  </details>
</section>
```
**改动**: 
- 默认显示 6-8 个最常用工具（PDF 相关、JSON、QR Code 等）
- 使用 `<details>` 折叠其余工具
- 删除原来的 Online Convert 独立区域（合并到工具区作为其中几个卡片）
- 保留"在线转换"卡片（Word→PDF 等）放在免费工具网格中

### ⑤ 付费工具区 Premium Apps
```html
<section id="premium" class="section">
  <h2>💎 <span data-i18n="premium_head">Premium Apps</span></h2>
  <p class="sec-sub" data-i18n="premium_head_sub">Download, double-click, done. One-time purchase.</p>
  
  <div class="cat-tabs" id="catTabs">
    <button class="cat-tab active" onclick="showCat('all')">All</button>
    <button class="cat-tab" onclick="showCat('pdf')">📄 PDF</button>
    <button class="cat-tab" onclick="showCat('image')">🎨 Image</button>
    <button class="cat-tab" onclick="showCat('media')">🎬 Media</button>
    <button class="cat-tab" onclick="showCat('ecommerce')">🚀 E-Com</button>
    <button class="cat-tab" onclick="showCat('dev')">⚙️ Dev</button>
    <button class="cat-tab" onclick="showCat('utility')">📊 Utility</button>
    <button class="cat-tab bundle-tab" onclick="showCat('bundle')">🎁 Bundles</button>
  </div>
  
  <div id="appToolList"><!-- 从 products.json 加载，按分类筛选 --></div>
</section>
```
**改动**: 
- 从原 right-col（两列中的右列）移到独立 section
- 不再用左右两列布局，改为单列流式
- 产品从 `products.json` 加载，按 category 筛选

### ⑥ 职场博客入口
```html
<section id="work-blog" class="section work-blog-entry">
  <a href="/blog/" class="blog-entry-card">
    <span>📝</span>
    <div>
      <h2 data-i18n="work_blog_head">Workplace Blog</h2>
      <p data-i18n="work_blog_sub">办公效率 · 职场心得 · 工具教程 · 独立开发</p>
    </div>
    <span class="arrow">→</span>
  </a>
</section>
```
**改动**: 
- 简洁入口卡片，链接到 /blog/
- 覆盖原来的双卡片（almanac + blog）

### ⑦ Shop 入口
```html
<section id="shop-entry" class="section shop-entry">
  <a href="#" onclick="showPage('shop');return false" class="shop-entry-card">
    <span>🛒</span>
    <div>
      <h2 data-i18n="shop_entry_head">Shop — DIY & Gadgets</h2>
      <p data-i18n="shop_entry_sub">Electronics, desk accessories, tools for the modern office.</p>
    </div>
    <span class="arrow">→</span>
  </a>
</section>
```
**改动**: 
- 简洁入口卡片
- 点击触发 showPage('shop') 进入现有 Shop 子页面

### ⑧ 保留区域
- **Request Box** (提需求) — 保持不变
- **Footer** — 保持不变  
- **Sidebar** — 保持不变
- **Nav** — 保持不变

---

## 2. CSS 改动清单

### 需要新增的 CSS 类
```css
/* Hero CTA buttons */
.hero-cta { display:flex; gap:12px; justify-content:center; margin-top:20px; flex-wrap:wrap; }

/* Fortune Gateway 整合卡片 */
.fortune-hero-card { display:flex; align-items:center; gap:16px; padding:24px; background:linear-gradient(135deg,#1a1a2e,#16213e,#0f3460); border-radius:16px; text-decoration:none; color:#fff; transition:all .2s; }
.fortune-hero-card:hover { transform:translateY(-2px); box-shadow:0 8px 30px rgba(15,52,96,.4); }
.fortune-icon { font-size:2.5rem; }
.fortune-hero-text { flex:1; }
.fortune-hero-text strong { font-size:1.2rem; display:block; margin-bottom:6px; }
.fortune-hero-text p { font-size:.85rem; opacity:.85; }
.fortune-arrow { font-size:2rem; opacity:.5; }
.fortune-tools { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; }
.fortune-tools a { font-size:.75rem; padding:4px 10px; border:1px solid var(--border); border-radius:6px; text-decoration:none; color:var(--text); background:var(--surface); transition:all .15s; }
.fortune-tools a:hover { border-color:var(--accent); color:var(--accent); }

/* 博客卡片网格 */
.blog-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:14px; margin-bottom:16px; }
.blog-card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:20px; transition:all .2s; }
.blog-card:hover { border-color:var(--accent); transform:translateY(-2px); }
.blog-card h3 { font-size:.95rem; font-weight:600; margin-bottom:6px; }
.blog-card .date { font-size:.72rem; color:var(--muted); margin-bottom:8px; }
.blog-card .excerpt { font-size:.82rem; color:var(--muted); line-height:1.5; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }

/* 紧凑工具网格 */
.tool-grid-compact { display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:10px; }
.tool-card-compact { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:14px; text-align:center; cursor:pointer; transition:all .2s; }
.tool-card-compact:hover { border-color:var(--accent); transform:translateY(-1px); }
.tool-card-compact .icon { font-size:1.5rem; margin-bottom:6px; }
.tool-card-compact .name { font-size:.82rem; font-weight:500; }

/* details 展开折叠 */
.tools-expand { margin-top:12px; }
.tools-expand summary { cursor:pointer; color:var(--accent); font-size:.85rem; font-weight:500; padding:8px 0; }
.tools-expand summary:hover { color:var(--text); }

/* 入口卡片统一样式 */
.blog-entry-card, .shop-entry-card { display:flex; align-items:center; gap:16px; padding:24px; background:var(--surface); border:1px solid var(--border); border-radius:16px; text-decoration:none; color:var(--text); transition:all .2s; }
.blog-entry-card:hover, .shop-entry-card:hover { border-color:var(--accent); transform:translateY(-2px); box-shadow:0 2px 8px rgba(0,0,0,.06); }
.blog-entry-card span:first-child, .shop-entry-card span:first-child { font-size:2rem; }
.blog-entry-card .arrow, .shop-entry-card .arrow { font-size:1.5rem; color:var(--muted); }
```

### 需要修改的现有 CSS
- `.section` — 减小 padding，紧凑布局（`padding: 32px 20px` 替代部分 `48px`）
- `.hero` — 减小 padding-bottom
- 删除原来的 `section#online` 样式
- 删除原来的 Two-column 布局相关样式（`.right-col`, 两栏 grid）
- 移动端适配：`.tool-grid-compact` 在 600px 以下改为 2 列

---

## 3. JS 改动清单

### 需要新增的 JS 函数

1. **`loadFortuneBlogs()`**: 
   - 尝试 fetch `/blog/index.html` 或从 hardcoded 数据加载最新 3-4 篇博客标题和摘要
   - 渲染到 `#fortuneBlogCards`
   - 降级方案：用 hardcoded I18N 数据

2. **`renderCompactTools()`**: 
   - 从 `I18N[lang].tools` 取前 6 个最常用的工具（JSON, QR, Base64, UUID, Password, Count）
   - 渲染为 compact 卡片网格 `#freeToolGrid`
   - 其余工具放到 `#toolGridFull`（details 折叠区）

3. **修改 `showCat()`**: 
   - 保持现有逻辑不变，但容器改为 `#premium` 下的 `#appToolList`
   - 确保 products.json 的 fetch 在此处生效

4. **修改 `setLang()`**: 
   - 加上 `loadFortuneBlogs()` 和 `renderCompactTools()` 调用

### 需要删除的代码
- 删除 `right-col` 相关的布局 JS（如果有）
- 删除 almanac 卡片的内联样式和链接
- 删除原来的 blog 双卡片布局代码

### 保持不变
- `showPage()`, `showTool()`, `renderToolCards()`, `renderShop()` 等核心函数
- 全部 i18n 数据结构（只需新增少量 key）
- 订单 modal 逻辑
- 侧边栏逻辑
- uploadConvert 在线转换逻辑

---

## 4. SEO 增强清单

### P0 — 首页改版必须做
- [ ] **修改 `<title>`** → `Free Office Tools & Fortune Reading — PDF, JSON, QR | slowbuild`
- [ ] **修改 `<meta name="description">`** → 面向职场受众，提及 "office productivity, PDF converter, fortune reading, workplace tools"
- [ ] **添加 `og:image`** → 生成一张 1200×630 的首页 OG 图
- [ ] **添加 JSON-LD WebSite Schema**:
  ```json
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "slowbuild",
    "url": "https://www.slowbuild.top/",
    "description": "Free online tools and fortune reading for office workers.",
    "potentialAction": {
      "@type": "SearchAction",
      "target": "https://www.slowbuild.top/search?q={search_term_string}",
      "query-input": "required name=search_term_string"
    }
  }
  ```
- [ ] **添加 JSON-LD Organization Schema**
- [ ] **添加 JSON-LD ItemList Schema**（工具列表）
- [ ] **每个 `<section>` 用语义标签 + ID**（已在上方结构体现）

### P1 — 重要但可稍后
- [ ] **`<html lang>` 动态设置**（JS 已做 `document.documentElement.lang = l`）
- [ ] **BlogPosting Schema**（博客摘要区）
- [ ] **Product Schema**（Shop 入口区）
- [ ] **面包屑 BreadcrumbList Schema**

### P2 — 性能优化
- [ ] CSS 提取到外部文件（减少 HTML 体积 ~8KB）
- [ ] JS 提取到外部文件（减少 HTML 体积 ~150KB+）
- [ ] 添加 `<link rel="preload">` 关键资源
- [ ] 图片懒加载（`loading="lazy"`）

---

## 5. 文件改动范围

### 必须修改
| 文件 | 改动内容 |
|------|----------|
| `slowbuild/index.html` | 重写首页 HTML 结构 + CSS + JS（唯二改动文件） |

### 可能需要新增
| 文件 | 用途 |
|------|------|
| `slowbuild/blog/work-11.md` | （可选）新增一篇职场向博客占位 |
| `slowbuild/images/og-home.png` | OG 图片（如果不生成则用 emoji SVG） |

### 绝对不改
- `products.json` — 不动
- `server.py` — 不动
- `admin.html` — 不动
- `fortune.html` — 不动
- `almanac.html` — 不动
- `blog/` 目录现有文件 — 不动
- `robots.txt` / `sitemap.xml` — 不动
- `vercel.json` — 不动

---

## 6. 新增 i18n Keys

需要在 I18N['en'], I18N['zh-CN'], I18N['zh-TW'] 中新增以下 keys:

| Key | EN | ZH-CN |
|-----|-----|-------|
| `hero_fortune_btn` | 🔮 Try Fortune | 🔮 免费算命 |
| `hero_tools_btn` | 🛠️ Browse Tools | 🛠️ 浏览工具 |
| `fortune_head` | Fortune Gateway | 命运之门 |
| `fortune_head_sub` | Bazi · Tarot · Zodiac · I Ching — AI-powered | 八字·塔罗·星座·易经 — AI驱动 |
| `fortune_blog_head` | Fortune Culture | 命理文化 |
| `fortune_blog_sub` | Bazi guides · zodiac insights · feng shui tips | 八字入门·星座解析·风水知识 |
| `blog_view_all` | View All Posts → | 查看全部文章 → |
| `tools_head` | Free Online Tools | 免费在线工具 |
| `tools_head_sub` | Runs in your browser. No upload. No signup. | 浏览器本地运行，不上传，不注册 |
| `tools_show_all` | Show all 30+ tools → | 展开全部 30+ 工具 → |
| `premium_head` | Premium Apps | 高级工具 |
| `premium_head_sub` | Download, double-click, done. One purchase. | 下载→双击→直接用。一次购买。 |
| `work_blog_head` | Workplace Blog | 职场博客 |
| `work_blog_sub` | Productivity tips · career insights · indie dev | 办公效率·职场心得·独立开发 |
| `shop_entry_head` | Shop — DIY & Gadgets | 商店 — DIY 与电子产品 |
| `shop_entry_sub` | Desk accessories, electronics, tools for the office | 桌面配件、电子产品、办公神器 |

---

## 附录: 删除的区域

以下现有区域在改版中**移除**（功能合并到上方新区域）:

1. ~~独立的 `#online` Online Convert 区域~~ → 合并到免费工具网格
2. ~~底部 almanac + blog 双卡片~~ → 替换为算命博客摘要 + 职场博客入口
3. ~~Featured Tools 区域~~ → 合并到免费工具网格
4. ~~Two-column Tools + Premium EXE~~ → 改为免费工具 + 付费工具两个独立 section
5. ~~Hero 区域的 tags 标签行~~ → 删除，改为 CTA 按钮
6. ~~底部的 Ad placeholder~~ → 保留但移到 footer 上方
