# ============================================
# slowbuild Tunnel 自动更新脚本
# 
# 首次使用请先设置 GitHub Token:
#   .\update_tunnel.ps1 -Token "ghp_xxx"    (推荐)
#   或者设置环境变量: $env:GH_TOKEN = "ghp_xxx"
#
# 用法:
#   .\update_tunnel.ps1              # 自动启动 cloudflared + 抓取 URL
#   .\update_tunnel.ps1 -Url "xxx"   # 手动指定 URL
# ============================================

param(
    [string]$Url = "",
    [string]$Token = "",
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"

# --- GitHub Token ---
if ($Token) {
    $GH_TOKEN = $Token
} elseif ($env:GH_TOKEN) {
    $GH_TOKEN = $env:GH_TOKEN
} else {
    Write-Host "❌ 未设置 GitHub Token！" -ForegroundColor Red
    Write-Host ""
    Write-Host "首次使用请先获取 Token：" -ForegroundColor Yellow
    Write-Host "  1. 打开 https://github.com/settings/tokens" -ForegroundColor Gray
    Write-Host "  2. 点击 'Generate new token (classic)'" -ForegroundColor Gray
    Write-Host "  3. 勾选 'repo' 权限，生成后复制" -ForegroundColor Gray
    Write-Host "  4. 运行: .\update_tunnel.ps1 -Token 'ghp_你的token'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "或者设置环境变量（一劳永逸）：" -ForegroundColor Yellow
    Write-Host "  [System.Environment]::SetEnvironmentVariable('GH_TOKEN','ghp_xxx','User')" -ForegroundColor Gray
    exit 1
}

$REPO = "fscbit/slowbuild"
$API = "https://api.github.com/repos/$REPO/contents"
$CLOUDFLARED_EXE = "cloudflared.exe"
$BRANCH = "master"

$headers = @{
    "Authorization" = "token $GH_TOKEN"
    "Accept"        = "application/vnd.github+json"
}

Write-Host ""
Write-Host "=== slowbuild Tunnel 自动更新 ===" -ForegroundColor Cyan

# --- 1. 获取 Tunnel URL ---
if ($Url) {
    Write-Host "[1/4] 使用手动指定的 URL: $Url" -ForegroundColor Yellow
} else {
    Write-Host "[1/4] 启动 cloudflared tunnel..." -ForegroundColor Yellow

    # 杀掉旧的 cloudflared
    Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1

    $logFile = "$env:TEMP\cloudflared_slowbuild.log"
    Remove-Item $logFile -ErrorAction SilentlyContinue

    $proc = Start-Process -FilePath $CLOUDFLARED_EXE `
        -ArgumentList "tunnel", "--url", "http://localhost:$Port" `
        -NoNewWindow -RedirectStandardOutput $logFile -PassThru

    Write-Host "  等待 tunnel 就绪（最多 60 秒）..." -ForegroundColor Gray
    $timeout = 60
    $elapsed = 0
    while ($elapsed -lt $timeout) {
        Start-Sleep -Seconds 3
        $elapsed += 3
        if (Test-Path $logFile) {
            $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
            if ($content -match 'https://([a-z\-]+\.trycloudflare\.com)') {
                $Url = $matches[0]
                Write-Host "  ✅ $Url" -ForegroundColor Green
                break
            }
        }
    }

    if (-not $Url) {
        Write-Host "❌ 超时！60 秒内未检测到 tunnel URL" -ForegroundColor Red
        Write-Host "   日志文件: $logFile"
        exit 1
    }
}

# --- 函数：更新单个文件 ---
function Update-File($path, $description) {
    Write-Host "[ ] 更新 $description..." -NoNewline
    
    try {
        # 获取当前文件
        $resp = Invoke-RestMethod -Uri "$API/$path`?ref=$BRANCH" -Headers $headers
        $oldContent = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($resp.content))
        $fileSha = $resp.sha

        # 替换 BACKEND URL
        $newContent = $oldContent -replace "var BACKEND\s*=\s*'[^']*'", "var BACKEND = '$Url'"

        if ($oldContent -eq $newContent) {
            Write-Host "`r[=] $description 无需更新（URL 相同）" -ForegroundColor Gray
            return
        }

        $newBase64 = [System.Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($newContent))
        $body = @{ message = "🔧 update backend: $Url"; content = $newBase64; sha = $fileSha; branch = $BRANCH } | ConvertTo-Json
        
        Invoke-RestMethod -Uri "$API/$path" -Method Put -Headers $headers -Body $body -ContentType "application/json" | Out-Null
        Write-Host "`r[✓] $description 已更新" -ForegroundColor Green
    } catch {
        Write-Host "`r[✗] $description 失败: $_" -ForegroundColor Red
        throw
    }
}

# --- 2-3. 更新两个 HTML 文件 ---
Update-File "index.html" "index.html"
Update-File "fortune.html" "fortune.html"

# --- 4. 完成 ---
Write-Host ""
Write-Host "🎉 完成！Vercel 将自动部署（约 30 秒）" -ForegroundColor Green
Write-Host "   访问 https://slowbuild.top 测试在线转换功能" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 cloudflared 已在后台运行，不要关闭" -ForegroundColor Gray
Write-Host "   下次 tunnel 断开重连，重新运行此脚本即可" -ForegroundColor Gray
