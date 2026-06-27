# 🔍 Slowbuild 工具挖掘报告

> 生成时间：2026-06-27  
> 目标：为 slowbuild.top 挖掘可封装为 EXE 或提供在线服务的 GitHub 开源工具  
> 数据来源：GitHub API（实时搜索 + 仓库详情）

---

## 📊 调研方法

通过 GitHub REST API 无 token 公开搜索，覆盖以下维度：
- 按 stars 排序的仓库搜索（分语言：Python/Go/TypeScript/JavaScript）
- 按创建时间过滤（2023-2026 新建项目优先）
- 关键词搜索：pdf、image、converter、cli、tool、ocr、markdown、video 等
- 逐个验证仓库详情（语言、topics、活跃度）

---

## 🏆 分类推荐

### 1. PDF 工具类 — 需求最大、竞争最激烈

| 项目 | Stars | 语言 | CLI | 封装难度 | 在线服务 | 评级 |
|------|-------|------|-----|----------|----------|------|
| [markitdown](https://github.com/microsoft/markitdown) | ⭐159K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 S |
| [MinerU](https://github.com/opendatalab/MinerU) | ⭐70K | Python | ✅ | ⭐⭐ 中等 | ✅ | 🟢 A+ |
| [Umi-OCR](https://github.com/hiroi-sora/Umi-OCR) | ⭐45K | Python | ✅ | ⭐⭐ 中等 | ❌ 需GUI | 🟢 A+ |
| [marker](https://github.com/datalab-to/marker) | ⭐36K | Python | ✅ | ⭐⭐ 中等 | ✅ | 🟢 A |
| [PDFMathTranslate](https://github.com/PDFMathTranslate/PDFMathTranslate) | ⭐35K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 A |
| [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | ⭐34K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 A |

**🥇 首推：markitdown**
- 微软官方出品，159K stars
- Python 纯血，`pip install markitdown` 即可
- 支持 Office/PDF/图片/音频/HTML → Markdown 转换
- CLI 一行命令：`markitdown input.pdf > output.md`
- PyInstaller 封装极简，依赖少
- 可做 Web 版文件转 Markdown 在线服务

**🥈 次推：OCRmyPDF**
- 33K stars，成熟稳定
- 核心依赖 tesseract（需打包），但 CLI 极其简洁
- 功能清晰：给扫描 PDF 加 OCR 文字层
- 刚需场景多（办公、档案数字化）

**🥉 惊喜：PDFMathTranslate**
- 35K stars，EMNLP 2025 论文
- PDF 科学论文翻译，保留排版格式
- Python CLI，打包简单
- 学术用户刚需，付费意愿高

**⚠️ 排除：**
- Stirling-PDF（84K stars）：Java 项目，需 Docker，太重
- PaddleOCR（84K stars）：需要 GPU 加速才有效果
- docling（62K stars）：library 为主，非独立工具

---

### 2. 图片处理类 — 高频刚需、封装收益大

| 项目 | Stars | 语言 | CLI | 封装难度 | 在线服务 | 评级 |
|------|-------|------|-----|----------|----------|------|
| [rembg](https://github.com/danielgatis/rembg) | ⭐23K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 S |
| [IOPaint](https://github.com/Sanster/IOPaint) | ⭐23K | Python | ✅ | ⭐⭐ 中等 | ✅ | 🟢 A |
| [Final2x](https://github.com/EutropicAI/Final2x) | ⭐7.2K | TypeScript | ✅ | ⭐⭐ 中等 | ✅ | 🟢 A- |
| [gowall](https://github.com/Achno/gowall) | ⭐2.2K | Go | ✅ | ⭐ 极易 | ✅ | 🟢 B+ |
| [ascii-image-converter](https://github.com/TheZoraiz/ascii-image-converter) | ⭐3.4K | Go | ✅ | ⭐ 极易 | ✅ | 🟢 B |

**🥇 首推：rembg**
- 23K stars，背景去除工具
- CLI 极简：`rembg i input.jpg output.png`
- `pip install rembg`，纯 Python，依赖少
- EXE 封装后就是"一键抠图神器"
- 可做在线抠图 API 服务（按调用量收费）

**🥈 次推：gowall**
- Go 语言编译后单文件可执行，天然跨平台
- 功能丰富：调色板转换、图片压缩、超分、格式转换
- 2.2K stars 但增长快，竞争少
- 直接 `go build` → exe，零依赖

**🥉 IOPaint**
- 23K stars，AI 图片修复/去水印
- 需要 PyTorch（~2GB），但可以打包瘦身版
- 功能独特，市场上同类产品少

**⚠️ 排除：**
- ImageMagick（⭐16.8K，C 语言，已有官方 Windows 版）
- CVAT（⭐16K，需 GPU，太重）
- labelImg（⭐25K，标注工具，受众窄）

---

### 3. 文件转换类 — 万能工具箱定位

| 项目 | Stars | 语言 | CLI | 封装难度 | 在线服务 | 评级 |
|------|-------|------|-----|----------|----------|------|
| [Pandoc](https://github.com/jgm/pandoc) | ⭐45K | Haskell | ✅ | ❌ 已有二进制 | ✅ | 🟢 A |
| [ConvertX](https://github.com/C4illin/ConvertX) | ⭐17K | TypeScript | ❌ Web | ⭐⭐⭐ 重 | ✅ | 🟡 B |
| [VERT](https://github.com/VERT-sh/VERT) | ⭐15K | Svelte | ❌ Web | ⭐⭐⭐ 重 | ✅ | 🟡 B |
| [transmute](https://github.com/transmute-app/transmute) | ⭐1K | Python | ❌ Web | ⭐⭐ 中等 | ✅ | 🟢 B+ |
| [kcc](https://github.com/ciromattia/kcc) | ⭐5.3K | Python | ✅ | ⭐ 极易 | ❌ | 🟢 B+ |
| [kokoro-tts](https://github.com/nazdridoy/kokoro-tts) | ⭐1.6K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 B+ |

**🥇 首推：kcc（Kindle Comic Converter）**
- 5.3K stars，漫画/图片→电子书格式转换
- Python CLI，打包后就是独立漫画转换器
- 用户群清晰（漫画爱好者），商业潜力好

**🥈 kokoro-tts**
- 1.6K stars，CLI 文字转语音
- 支持多种语言和声音混合
- Python CLI，`kokoro "hello" -o output.wav`
- 可封装为"文本转语音 EXE"
- TTS 是热门赛道，API 化可按 token 收费

**🥉 VERT / ConvertX**
- 在线文件转换器，自托管方案
- 适合直接部署为 slowbuild 的子服务
- 而非封装为 EXE

**⚠️ 排除：**
- Pandoc：Haskell 编写，已有官方 Windows 安装包，没必要重新打包

---

### 4. 文本/数据处理类 — 开发者 + 普通用户双受众

| 项目 | Stars | 语言 | CLI | 封装难度 | 在线服务 | 评级 |
|------|-------|------|-----|----------|----------|------|
| [shell_gpt](https://github.com/TheR1D/shell_gpt) | ⭐12K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 A |
| [marker](https://github.com/datalab-to/marker) | ⭐36K | Python | ✅ | ⭐⭐ 中等 | ✅ | 🟢 A |
| [markitdown](https://github.com/microsoft/markitdown) | ⭐159K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 S |
| [docutranslate](https://github.com/xunbu/docutranslate) | ⭐1.1K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 B+ |
| [abogen](https://github.com/denizsafak/abogen) | ⭐5K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 B+ |

**🥇 首推：markitdown（已在 PDF 类中推荐）**
- 跨分类最强工具，既是 PDF 工具也是文件转换器

**🥈 次推：docutranslate**
- 1.1K stars，文档翻译
- 支持 pdf/word/excel/json/epub/srt 多格式
- Python CLI，打包简单
- 文档翻译是高频需求

**🥉 shell_gpt**
- 12K stars，终端 AI 助手
- 需要 API key（OpenAI/Ollama），适合工具站提供"配置版"
- 可预配置为"本地 AI 助手 EXE"

---

### 5. 开发者工具类 — 极客受众、口碑传播强

| 项目 | Stars | 语言 | CLI | 封装难度 | 在线服务 | 评级 |
|------|-------|------|-----|----------|----------|------|
| [dive](https://github.com/wagoodman/dive) | ⭐54K | Go | ✅ | ⭐ 极易 | ❌ | 🟢 A+ |
| [syft](https://github.com/anchore/syft) | ⭐9.2K | Go | ✅ | ⭐ 极易 | ❌ | 🟢 A |
| [ascii-image-converter](https://github.com/TheZoraiz/ascii-image-converter) | ⭐3.4K | Go | ✅ | ⭐ 极易 | ✅ | 🟢 B |
| [Final2x](https://github.com/EutropicAI/Final2x) | ⭐7.2K | TypeScript | ✅ | ⭐⭐ 中等 | ✅ | 🟢 A- |

**🥇 首推：dive**
- 54K stars，Docker 镜像层级分析
- Go 编译后单文件，可直接分发
- 虽然是开发者工具，但知名度极高
- 可以作为 slowbuild 的"引流神器"

**🥈 syft**
- 9.2K stars，软件物料清单(SBOM)生成
- Go 单文件，CLI 一行命令
- 企业安全合规刚需

---

### 6. 效率/办公类 — 最大众、付费意愿高

| 项目 | Stars | 语言 | CLI | 封装难度 | 在线服务 | 评级 |
|------|-------|------|-----|----------|----------|------|
| [VideoCaptioner](https://github.com/WEIFENG2333/VideoCaptioner) | ⭐15K | Python | ✅ | ⭐⭐ 中等 | ✅ | 🟢 A |
| [video-subtitle-remover](https://github.com/YaoFANGUK/video-subtitle-remover) | ⭐11.5K | Python | ✅ | ⭐⭐ 中等 | ✅ | 🟢 A |
| [abogen](https://github.com/denizsafak/abogen) | ⭐5K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 B+ |
| [AutoSubSync](https://github.com/denizsafak/AutoSubSync) | ⭐1.1K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 B+ |
| [kokoro-tts](https://github.com/nazdridoy/kokoro-tts) | ⭐1.6K | Python | ✅ | ⭐ 极易 | ✅ | 🟢 B+ |

**🥇 首推：VideoCaptioner**
- 15K stars，AI 字幕全流程工具
- 视频→字幕生成、断句、校正、翻译
- CLI 模式可提取，封装为"视频字幕助手 EXE"
- 短视频创作者刚需，付费意愿强

**🥈 次推：video-subtitle-remover**
- 11.5K stars，去硬字幕/去水印
- 纯本地运行，无需 API
- 功能独特，市面上少有替代品
- 封装后就是"一键去水印工具"

**🥉 abogen**
- 5K stars，电子书→有声书
- 支持 EPUB/PDF/TXT → 音频
- Python CLI，打包简单
- "文字转有声书"产品定位清晰

---

## 📈 增长趋势观察（2025-2026 新建热门）

| 项目 | Stars | 创建 | 月均增长 | 分析 |
|------|-------|------|----------|------|
| markitdown | 159K | 2024-12 | ~22K/月 | 🔥 微软出品，持续爆火 |
| MinerU | 70K | 2024-07 | ~3K/月 | 稳定增长 |
| marker | 36K | 2024-03 | ~1.5K/月 | 稳定的 PDF 工具 |
| PDFMathTranslate | 35K | 2025-01 | ~2K/月 | EMNLP 2025 论文带火 |
| transmute | 1K | 2025-06 | ~200/月 | 新项目，快速增长中 |
| kokoro-tts | 1.6K | 2025-03 | ~100/月 | 稳定增长 |

---

## 🎯 封装优先级排序

基于 "封装难度 × 用户需求 × 商业潜力" 三维评分：

| 优先级 | 项目 | 理由 |
|--------|------|------|
| 🔴 P0 | **markitdown** | 159K stars，微软背书，Python一行封装，文件转Markdown万能工具 |
| 🔴 P0 | **rembg** | 23K stars，一键抠图，CLI极简，封装后即成产品 |
| 🟠 P1 | **kokoro-tts** | TTS赛道热，CLI极简，Python易封装，可做在线API |
| 🟠 P1 | **kcc** | 漫画转电子书，用户群明确，Python CLI简单 |
| 🟠 P1 | **PDFMathTranslate** | 35K stars，学术用户付费意愿高 |
| 🟡 P2 | **VideoCaptioner** | 15K stars，短视频创作刚需，封装稍复杂但价值大 |
| 🟡 P2 | **video-subtitle-remover** | 11.5K stars，独特功能，去水印刚需 |
| 🟡 P2 | **OCRmyPDF** | 34K stars，稳定成熟，依赖tesseract需处理 |
| 🟢 P3 | **dive** | 54K stars，Go单文件，流量引流神器 |
| 🟢 P3 | **gowall** | 2.2K stars，Go编译即用，竞争少 |
| 🟢 P3 | **docutranslate** | 1.1K stars，文档翻译，增长空间大 |

---

## 🔧 封装建议

### 方案 A：PyInstaller 打包 Python 工具
```bash
# 适合 markitdown, rembg, kokoro-tts 等
pip install pyinstaller
pyinstaller --onefile --name "tool-name" cli.py
```

### 方案 B：Go 编译
```bash
GOOS=windows GOARCH=amd64 go build -o tool.exe
```
✅ 单文件、体积小、启动快 — 适合 dive, syft, gowall, ascii-image-converter

### 方案 C：Node.js pkg 打包
```bash
npm install -g pkg
pkg cli.js --targets node18-win-x64 -o tool.exe
```

### 方案 D：在线服务（Web 版）
适合 markitdown, rembg, kokoro-tts, ConvertX — 部署到 VM/NAS 提供 Web 服务

---

## 🚀 立即行动

1. **本周：封装 markitdown → markitdown.exe**
2. **本周：封装 rembg → bgremover.exe**
3. **下周：封装 kokoro-tts → kokoro-tts.exe**
4. **持续：运行 github_scout.py 监控新工具**

---

*报告由 subagent:tool-scout 自动生成 | slowbuild.top 工具挖掘系统*
