# Pokémon Multi-Agent System Tests

This README provides information about the testing framework for the Pokémon Multi-Agent System.

## Test Structure

I've implemented a simplified testing approach with focused test files:

```
tests/
├── conftest.py                # Shared test fixtures and mocks
├── test_pokemon_utils.py      # Tests for Pokémon utility functions
├── test_api.py                # Tests for FastAPI endpoints
├── test_agents.py             # Tests for agent functionality
├── pytest.ini                # PyTest configuration
└── README.md                  # This file
```

## Test Components

The tests cover three primary areas:

1. **Utility Functions** (`test_pokemon_utils.py`)
   - Type effectiveness calculations
   - Pokémon data fetching
   - Battle analysis logic

2. **API Endpoints** (`test_api.py`)
   - `/chat` endpoint for general questions
   - `/battle` endpoint for simulating battles
   - Error handling and edge cases

3. **Agent Functionality** (`test_agents.py`)
   - Researcher agent functionality
   - Expert agent battle analysis
   - Supervisor agent coordination
   - Response formatting

## Setting Up the Test Environment

### Prerequisites

- Python 3.9+
- pytest and pytest-mock

### Installation

```bash
# Install required packages
pip install pytest pytest-mock

# If you're using the project's requirements.txt
pip install -r requirements.txt
```

## Running Tests

### Running All Tests

```bash
# From the project root directory
pytest
```

### Running Specific Test Files

```bash
# Test utility functions
pytest tests/test_pokemon_utils.py

# Test API endpoints
pytest tests/test_api.py

# Test agent functionality
pytest tests/test_agents.py
```

### Running with Verbose Output

```bash
pytest -v
```

## Mocking Strategy

The tests use a simplified mocking approach to avoid external dependencies:

- **API Mocks**: We mock the PokéAPI responses to avoid actual network calls
- **LLM Mocks**: Language model calls are mocked to ensure consistent results
- **Agent Mocks**: Agent interactions are simulated without requiring actual LLM calls

## Adding New Tests

To add new tests:

1. Choose the appropriate test file based on what you're testing
2. Use existing fixtures from `conftest.py`
3. Follow the pattern of existing tests
4. Run the test to verify it works

## Continuous Integration

I'm using GitHub Actions to automatically run tests on each push and pull request. The workflow is defined in `.github/workflows/test.yml`.

## Best Practices

- Keep tests focused on a single functionality
- Use mocks to isolate the component being tested
- Maintain test independence (tests should not depend on each other)
- Add comments to explain complex test scenarios

## Troubleshooting

If you encounter import errors, make sure your Python path includes the project root directory. This is configured in `pytest.ini` but may require additional setup in some environments.

For more complex debugging, use the `-v` flag for verbose output:

```bash
pytest -v
```