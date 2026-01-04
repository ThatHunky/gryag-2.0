# Development Guide

This guide covers setting up a development environment, understanding the project structure, coding standards, testing, and contributing to Gryag 2.0.

## Development Setup

### Prerequisites

- Python 3.13+
- Docker and Docker Compose (for services)
- Git
- Code editor (VS Code, PyCharm, etc.)

### Initial Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourserver/gryag-2.0.git
    cd gryag-2.0
    ```

2. **Create virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install dependencies:**

    ```bash
    pip install -e ".[dev]"
    ```

    Or using uv (faster):

    ```bash
    pip install uv
    uv pip install -e ".[dev]"
    ```

4. **Start services (Docker):**

    ```bash
    docker compose up -d postgres redis
    ```

5. **Create `.env` file:**

    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

6. **Run database migrations:**

    ```bash
    alembic upgrade head
    ```

7. **Run the bot:**

    ```bash
    python -m bot.main
    ```

### Development Configuration

For development, use these settings in `.env`:

```env
LOG_LEVEL=DEBUG
LOG_FORMAT=text
ACCESS_MODE=private
RATE_LIMIT_ENABLED=False
```

## Project Structure

```
gryag-2.0/
├── bot/                    # Main application code
│   ├── __init__.py
│   ├── main.py            # Entry point
│   ├── config.py          # Configuration management
│   ├── cache/             # Caching (Redis)
│   │   ├── __init__.py
│   │   └── redis.py
│   ├── context/           # Context management
│   │   ├── __init__.py
│   │   ├── manager.py     # Context assembly
│   │   ├── immediate.py   # Immediate context
│   │   ├── permanent.py   # System prompts
│   │   ├── scheduler.py   # Background tasks
│   │   └── summarizer.py  # Summary generation
│   ├── db/                # Database layer
│   │   ├── __init__.py
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── session.py     # Session management
│   │   └── repositories/  # Repository pattern
│   │       ├── __init__.py
│   │       ├── chats.py
│   │       ├── messages.py
│   │       ├── memories.py
│   │       ├── summaries.py
│   │       └── users.py
│   ├── handlers/          # Message handlers
│   │   ├── __init__.py
│   │   ├── base.py        # Base utilities
│   │   ├── commands.py    # Bot commands
│   │   ├── admin.py       # Admin commands
│   │   ├── private.py     # Private chat handler
│   │   └── group.py       # Group chat handler
│   ├── llm/               # LLM client
│   │   ├── __init__.py
│   │   ├── client.py      # LLM client
│   │   └── models.py      # LLM models
│   ├── middlewares/       # Middleware
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── access_control.py
│   │   └── rate_limit.py
│   ├── tools/             # Tool system
│   │   ├── __init__.py
│   │   ├── base.py        # Base tool interface
│   │   ├── registry.py    # Tool registry
│   │   ├── calculator.py
│   │   ├── weather.py
│   │   ├── search.py
│   │   ├── image.py
│   │   └── memory.py
│   └── utils/             # Utilities
│       ├── __init__.py
│       ├── commands.py
│       ├── errors.py
│       ├── formatting.py
│       ├── logging.py
│       └── triggers.py
├── tests/                 # Tests
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures
│   └── test_tools/        # Tool tests
├── migrations/            # Alembic migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── prompts/               # System prompts
│   ├── default.md
│   ├── assistant.md
│   └── casual.md
├── docs/                  # Documentation
│   ├── en/
│   └── uk/
├── data/                  # Data directory
│   ├── logs/
│   └── postgres/
├── docker-compose.yml      # Docker Compose config
├── Dockerfile             # Docker image
├── pyproject.toml         # Project config
├── pytest.ini            # Pytest config
├── alembic.ini            # Alembic config
└── README.md             # Main README
```

## Code Style and Conventions

### Python Style

The project uses:

- **Python 3.13+** features
- **Type hints** for all functions and methods
- **Async/await** for all I/O operations
- **Ruff** for linting and formatting

### Code Formatting

1. **Install pre-commit hooks (optional):**

    ```bash
    pip install pre-commit
    pre-commit install
    ```

2. **Format code:**

    ```bash
    ruff format .
    ```

3. **Lint code:**

    ```bash
    ruff check .
    ```

### Type Hints

Always use type hints:

```python
from typing import Optional

async def get_user(user_id: int) -> Optional[User]:
    """Get user by ID."""
    pass
```

### Async/Await

All I/O operations must be async:

```python
# Good
async def fetch_data() -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")
        return response.json()

# Bad
def fetch_data() -> dict:
    response = requests.get("https://api.example.com")
    return response.json()
```

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `ContextManager`)
- **Functions/Methods**: `snake_case` (e.g., `get_user`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- **Private**: Prefix with `_` (e.g., `_internal_method`)

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

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=bot --cov-report=html

# Run specific test file
pytest tests/test_tools/test_calculator.py

# Run with verbose output
pytest -v
```

### Writing Tests

Tests use pytest with async support:

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
```

### Test Fixtures

Common fixtures in `tests/conftest.py`:

- `db_session` - Database session for tests
- `event_loop` - Async event loop

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── test_tools/           # Tool tests
│   ├── __init__.py
│   └── test_calculator.py
└── test_handlers/        # Handler tests (future)
```

## Adding New Features

### 1. Adding a New Tool

1. **Create tool file** (`bot/tools/mytool.py`):

    ```python
    from bot.tools.base import BaseTool, ToolResult

    class MyTool(BaseTool):
        name = "my_tool"
        description = "Tool description"
        parameters = {...}
        
        async def execute(self, **kwargs) -> ToolResult:
            # Implementation
            pass
    ```

