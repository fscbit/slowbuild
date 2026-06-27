# SEO Audit Report — slowbuild.top 首页

**评估日期**: 2026-06-27  
**评估页面**: `index.html`  
**文件大小**: 209 KB (含全部 i18n + JS 内联)  
**目标受众**: 打工牛马（办公室白领、职场人）

---

## 综合评分: **47/100**

| 维度 | 得分 | 满分 | 状态 |
|------|------|------|------|
| Meta 标签 | 14 | 20 | 🟡 中等 |
| 结构化数据 | 0 | 20 | 🔴 严重缺失 |
| 标题层级 | 10 | 15 | 🟡 可改进 |
| 内容质量 | 8 | 15 | 🟡 偏弱 |
| 性能 | 5 | 15 | 🔴 需优化 |
| URL / 技术 | 10 | 15 | 🟡 可改进 |

---

## 1. Meta 标签分析

### ✅ 做得好的
- `title` 有英文关键词: "Free Online Tools — JSON Formatter..."
- `description` 存在，字数合理（~155字符）
- `keywords` 存在（虽然 Google 已不看重）
- OG 标签完整（title, description, url, type, site_name）
- Twitter Card 标签存在（summary_large_image）
- `canonical` 指向 https://www.slowbuild.top/
- `hreflang` 存在 en / x-default
- `robots`: index, follow

### ❌ 问题
1. **Title 不匹配目标受众**  
   当前: "Free micro tools, built slow" → 面向开发者/制作者  
   应有: 面向"办公室白领/职场效率"的关键词（如 "office tools", "workplace productivity", "打工效率工具"）
2. **缺少 `og:image`** —— Open Graph 图片对社交分享至关重要
3. **缺少 `twitter:image`** —— Twitter 卡片无图片
4. **Description 同样不匹配受众**  
   当前: "Free online tools for devs, writers, and makers" → devs? 不是目标用户  
   应有: 提及"职场效率"、"办公工具"、"office productivity"
5. **`<html lang="en">` 固定为 en**  
   但页面有中文内容。i18n SPA 单页应用 hreflang 指向同一 URL 无意义 —— Google 只能看到 en 版

---

## 2. 结构化数据（Schema.org）

### 🔴 完全缺失！

页面上 **没有任何 JSON-LD 或 Microdata 结构化数据**。这是最大的 SEO 漏洞。

**应该添加的 Schema 类型**:
- `WebSite` + `SearchAction` (站内搜索框标记)
- `Organization` (站点/作者信息)
- `ItemList` (工具列表 - 每个工具一个 `ListItem`)
- `BreadcrumbList` (面包屑导航)
- `FAQPage`（如有 FAQ 板块）
- `BlogPosting`（博客摘要部分）
- `Product`（Shop 商品）

**Google 富媒体搜索结果机会**: 零。结构化数据是获得 Rich Snippets 的唯一方式。

---

## 3. 标题层级分析

### ✅ 做的好的
- 有且仅有一个 `<h1>`（在 Hero 区域）
- 各板块使用 `<h2>` 作为主标题
- 工具卡片内使用 `<h3>`

### ❌ 问题
1. **部分区域使用内联样式替代语义标题**  
   例如"命运之门"入口使用 `<h2>` 但在 `<a>` 标签内，语义不清
2. **Fortune tools 列表无标题层级**  
   "🔮 热门命理工具"使用的是 `<p>` 加 `font-weight:700` 而非 `<h2>/<h3>`，搜索引擎无法理解这是子板块
3. **Featured Tools 区每个卡片用 `<strong>` 而非 `<h3>`**  
   语义化 HTML 对 SEO 和可访问性都很重要
4. **整体 h1-h6 层次**: h1 → h2 → h3，缺少 h4-h6 用于更深嵌套内容

---

## 4. 内容质量

### ❌ 问题
1. **首页英文内容严重偏向开发者**  
   "Free online tools for devs, writers, and makers" → 完全不是"打工牛马"的语言。没有出现 "office worker", "workplace", "productivity", "职场效率" 等关键词。
2. **关键词密度问题**  
   - "tool" 出现很多次（OK）
   - "fortune/算命/八字" 出现很多（OK）
   - 但缺少目标受众搜索的关键词（office tools, free PDF converter, workplace efficiency）
3. **正文可读文本量不足**  
   大量内容是链接、图标和按钮。Google 需要足够的多段落文本来理解页面主题。当前纯英文文本约 200-300 词，对于一个需要排名的首页来说太少。
4. **中文 SEO 关键词几乎为零**  
   Google 抓取 `<html lang="en">` 时看到的是英文版 i18n 内容。中文关键词如"在线工具"、"免费工具"、"办公效率"对搜索引擎不可见。
