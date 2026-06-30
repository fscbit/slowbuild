# GitHub 热门项目自动抓取 — 安装上架完整指南

> 自动抓取 GitHub 高星标/高增长工具项目 → 生成商品数据 → 上架到 slowbuild 后台

---

## 一、环境准备（只做一次）

### 1.1 安装 Python

到 `python.org` 下载 Python 3.12，安装时**勾选** "Add Python to PATH"。

安装完验证：
```
Win+R → 输入 cmd → 回车
输入: python --version
```
应该显示 `Python 3.12.x`

### 1.2 安装依赖

打开 cmd，输入：
```
pip install requests
```

### 1.3 (可选) 申请 GitHub Token

不用 Token 也能用，但加了能多抓 10 倍数据：
1. 打开 `github.com` → 右上角头像 → Settings
2. 左边 Developer settings → Personal access tokens → Tokens (classic)
3. Generate new token → 勾选 `public_repo` → 生成
4. 复制 token（只显示一次）

---

## 二、下载脚本

脚本文件：`github-trending-fetcher.py`

放在 Win10 虚拟机上，比如 `C:\slowbuild\scripts\github-trending-fetcher.py`

---

## 三、运行脚本

### 手动运行

打开 cmd：
```
cd C:\slowbuild\scripts
python github-trending-fetcher.py
```

输出示例：
```
🚀 GitHub 热门项目抓取器 - 2026-06-30 10:42
=================================================
✅ 找到 2 个工具类项目

#    项目          语言         ⭐       📈/天
1    wloc          JavaScript  1528     254.7
2    torlink       TypeScript  700      175.0

📁 产品数据已保存: github-trending/products.json
```

### 使用 Token 运行（可选，抓更多）

```
set GITHUB_TOKEN=你的token
python github-trending-fetcher.py
```

---

## 四、设置定时自动运行

### 方法：Windows 任务计划程序

1. Win+R → 输入 `taskschd.msc` → 回车
2. 右边 "创建基本任务"
3. 名称：`GitHub Trending Fetcher`
4. 触发器：**每天**
5. 时间：上午 9:00
6. 操作：启动程序
   - 程序：`python`
   - 参数：`C:\slowbuild\scripts\github-trending-fetcher.py`
   - 起始于：`C:\slowbuild\scripts`
7. 完成

**这样每天早上 9 点自动抓一次，结果保存在 `C:\slowbuild\scripts\github-trending\products.json`**

---

## 五、查看抓取结果

运行后在 `github-trending/` 文件夹里会生成：

| 文件 | 说明 |
|------|------|
| `products.json` | 最新一次抓取的**产品格式**数据（可直接参考上架） |
| `trending_20260630_1042.json` | 完整报告（含原始 GitHub 数据） |

---

## 六、如何上架到 slowbuild 后台

### 6.1 打开后台

浏览器打开：`slowbuild.top/admin.html`

### 6.2 连接后端

顶栏输入你的 Win10 虚拟机后端地址，点「测试连接」变绿。

我的后端在Win10上运行：
```
http://localhost:5000
```

### 6.3 添加数字产品

**方法一：手动添加（推荐，每抓到一个就加）**

1. 左边点 📦 **商品管理** → 点 **➕ 添加商品**
2. 类型选：**数字产品**
3. 按抓取结果填写：

| 表单字段 | 填什么 |
|---------|--------|
| 商品 ID | 用脚本生成的 id，如 `github-wloc` |
| 商品名 EN | 项目名，如 `wloc` |
| 商品名 简体 | `wloc (GitHub 1528⭐)` |
| 价格 USD | `4.99` |
| 图片路径 | 留空（显示占位图标） |
| 描述 EN | 复制 `products.json` 里的 `desc.en` |
| 描述 简体 | 复制 `products.json` 里的 `desc.zh-CN` |
| 规格说明 | 复制 `products.json` 里的 `specs.zh-CN`，逐行粘贴 |
| 物流说明 EN | `📦 Instant digital delivery` |
| 物流说明 简体 | `📦 即时数字交付` |

**方法二：快速模板**

点 **📋 快速模板** 按钮 → 自动填好数字产品通用字段 → 你只改名字和价格

### 6.4 保存后验证

- 保存 → 退回商品列表 → 点 🔄 刷新
- 打开 `slowbuild.top` → 滚动到 Shop 区域 → 应该能看到新上架的商品

---

## 七、数字产品定价建议

| 项目热度 | 建议价格 |
|---------|---------|
| 100-500 ⭐ | $2.99 |
| 500-2000 ⭐ | $4.99 |
| 2000-5000 ⭐ | $7.99 |
| 5000-10000 ⭐ | $9.99 |

> 价格在脚本的 `generate_products()` 函数里改，默认 `$4.99`

---

## 八、自定义抓取条件

编辑脚本开头的配置：

```python
MAX_RESULTS = 20      # 每次最多抓几个
MIN_STARS = 50        # 最少星标数
MAX_STARS = 10000     # 最多星标数（太出名不要）
```

修改关键词：
```python
KEYWORDS = ["tool", "cli", "app", "generator", "converter", ...]
```

---

## 九、脚本输出示例

`products.json` 内容示例：
```json
[
  {
    "id": "github-wloc",
    "type": "digital",
    "price": 4.99,
    "name": {
      "en": "wloc",
      "zh-CN": "wloc (GitHub 1528⭐)"
    },
    "desc": {
      "en": "Wi-Fi location triangulation... ⭐ 1528 stars | 📈 254.7/day",
      "zh-CN": "Wi-Fi 定位三角测量... ⭐ 1528 星标 | 📈 日增 254.7 星"
    },
    ...
  }
]
```

---

## 十、常见问题

| 问题 | 解决 |
|------|------|
| `pip: command not found` | Python 没装或没加 PATH，重装勾选 Add to PATH |
| `requests module not found` | 运行 `pip install requests` |
| `API 限流` | 申请 GitHub Token 再跑 |
| 抓不到新项目 | 调低 `MIN_STARS` 到 10 |
| 后台连不上 | 检查 Win10 后端是否在运行 |

---

📅 版本：2026-06-30

### 💡 关键提醒

**这个脚本的价值是帮你发现新项目，不是自动上架。**
- 跑完后看 `products.json`
- 挑你觉得有用的项目
- 手动去后台添加上架
- 如果项目有现成的 EXE 就附上 EXE 下载链接，没有就附 GitHub 地址
