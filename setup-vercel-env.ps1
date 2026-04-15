# Vercel Environment Variables Setup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setting up Vercel Environment Variables" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$envVars = @{
    "NVIDIA_API_KEY" = "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"
    "OPENROUTER_API_KEY" = "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"
    "NVIDIA_IMAGE_API_KEY" = "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"
    "GOOGLE_DRIVE_FOLDER_ID" = "1iTngyUVgE7suUZ9ChA1QZhyVr6bGK5VH"
    "ADMIN_USERNAME" = "lychee"
    "ADMIN_PASSWORD" = "lycheechee2026"
    "SECRET_KEY" = "tencent-broker-analysis-secret-key-2026"
    "DATABASE_URL" = "broker_analysis.db"
    "FLASK_ENV" = "production"
}

$i = 1
$total = $envVars.Count

foreach ($key in $envVars.Keys) {
    $value = $envVars[$key]
    Write-Host "[$i/$total] Setting $key..." -ForegroundColor Yellow
    
    # Use echo to pipe the value to vercel env add
    $value | vercel env add $key production --yes
    
    $i++
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "All environment variables set!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Redeploying to Vercel..." -ForegroundColor Cyan
vercel --prod

Write-Host ""
Write-Host "Done! Visit: https://broker-report-analysis.vercel.app" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"
