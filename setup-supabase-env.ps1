# ============================================================================
# Supabase 環境變數自動化設置腳本
# 用途：自動配置 Vercel 環境變數並重新部署
# ============================================================================

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Supabase 環境變數自動化設置工具" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 檢查 vercel CLI 是否已安裝
Write-Host "[1/5] 檢查 Vercel CLI..." -ForegroundColor Yellow
try {
    $vercelVersion = vercel --version 2>&1
    Write-Host "✅ Vercel CLI 已安裝: $vercelVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Vercel CLI 未安裝" -ForegroundColor Red
    Write-Host "請先運行: npm install -g vercel" -ForegroundColor Yellow
    exit 1
}

# 提示用戶輸入 Supabase 憑證
Write-Host ""
Write-Host "[2/5] 請輸入 Supabase 憑證" -ForegroundColor Yellow
Write-Host "提示：可以在 https://supabase.com/dashboard → Settings → API 找到" -ForegroundColor Gray
Write-Host ""

$supabaseUrl = Read-Host "Supabase Project URL (例如: https://xxx.supabase.co)"
$supabaseKey = Read-Host "Supabase Service Role Key (長約 200+ 字符)"

# 驗證輸入
if ([string]::IsNullOrWhiteSpace($supabaseUrl) -or [string]::IsNullOrWhiteSpace($supabaseKey)) {
    Write-Host "❌ 錯誤：URL 和 Key 不能為空" -ForegroundColor Red
    exit 1
}

if (-not $supabaseUrl.StartsWith("https://")) {
    Write-Host "⚠️  警告：URL 應該以 https:// 開頭" -ForegroundColor Yellow
}

if ($supabaseKey.Length -lt 50) {
    Write-Host "⚠️  警告：Service Role Key 通常長度超過 200 字符，請確認使用的是 service_role key 而非 anon key" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[3/5] 設置 Vercel 環境變數..." -ForegroundColor Yellow

# 設置 SUPABASE_URL
Write-Host "  → 設置 SUPABASE_URL..." -ForegroundColor Gray
$sbUrlEncoded = [System.Web.HttpUtility]::UrlEncode($supabaseUrl)
echo $supabaseUrl | vercel env add SUPABASE_URL production --yes 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ SUPABASE_URL 設置成功" -ForegroundColor Green
} else {
    Write-Host "  ❌ SUPABASE_URL 設置失敗" -ForegroundColor Red
    exit 1
}

# 設置 SUPABASE_KEY
Write-Host "  → 設置 SUPABASE_KEY..." -ForegroundColor Gray
echo $supabaseKey | vercel env add SUPABASE_KEY production --yes 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✅ SUPABASE_KEY 設置成功" -ForegroundColor Green
} else {
    Write-Host "  ❌ SUPABASE_KEY 設置失敗" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[4/5] 提交代碼到 GitHub..." -ForegroundColor Yellow
git add -A
git commit -m "chore: 配置 Supabase 環境變數自動化腳本" 2>&1 | Out-Null
git push origin master 2>&1 | Out-Null
Write-Host "✅ 代碼已推送到 GitHub" -ForegroundColor Green

Write-Host ""
Write-Host "[5/5] 重新部署到 Vercel..." -ForegroundColor Yellow
Write-Host "這可能需要 30-60 秒..." -ForegroundColor Gray
vercel --prod --yes

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  ✅ 設置完成！" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "1. 在 Supabase SQL Editor 中執行建表 SQL（見 setup-supabase.sql）" -ForegroundColor White
Write-Host "2. 訪問儀表板並掃描 PDF 文件" -ForegroundColor White
Write-Host "3. 運行 python test_charts.py 驗證圖表功能" -ForegroundColor White
Write-Host ""
