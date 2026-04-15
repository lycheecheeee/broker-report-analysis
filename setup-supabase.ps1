# Auto setup Supabase environment variables
Write-Host "Setting up Supabase environment variables..." -ForegroundColor Cyan

# Set SUPABASE_KEY
$sbKey = "sb_publishable_KT7L8opXmN7g1Dc1pGtZqA_0WskH5Ot"
$sbKey | vercel env add SUPABASE_KEY production --yes

Write-Host "✅ SUPABASE_KEY set successfully" -ForegroundColor Green

# Redeploy
Write-Host "Redeploying to Vercel..." -ForegroundColor Yellow
vercel --prod

Write-Host "Done!" -ForegroundColor Green
