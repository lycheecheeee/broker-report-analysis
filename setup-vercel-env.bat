@echo off
chcp 65001 >nul
echo ========================================
echo Setting up Vercel Environment Variables
echo ========================================
echo.
echo This will set the following variables:
echo   - NVIDIA_API_KEY
echo   - OPENROUTER_API_KEY
echo   - NVIDIA_IMAGE_API_KEY
echo   - GOOGLE_DRIVE_FOLDER_ID
echo   - ADMIN_USERNAME
echo   - ADMIN_PASSWORD
echo   - SECRET_KEY
echo   - DATABASE_URL
echo   - FLASK_ENV
echo.
echo Press Ctrl+C to cancel, or any key to continue...
pause >nul

echo.
echo [1/8] Setting NVIDIA_API_KEY...
vercel env add NVIDIA_API_KEY production <<< "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"

echo.
echo [2/8] Setting OPENROUTER_API_KEY...
vercel env add OPENROUTER_API_KEY production <<< "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"

echo.
echo [3/8] Setting NVIDIA_IMAGE_API_KEY...
vercel env add NVIDIA_IMAGE_API_KEY production <<< "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"

echo.
echo [4/8] Setting GOOGLE_DRIVE_FOLDER_ID...
vercel env add GOOGLE_DRIVE_FOLDER_ID production <<< "1iTngyUVgE7suUZ9ChA1QZhyVr6bGK5VH"

echo.
echo [5/8] Setting ADMIN_USERNAME...
vercel env add ADMIN_USERNAME production <<< "lychee"

echo.
echo [6/8] Setting ADMIN_PASSWORD...
vercel env add ADMIN_PASSWORD production <<< "lycheechee2026"

echo.
echo [7/8] Setting SECRET_KEY...
vercel env add SECRET_KEY production <<< "tencent-broker-analysis-secret-key-2026"

echo.
echo [8/8] Setting DATABASE_URL and FLASK_ENV...
vercel env add DATABASE_URL production <<< "broker_analysis.db"
vercel env add FLASK_ENV production <<< "production"

echo.
echo ========================================
echo All environment variables set!
echo ========================================
echo.
echo Now redeploying to Vercel...
vercel --prod

echo.
echo Done! Visit: https://broker-report-analysis.vercel.app
pause
