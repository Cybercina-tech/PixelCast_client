@echo off
REM Test runner batch script for Windows
REM Usage: test_runner.bat [test_module]

cd /d "%~dp0"

if "%1"=="" (
    python manage.py test tests --settings=tests.test_settings
) else (
    python manage.py test tests.%1 --settings=tests.test_settings
)
