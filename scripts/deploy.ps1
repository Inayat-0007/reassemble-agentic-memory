# REASSEMBLE — Deploy to AWS Lambda
# Usage: .\scripts\deploy.ps1
# Requires: AWS CLI configured, reassemble-lambda.zip built

$ErrorActionPreference = "Stop"

$FunctionName = "reassemble-agent"
$projectRoot = Split-Path -Parent $PSScriptRoot
$zipFile = Join-Path $projectRoot "reassemble-lambda.zip"

Write-Host "=== REASSEMBLE Deploy Script ===" -ForegroundColor Cyan

# Check ZIP exists
if (-not (Test-Path $zipFile)) {
    Write-Host "❌ reassemble-lambda.zip not found. Run build.ps1 first." -ForegroundColor Red
    exit 1
}

# Deploy
Write-Host "Uploading to Lambda function: $FunctionName ..." -ForegroundColor Yellow

aws lambda update-function-code `
    --function-name $FunctionName `
    --zip-file "fileb://$zipFile" `
    --no-cli-pager

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deploy complete!" -ForegroundColor Green

    # Get Function URL
    Write-Host ""
    Write-Host "Function URL:" -ForegroundColor Cyan
    aws lambda get-function-url-config --function-name $FunctionName --query "FunctionUrl" --output text --no-cli-pager 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "(No Function URL configured yet. Create one in Lambda Console.)" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ Deploy failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
