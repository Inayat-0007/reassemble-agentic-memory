# REASSEMBLE — Build Lambda ZIP
# Usage: .\scripts\build.ps1
# Produces: reassemble-lambda.zip in project root

$ErrorActionPreference = "Stop"

Write-Host "=== REASSEMBLE Build Script ===" -ForegroundColor Cyan
Write-Host "Building Lambda deployment package..." -ForegroundColor Yellow

$projectRoot = Split-Path -Parent $PSScriptRoot
$packageDir = Join-Path $projectRoot "package"
$zipFile = Join-Path $projectRoot "reassemble-lambda.zip"

# Clean previous build
if (Test-Path $packageDir) {
    Write-Host "Cleaning previous build..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $packageDir
}
if (Test-Path $zipFile) {
    Remove-Item -Force $zipFile
}

# Create package directory
New-Item -ItemType Directory -Path $packageDir | Out-Null

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install -r (Join-Path $projectRoot "requirements.txt") -t $packageDir --quiet

# Copy Lambda function
Write-Host "Copying Lambda function..." -ForegroundColor Yellow
Copy-Item (Join-Path $projectRoot "lambda_function.py") $packageDir

# Create ZIP
Write-Host "Creating ZIP archive..." -ForegroundColor Yellow
Push-Location $packageDir
Compress-Archive -Path * -DestinationPath $zipFile -Force
Pop-Location

# Verify
if (Test-Path $zipFile) {
    $size = (Get-Item $zipFile).Length / 1MB
    Write-Host "✅ Build complete: reassemble-lambda.zip ($([math]::Round($size, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

# Cleanup
Write-Host "Cleaning up package directory..." -ForegroundColor Yellow
Remove-Item -Recurse -Force $packageDir

Write-Host "=== Done ===" -ForegroundColor Cyan