2. **Register in registry** (`bot/tools/registry.py`):

    ```python
    from bot.tools.mytool import MyTool
    
    def _register_default_tools(registry: ToolRegistry) -> None:
        # ... existing tools
        registry.register(MyTool())
    ```

3. **Write tests** (`tests/test_tools/test_mytool.py`):

    ```python
    @pytest.mark.asyncio
    async def test_my_tool():
        # Test implementation
        pass
    ```

4. **Update documentation** (`docs/en/tools.md`)

### 2. Adding a New Handler

1. **Create handler** (`bot/handlers/myhandler.py`):

    ```python
    from aiogram import Router, F
    from aiogram.types import Message

    router = Router(name="myhandler")

    @router.message(F.text.startswith("/mycommand"))
    async def handle_my_command(message: Message):
        await message.answer("Response")
    ```

2. **Register in dispatcher** (`bot/main.py`):

    ```python
    from bot.handlers import myhandler
    
    def create_dispatcher() -> Dispatcher:
        dp = Dispatcher()
        # ... existing routers
        dp.include_router(myhandler.router)
        return dp
    ```

### 3. Adding a New Database Model

1. **Add model** (`bot/db/models.py`):

    ```python
    class MyModel(Base):
        __tablename__ = "my_table"
        
        id: Mapped[int] = mapped_column(primary_key=True)
        # ... fields
    ```

2. **Create migration:**

    ```bash
    alembic revision --autogenerate -m "Add my_table"
    ```

3. **Review and apply migration:**

    ```bash
    alembic upgrade head
    ```

4. **Create repository** (`bot/db/repositories/mymodel.py`):

    ```python
    class MyModelRepository:
        def __init__(self, session: AsyncSession):
            self.session = session
        
        # ... methods
    ```

## Debugging

### Debug Mode

Set in `.env`:

```env
LOG_LEVEL=DEBUG
```

### Debugging in VS Code

1. **Create `.vscode/launch.json`:**

    ```json
    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Bot",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/bot/main.py",
                "console": "integratedTerminal",
                "envFile": "${workspaceFolder}/.env"
            }
        ]
    }
    ```

2. **Set breakpoints and debug**

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

### Database Debugging

Enable SQL logging:

```env
LOG_LEVEL=DEBUG
```

This will log all SQL queries.

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Description"

# Manual migration
alembic revision -m "Description"
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision>

# Rollback one migration
alembic downgrade -1
```

### Migration Best Practices

1. Always review auto-generated migrations
2. Test migrations on development database first
3. Backup production database before applying
4. Use descriptive migration messages
5. Never edit existing migration files

## Performance Optimization

### Database Queries

1. **Use indexes** (already defined in models)
2. **Limit queries** (use `.limit()`)
3. **Use select_related** for relationships
4. **Avoid N+1 queries**

### Caching

Redis is available for caching:

```python
from bot.cache.redis import get_redis

redis = await get_redis()
await redis.set("key", "value", ex=3600)  # 1 hour TTL
value = await redis.get("key")
```

### Context Limits

Adjust context limits based on usage:

```env
IMMEDIATE_CONTEXT_MESSAGES=100  # Reduce if too slow
CONTEXT_MAX_TOKENS=8000         # Reduce if hitting limits
```

## Contributing Guidelines

### Workflow

1. **Fork the repository**
2. **Create a feature branch:**

    ```bash
    git checkout -b feature/my-feature
    ```

3. **Make changes and commit:**

    ```bash
    git commit -m "Add feature: description"
    ```

4. **Write/update tests**
5. **Run tests and linting:**

    ```bash
    pytest
    ruff check .
    ruff format .
    ```

6. **Push and create pull request**

### Commit Messages

Use clear, descriptive commit messages:

```
Add feature: Calculator tool with AST parsing
Fix bug: Handle rate limit errors gracefully
Update docs: Add tool development guide
```

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Migration created (if database changes)
- [ ] Backward compatible (if possible)

### Code Review

- Be respectful and constructive
- Focus on code, not person
- Explain reasoning for suggestions
- Respond to feedback promptly

## Common Development Tasks

### Running Bot Locally

```bash
# Start services
docker compose up -d postgres redis

# Run bot
python -m bot.main
```

### Testing Database Changes

```bash
# Create test database
createdb gryag_test

# Update DATABASE_URL in .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/gryag_test

# Run migrations
alembic upgrade head

# Test
pytest
```

### Updating Dependencies

```bash
# Update pyproject.toml
# Then:
pip install -e ".[dev]"
```

### Building Docker Image

```bash
docker compose build bot
```

## Troubleshooting Development Issues

### Import Errors

- Ensure virtual environment is activated
- Check `PYTHONPATH` is set correctly
- Verify package is installed: `pip install -e .`

### Database Connection Errors

- Verify PostgreSQL is running: `docker compose ps postgres`
- Check `DATABASE_URL` in `.env`
- Ensure database exists

### Test Failures

- Check test database is clean
- Verify fixtures are working
- Check async test markers are present

### Linting Errors

- Run `ruff format .` to auto-fix formatting
- Fix remaining issues manually
- Check `ruff check .` output

## Related Documentation

- [API Reference](api-reference.md) - Code-level API documentation
- [Architecture](architecture.md) - System architecture
- [Tools Guide](tools.md) - Tool development guide
- [Database Schema](database.md) - Database documentation