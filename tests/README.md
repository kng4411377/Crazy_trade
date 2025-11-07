# Test Suite

Comprehensive test suite for the Crazy Trade Bot.

## Test Files

### Unit Tests
- **test_config.py** - Configuration loading and validation
- **test_database.py** - Database operations and models
- **test_market_hours.py** - Market hours detection and RTH logic
- **test_performance.py** - Performance tracking and metrics
- **test_sizing.py** - Position sizing calculations
- **test_state_machine.py** - Per-symbol state machine logic

### Integration Tests
- **test_integration.py** - End-to-end trading scenarios
- **test_api_server.py** - REST API endpoints

### Test Fixtures
- **conftest.py** - Shared pytest fixtures
- **__init__.py** - Test package initialization

## Running Tests

### Using Shell Script (Unix/macOS/Linux)
```bash
# Run all tests
./run_tests.sh

# Run specific test suites
./run_tests.sh unit
./run_tests.sh integration
./run_tests.sh api

# Run with coverage
./run_tests.sh coverage

# Run specific test file
./run_tests.sh file test_api_server.py

# Fast mode (less verbose)
./run_tests.sh fast
```

### Using Python Script (Cross-platform)
```bash
# Run all tests
python run_tests.py

# Run specific test suites
python run_tests.py --unit
python run_tests.py --integration
python run_tests.py --api

# Run with coverage
python run_tests.py --coverage

# Run specific test file
python run_tests.py --file test_api_server.py

# Fast mode
python run_tests.py --fast
```

### Direct pytest
```bash
# Run all tests
pytest tests/

# Run specific file
pytest tests/test_api_server.py

# Run with verbosity
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific marker
pytest tests/ -m unit
pytest tests/ -m integration
```

## Test Coverage

Current test coverage by module:

- **API Server** ✅ - 16 tests covering all endpoints
  - Health check
  - Status endpoint
  - Orders endpoint (with pagination & filtering)
  - Fills, events, daily endpoints
  - Performance metrics
  - Admin endpoints

- **Database** ✅ - 11 tests covering all database operations
  - CRUD operations
  - State management
  - Query methods

- **Configuration** - 5 tests
- **Market Hours** - 7 tests
- **Performance** - 10 tests
- **Position Sizing** - 9 tests
- **State Machine** - 13 tests
- **Integration** - 7 tests

## Test Structure

```
tests/
├── README.md           # This file
├── conftest.py        # Shared fixtures
├── __init__.py
│
├── test_api_server.py         # API endpoint tests
├── test_config.py             # Configuration tests
├── test_database.py           # Database tests
├── test_integration.py        # Integration tests
├── test_market_hours.py       # Market hours tests
├── test_performance.py        # Performance tracking tests
├── test_sizing.py             # Position sizing tests
└── test_state_machine.py      # State machine tests
```

## Writing New Tests

### Test Naming Convention
- Test files: `test_<module>.py`
- Test functions: `test_<functionality>`
- Test classes: `Test<Scenario>`

### Using Fixtures
```python
def test_something(test_db, test_config):
    """Use shared fixtures from conftest.py."""
    # test_db provides in-memory database
    # test_config provides test configuration
    pass
```

### Marking Tests
```python
import pytest

@pytest.mark.unit
def test_unit_functionality():
    """Mark as unit test."""
    pass

@pytest.mark.integration
def test_integration_scenario():
    """Mark as integration test."""
    pass

@pytest.mark.asyncio
async def test_async_function():
    """Mark as async test."""
    pass
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    python run_tests.py --coverage
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.xml
```

## Debugging Failed Tests

### View full output
```bash
pytest tests/test_file.py -vv --tb=long
```

### Run specific test
```bash
pytest tests/test_file.py::test_function_name -v
```

### Run with print statements
```bash
pytest tests/ -s
```

### Run last failed tests
```bash
pytest --lf
```

## Requirements

Tests require the following packages (in `requirements.txt`):
- pytest
- pytest-asyncio
- pytest-cov
- pytest-mock

Install with:
```bash
pip install -r requirements.txt
```

## Notes

- Tests use in-memory SQLite databases (no cleanup needed)
- API tests mock the database connection
- Integration tests may require mocked Alpaca client
- All tests should be independent and repeatable

---

**Keep tests updated when adding new features!** 🧪