5. **i18n SPA 的 SEO 问题**  
   页面用 JS 动态切换语言，搜索引擎只会索引默认语言（en）。Google 可能完全看不到中文内容。

---

## 5. 性能分析

### ❌ 问题
1. **文件体积过大**: 209 KB  
   - 全部 CSS 内联（~8KB）  
   - 全部 i18n 数据（中/英/繁三种语言）内联在 JS 中（~80KB+）  
   - 全部工具渲染逻辑内联  
   - 推荐：首页 HTML 应 <50KB（含 CSS），JS 应外置且按需加载
2. **无资源压缩**：未使用 gzip/brotli 级别的优化
3. **无图片懒加载**：虽然没有大量图片，但 products.json 里的图片加载方式可以优化
4. **阻塞渲染**：大量内联 JS 在 `<head>` 后就开始，可能阻塞首屏渲染
5. **Google Core Web Vitals 风险**:
   - LCP (Largest Contentful Paint): 可能偏慢（全量渲染工具卡片）
   - CLS (Cumulative Layout Shift): 动态加载 products.json 会导致布局偏移
   - TTFB: 取决于服务器，代码层面无大问题

---

## 6. URL 结构与技术 SEO

### ✅ 做的好的
- `canonical` 正确
- `hreflang` 存在
- `robots.txt` 存在，允许全部爬取
- `sitemap.xml` 存在，覆盖主要页面
- HTTPS (通过 canonical 确认使用 https)

### ❌ 问题
1. **SPA Hash 路由问题**: 页面使用 `onclick="showPage('shop')"` 等 JS 切换视图，URL 不变。Google 无法索引"子页面"（About/Privacy/Shop）。每个子页面应该是独立 URL。
2. **hreflang 全部指向同一 URL**: `en`、`x-default` 都指向 `/`——但只有一个页面。Google 无法区分多语言版本的对应关系。
3. **工具页面 URL**: 点击工具后 `showTool('json')` 不改变 URL，每个工具页面都无法被独立索引。
4. **无 Breadcrumb（面包屑）**: 没有 `<nav aria-label="breadcrumb">` 或 `BreadcrumbList` 结构化数据。
5. **blog 目录存在但首页链接是 `/blog/`**: blog 内容页面是否有独立 URL 需要确认。
6. **缺少 HTML5 语义标签**: 未使用 `<main>`, `<article>`, `<section>`（用了 `<section>` 但有些是 `<div>`）
7. **缺少明确的 `<header>` 和 `<main>`**: `<nav>` 存在，但 `<header>` 和 `<main>` 是 SEO 最佳实践。

---

## 7. 改进清单（优先级排序）

### 🔴 P0 — 必须做
- [ ] **添加 JSON-LD 结构化数据**（WebSite + Organization + ItemList）
- [ ] **修改 Title/Description 面向职场受众**（加入 "office tools", "productivity", "workplace"）
- [ ] **添加 `og:image` 和 `twitter:image`**
- [ ] **将 HTML/CSS/JS 分离**（CSS 外置，JS 按需加载，减小首页体积到 <100KB）

### 🟡 P1 — 应该做
- [ ] 修复标题层级（h1/h2/h3/h4 语义正确）
- [ ] 首页增加至少 300-500 词的可读正文
- [ ] 工具列表区域添加 ItemList Schema
- [ ] 使用语义 HTML5 标签（`<main>`, `<article>`, `<header>`, `<footer>`）
- [ ] 每个工具页面用独立 URL（如 `/tools/json-formatter/`）而非 JS 路由

### 🟢 P2 — 可以做
- [ ] 处理多语言 SEO（独立 URL 如 `/zh/`, `/en/`）
- [ ] 为每个工具页面添加独立 meta + Schema
- [ ] 添加面包屑导航 + BreadcrumbList Schema
- [ ] 图片添加有意义的 alt 属性
- [ ] 使用 `<link rel="preload">` 优化关键资源
- [ ] 注册 Google Search Console + 提交 sitemap

---

## 8. 首页改版 SEO 必须要点

基于用户需求（面向打工牛马 / 算命+工具两大板块），改版时务必：

1. **Title 改为**: `Free Office & Productivity Tools | Fortune Reading | slowbuild`
2. **Description 改为**: 提及 "office workers, productivity tools, PDF converter, fortune reading, workplace efficiency"
3. **每个板块用 `<section>` + 语义标题**
4. **工具列表添加 `ItemList` JSON-LD**
5. **博客摘要区添加 `BlogPosting` JSON-LD**
6. **Shop 商品添加 `Product` JSON-LD**
7. **文件体积控制**: CSS 外置，JS 按需加载
8. **确保 h1 唯一且包含核心关键词**
