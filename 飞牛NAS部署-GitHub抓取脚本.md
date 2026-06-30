# GitHub 抓取脚本 — 部署到飞牛 FnOS NAS

> 替代 Win10 方案，NAS 24小时运行，定时任务更可靠

---

## 一、SSH 登录 NAS

用你电脑的终端（或 Putty）连接：

```bash
ssh 你的NAS用户名@你的NAS_IP地址
```

不知道 NAS IP 的话，在飞牛管理页面 → 系统设置 → 网络信息 里看。

---

## 二、安装 Python（如果没有）

```bash
# 检查是否已有 Python
python3 --version

# 如果没有，安装
sudo apt update
sudo apt install python3 python3-pip -y

# 安装依赖
pip3 install requests
```

---

## 三、上传脚本到 NAS

在 NAS 上创建目录：

```bash
mkdir -p /volume1/scripts/github-trending
```

**方法1：从电脑上传**

用飞牛的文件管理器 → 把 `github-trending-fetcher.py` 拖到 `/volume1/scripts/github-trending/`

**方法2：用 scp**
```bash
scp github-trending-fetcher.py 用户名@NAS_IP:/volume1/scripts/github-trending/
```

---

## 四、手动测试

```bash
cd /volume1/scripts/github-trending
python3 github-trending-fetcher.py
```

看到输出 `✅ 找到 X 个工具类项目` 就是成功了。

---

## 五、设置定时任务（cron）

```bash
crontab -e
```

如果提示选择编辑器，选 `nano`（最简单）。

在文件末尾加一行：

```bash
0 9 * * * cd /volume1/scripts/github-trending && python3 github-trending-fetcher.py >> /volume1/scripts/github-trending/cron.log 2>&1
```

意思：每天早上 9:00 运行脚本，日志写到 `cron.log`。

保存退出（nano: `Ctrl+O` 回车 → `Ctrl+X`）

追加 GitHub Token 的环境变量：

```bash
crontab -e
```

改成：
```bash
0 9 * * * export GITHUB_TOKEN=你的token && cd /volume1/scripts/github-trending && python3 github-trending-fetcher.py >> /volume1/scripts/github-trending/cron.log 2>&1
```

---

## 六、查看抓取结果

在飞牛文件管理器里打开：

```
/volume1/scripts/github-trending/github-trending/products.json
```

每行一个产品数据，挑感兴趣的上架。

---

## 七、看运行日志

```bash
# 查看最新日志
tail -50 /volume1/scripts/github-trending/cron.log

# 实时看
tail -f /volume1/scripts/github-trending/cron.log
```

---

## 八、可选：把结果同步到 Win10

如果后台 `admin.html` 在 Win10 上，需要把 `products.json` 同步过去。

**方法1：用飞牛共享文件夹**

Win10 映射 NAS 共享文件夹为网络驱动器，直接读 `/volume1/scripts/github-trending/github-trending/products.json`

**方法2：用 Python 起个简单 HTTP 服务**

在 NAS 上：
```bash
cd /volume1/scripts/github-trending/github-trending
python3 -m http.server 8899 &
```

然后在 Win10 浏览器访问：`http://NAS_IP:8899/products.json`

---

## 九、完整命令速查

```bash
# 1. 安装
sudo apt update && sudo apt install python3 python3-pip -y
pip3 install requests

# 2. 创建目录
mkdir -p /volume1/scripts/github-trending

# 3. 上传脚本（复制文件到 /volume1/scripts/github-trending/）

# 4. 测试运行
cd /volume1/scripts/github-trending
python3 github-trending-fetcher.py

# 5. 设置定时
crontab -e
# 加入: 0 9 * * * cd /volume1/scripts/github-trending && python3 github-trending-fetcher.py >> cron.log 2>&1

# 6. 查看结果
cat github-trending/products.json
```

---

📅 2026-06-30 | 有问题截图给我
