# Contributing to Gryag 2.0

Thank you for your interest in contributing to Gryag 2.0! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's coding standards

## Getting Started

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/yourusername/gryag-2.0.git
   cd gryag-2.0
   ```

3. **Set up development environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

4. **Create a branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

## Development Workflow

### 1. Making Changes

- Make your changes in a feature branch
- Follow the coding standards (see below)
- Write or update tests
- Update documentation

### 2. Testing

Run tests before submitting:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bot --cov-report=html

# Run specific test
pytest tests/test_tools/test_calculator.py
```

### 3. Code Quality

Check code quality:

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking (if configured)
mypy bot/
```

### 4. Commit Messages

Use clear, descriptive commit messages:

```
Add feature: Calculator tool with AST parsing
Fix bug: Handle rate limit errors gracefully
Update docs: Add tool development guide
Refactor: Simplify context assembly logic
```

**Format:**
```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `Add`: New feature
- `Fix`: Bug fix
- `Update`: Documentation or configuration update
- `Refactor`: Code refactoring
- `Remove`: Remove feature or code
- `Test`: Add or update tests

### 5. Pull Request

1. **Push your branch:**
   ```bash
   git push origin feature/my-feature
   ```

2. **Create Pull Request:**
   - Use clear title and description
   - Reference related issues
   - Include screenshots if UI changes
   - Update CHANGELOG if applicable

3. **Pull Request Checklist:**
   - [ ] Code follows style guidelines
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No linting errors
   - [ ] Migration created (if database changes)
   - [ ] Backward compatible (if possible)

## Coding Standards

### Python Style

- **Python 3.13+** features
- **Type hints** for all functions
- **Async/await** for I/O operations
- **Ruff** for formatting and linting

### Code Formatting

```bash
# Auto-format
ruff format .

# Check formatting
ruff format --check .
```

### Type Hints

Always use type hints:

```python
from typing import Optional

async def get_user(user_id: int) -> Optional[User]:
    """Get user by ID."""
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_total(items: list[float]) -> float:
    """Calculate total of items.
    
    Args:
        items: List of item prices
        
    Returns:
        Total price
        
    Raises:
        ValueError: If items list is empty
    """
    if not items:
        raise ValueError("Items list cannot be empty")
    return sum(items)
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `ContextManager`)
- **Functions/Methods**: `snake_case` (e.g., `get_user`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private**: Prefix with `_` (e.g., `_internal_method`)

### Error Handling

Always handle errors explicitly:

```python
try:
    result = await some_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    return None
except Exception as e:
    logger.exception("Unexpected error")
    raise
```

## Adding New Features

### Adding a Tool

1. Create tool file in `bot/tools/`
2. Implement `BaseTool` interface
3. Register in `bot/tools/registry.py`
4. Write tests
5. Update documentation

See [Tools Guide](docs/en/tools.md) for details.

### Adding a Handler

1. Create handler file in `bot/handlers/`
2. Register router in `bot/main.py`
3. Write tests
4. Update documentation

### Adding a Database Model

1. Add model to `bot/db/models.py`
2. Create migration: `alembic revision --autogenerate -m "Description"`
3. Review migration
4. Create repository in `bot/db/repositories/`
5. Update documentation

## Testing Guidelines

### Writing Tests

- Use pytest with async support
- Test both success and failure cases
- Use fixtures for common setup
- Keep tests isolated and independent

**Example:**

```python
import pytest
from bot.tools.calculator import CalculatorTool

@pytest.mark.asyncio
async def test_calculator_addition():
    tool = CalculatorTool()
    result = await tool.execute(expression="2+2")
    
    assert result.success is True
    assert "4" in result.output
    assert result.data["result"] == 4.0

@pytest.mark.asyncio
async def test_calculator_invalid_expression():
    tool = CalculatorTool()
    result = await tool.execute(expression="invalid")
    
    assert result.success is False
    assert result.error is not None
```

### Test Coverage

- Aim for high test coverage
- Test edge cases
- Test error handling
- Test async operations

## Documentation

### Updating Documentation

- Update relevant documentation files
- Add examples for new features
- Update API reference if needed
- Keep diagrams up to date

### Documentation Structure

- `docs/en/` - English documentation
- `docs/uk/` - Ukrainian documentation (if applicable)
- Keep both versions in sync

## Review Process

### What Reviewers Look For

1. **Code Quality:**
   - Follows style guidelines
   - Proper error handling
   - Type hints
   - Documentation

2. **Functionality:**
   - Works as intended
   - Handles edge cases
   - No breaking changes (if possible)

3. **Tests:**
   - Tests pass
   - Good coverage
   - Tests are meaningful

4. **Documentation:**
   - Updated appropriately
   - Clear and accurate
   - Examples included

### Responding to Feedback

- Be open to feedback
- Ask questions if unclear
- Make requested changes
- Explain your reasoning if needed

## Issue Reporting

### Before Creating an Issue

1. Check existing issues
2. Search for similar problems
3. Verify it's a bug (not a feature request)
4. Gather relevant information

### Creating an Issue

Include:

1. **Description:**
   - What happened
   - What you expected
   - Steps to reproduce

2. **Environment:**
   - OS and version
   - Python version
   - Bot version
   - Configuration (sanitized)

3. **Logs:**
   - Relevant log excerpts
   - Error messages
   - Stack traces

4. **Additional Info:**
   - Screenshots if applicable
   - Related issues
   - Possible solutions

## Feature Requests

### Submitting Feature Requests

1. **Check existing requests:**
   - Search for similar features
   - Comment on existing issues if relevant

2. **Create feature request:**
   - Clear title
   - Detailed description
   - Use case examples
   - Possible implementation approach

3. **Discussion:**
   - Engage in discussion
   - Provide feedback on others' requests
   - Help prioritize features

## Questions?

- Check [Documentation](docs/en/README.md)
- Search existing issues
- Ask in discussions (if enabled)
- Contact maintainers

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Thank You!

Your contributions make this project better. Thank you for taking the time to contribute!
