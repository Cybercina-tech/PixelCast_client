# Setup script for test environment
# Run this first before running tests

Write-Host "Setting up test environment..." -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "manage.py")) {
    Write-Host "Error: manage.py not found. Please run this script from the BackEnd directory." -ForegroundColor Red
    exit 1
}

Write-Host "Installing test dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pytest pytest-django pytest-cov coverage Pillow

Write-Host "`nChecking installations..." -ForegroundColor Yellow
python -c "import django; print(f'Django {django.get_version()}')"
python -c "import pytest; print(f'pytest {pytest.__version__}')"

Write-Host "`n✅ Setup complete! You can now run tests with:" -ForegroundColor Green
Write-Host "   python -m pytest tests/ -v" -ForegroundColor Cyan
Write-Host "   OR" -ForegroundColor Cyan
Write-Host "   python manage.py test tests --settings=tests.test_settings" -ForegroundColor Cyan
