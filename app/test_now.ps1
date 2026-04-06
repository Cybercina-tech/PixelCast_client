# Quick test runner - installs dependencies if needed, then runs tests
# Usage: .\test_now.ps1

Write-Host "PixelCast Signage Test Runner" -ForegroundColor Green
Write-Host "======================" -ForegroundColor Green
Write-Host ""

# Check if in correct directory
if (-not (Test-Path "manage.py")) {
    Write-Host "Error: Please run this script from the BackEnd directory" -ForegroundColor Red
    exit 1
}

# Check Django installation
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    $django = python -c "import django; print(django.get_version())" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Django not found"
    }
    Write-Host "✓ Django $django installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Django not found. Installing..." -ForegroundColor Yellow
    python -m pip install Django djangorestframework djangorestframework-simplejwt
}

# Check pytest installation
try {
    $pytest = python -c "import pytest; print(pytest.__version__)" 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "pytest not found"
    }
    Write-Host "✓ pytest $pytest installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ pytest not found. Installing..." -ForegroundColor Yellow
    python -m pip install pytest pytest-django pytest-cov coverage
}

# Install other required packages if needed
Write-Host "Checking other dependencies..." -ForegroundColor Yellow
try {
    python -c "import rest_framework" 2>&1 | Out-Null
    Write-Host "✓ Django REST Framework installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Installing Django REST Framework..." -ForegroundColor Yellow
    python -m pip install djangorestframework djangorestframework-simplejwt
}

try {
    python -c "import PIL" 2>&1 | Out-Null
    Write-Host "✓ Pillow installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Installing Pillow..." -ForegroundColor Yellow
    python -m pip install Pillow
}

Write-Host ""
Write-Host "Running tests..." -ForegroundColor Yellow
Write-Host ""

# Run tests
python -m pytest tests/ -v

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Some tests failed. Check output above." -ForegroundColor Red
}
