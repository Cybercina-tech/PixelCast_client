.PHONY: test test-coverage test-fast test-security lint format

# Run all tests
test:
	cd BackEnd && pytest tests/ -v

# Run tests with coverage
test-coverage:
	cd BackEnd && pytest tests/ --cov=. --cov-report=html --cov-report=term-missing --cov-fail-under=80

# Run fast tests only
test-fast:
	cd BackEnd && pytest tests/ -m "not slow" -v

# Run security tests only
test-security:
	cd BackEnd && pytest tests/test_content_validation.py -m security -v

# Run linting
lint:
	cd BackEnd && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	cd BackEnd && flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
format:
	cd BackEnd && black .
	cd BackEnd && isort .

# Check formatting
format-check:
	cd BackEnd && black --check .
	cd BackEnd && isort --check-only .

# Run all checks (tests + linting)
check: lint format-check test-coverage
