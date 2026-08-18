# REASSEMBLE — Local Test Script
# Usage: .\scripts\test-local.ps1
# Requires: .env or environment variables set

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== REASSEMBLE Local Test ===" -ForegroundColor Cyan

# Check Python
Write-Host "Python version:" -ForegroundColor Yellow
python --version

# Check environment variables
$required = @("CRDB_URL", "AWS_REGION", "CHAT_MODEL_ID", "EMBED_MODEL_ID")
$missing = @()
foreach ($var in $required) {
    $val = [Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($val)) {
        $missing += $var
    } else {
        $masked = if ($var -eq "CRDB_URL") { "****" } else { $val }
        Write-Host "  ✅ $var = $masked" -ForegroundColor Green
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "❌ Missing environment variables:" -ForegroundColor Red
    foreach ($var in $missing) {
        Write-Host "  - $var" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Set them with:" -ForegroundColor Yellow
    Write-Host '  $env:CRDB_URL="postgresql://USER:PASSWORD@HOST:26257/defaultdb?sslmode=verify-full"'
    Write-Host '  $env:AWS_REGION="us-east-1"'
    Write-Host '  $env:CHAT_MODEL_ID="amazon.nova-lite-v1:0"'
    Write-Host '  $env:EMBED_MODEL_ID="amazon.titan-embed-text-v2:0"'
    exit 1
}

# Test GET /
Write-Host ""
Write-Host "Testing GET / ..." -ForegroundColor Yellow
python -c @"
import json, sys
sys.path.insert(0, r'$projectRoot')
from lambda_function import lambda_handler
event = {'requestContext': {'http': {'method': 'GET'}}, 'rawPath': '/'}
result = lambda_handler(event, None)
print(f"Status: {result['statusCode']}")
print(f"Content-Type: {result['headers']['Content-Type']}")
print(f"Body length: {len(result['body'])} chars")
if result['statusCode'] == 200:
    print('✅ GET / works!')
else:
    print('❌ GET / failed!')
"@

Write-Host ""
Write-Host "=== Done ===" -ForegroundColor Cyan
