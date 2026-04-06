# Test runner PowerShell script
# Usage: .\test_runner.ps1 [test_module]

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if ($args.Count -eq 0) {
    python manage.py test tests --settings=tests.test_settings
} else {
    python manage.py test "tests.$($args[0])" --settings=tests.test_settings
}
