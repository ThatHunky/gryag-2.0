# API Reference

This document provides detailed API reference for key modules, classes, and methods in the Gryag 2.0 codebase.

## Table of Contents

- [Configuration](#configuration)
- [Database](#database)
- [Context Management](#context-management)
- [LLM Client](#llm-client)
- [Tools](#tools)
- [Handlers](#handlers)
- [Middlewares](#middlewares)
- [Utilities](#utilities)

## Configuration

### `bot.config.Settings`

Main configuration class using Pydantic Settings.

```python
from bot.config import get_settings

settings = get_settings()
```

**Key Properties:**

- `telegram_bot_token: str` - Telegram bot token (required)
- `llm_api_key: str` - LLM API key (required)
- `llm_base_url: str` - LLM API base URL
- `llm_model: str` - Primary LLM model
- `database_url: str` - PostgreSQL connection URL
- `redis_url: str` - Redis connection URL
- `admin_ids: list[int]` - Admin user IDs (property, parsed from comma-separated string)
- `bot_trigger_keywords: list[str]` - Group chat trigger keywords (property)

**Methods:**

- `get_settings() -> Settings` - Get cached settings instance (singleton)

**Example:**

```python
from bot.config import get_settings

settings = get_settings()
print(settings.llm_model)  # "gpt-4o"
print(settings.admin_ids)  # [12345678, 87654321]
```

## Database

### Session Management

#### `bot.db.session.get_session()`

Async context manager for database sessions.

```python
from bot.db.session import get_session

async with get_session() as session:
    # Use session
    pass
```

**Returns:** `AsyncGenerator[AsyncSession, None]`

**Usage:**

```python
async with get_session() as session:
    repo = MessageRepository(session)
    messages = await repo.get_recent(chat_id=123, limit=10)
```

#### `bot.db.session.init_db()`

Initialize database tables (creates tables if they don't exist).

```python
from bot.db.session import init_db

await init_db()
```

#### `bot.db.session.close_db()`

Close all database connections.

```python
from bot.db.session import close_db

await close_db()
```

### Repositories

All repositories follow the same pattern: they take an `AsyncSession` in the constructor and provide async methods for database operations.

#### `bot.db.repositories.ChatRepository`

Repository for chat operations.

**Methods:**

- `get_by_id(chat_id: int) -> Chat | None` - Get chat by ID
- `get_or_create(chat_id: int, title: str | None = None, chat_type: str = "private", member_count: int | None = None) -> Chat` - Get or create chat
- `update(chat: Chat) -> Chat` - Update chat
- `get_active_chats() -> list[Chat]` - Get all active chats

**Example:**

```python
async with get_session() as session:
    repo = ChatRepository(session)
    chat = await repo.get_or_create(
        chat_id=-1001234567890,
        title="My Group",
        chat_type="supergroup",
        member_count=50
    )
```

#### `bot.db.repositories.UserRepository`

Repository for user operations.

**Methods:**

- `get_by_id(user_id: int) -> User | None` - Get user by ID
- `get_or_create(user_id: int, username: str | None = None, full_name: str = "Unknown") -> User` - Get or create user
- `update(user: User) -> User` - Update user

**Example:**

```python
async with get_session() as session:
    repo = UserRepository(session)
    user = await repo.get_or_create(
        user_id=12345678,
        username="johndoe",
        full_name="John Doe"
    )
```

#### `bot.db.repositories.MessageRepository`

Repository for message operations.

**Methods:**

- `add(telegram_message_id: int, chat_id: int, user_id: int | None, content: str, content_type: str = "text", reply_to_message_id: int | None = None, is_bot_message: bool = False) -> Message` - Add new message
- `get_recent(chat_id: int, limit: int = 100) -> list[Message]` - Get recent messages (chronological order)
- `get_since(chat_id: int, since: datetime) -> list[Message]` - Get messages since datetime
- `get_count_since(chat_id: int, since: datetime) -> int` - Get message count since datetime
- `delete_old(chat_id: int, older_than_days: int = 60) -> int` - Delete old messages
- `find_by_telegram_id(chat_id: int, telegram_message_id: int) -> Message | None` - Find by Telegram message ID

**Example:**

```python
async with get_session() as session:
    repo = MessageRepository(session)
    
    # Add message
    message = await repo.add(
        telegram_message_id=12345,
        chat_id=-1001234567890,
        user_id=12345678,
        content="Hello, world!",
        content_type="text"
    )
    
    # Get recent messages
    messages = await repo.get_recent(chat_id=-1001234567890, limit=50)
```

#### `bot.db.repositories.SummaryRepository`

Repository for summary operations.

**Methods:**

- `add(chat_id: int, summary_type: str, content: str, token_count: int, period_start: datetime, period_end: datetime) -> Summary` - Add summary
- `get_latest(chat_id: int, summary_type: str) -> Summary | None` - Get latest summary of type
- `get_all(chat_id: int) -> list[Summary]` - Get all summaries for chat

**Example:**

```python
async with get_session() as session:
    repo = SummaryRepository(session)
    summary = await repo.get_latest(chat_id=-1001234567890, summary_type="7day")
```

#### `bot.db.repositories.MemoryRepository`

Repository for user memory operations.

**Methods:**

- `add_memory(user_id: int, fact: str) -> UserMemory` - Add memory (auto-cleans old memories if limit exceeded)
- `get_memories(user_id: int) -> list[UserMemory]` - Get all memories for user
- `delete_memory(memory_id: int) -> None` - Delete specific memory

**Example:**

```python
async with get_session() as session:
    repo = MemoryRepository(session, max_facts=50)
    await repo.add_memory(user_id=12345678, fact="User likes Python")
    memories = await repo.get_memories(user_id=12345678)
```

### Models

All models are defined in `bot.db.models` using SQLAlchemy 2.0 ORM.

**Key Models:**

- `Chat` - Telegram chat metadata
- `User` - Telegram user information
- `Message` - Stored messages
- `Summary` - Context summaries
- `UserMemory` - User memories
- `UserRestriction` - User bans/restrictions
- `AccessList` - Whitelist/blacklist entries

See [Database Schema](database.md) for complete model documentation.

## Context Management

### `bot.context.manager.ContextManager`

Manages context assembly for LLM requests.

**Constructor:**

```python
ContextManager(
    chat_id: int,
    user_id: int,
    bot: Bot | None = None,
    reply_to_message: Message | None = None,
    chat_title: str | None = None,
    chat_type: str = "private",
    member_count: int | None = None,
    bot_name: str = "Грягі",
    bot_username: str = "gryag_bot"
)
```

**Methods:**

- `build_context() -> list[dict]` - Build complete context for LLM

**Returns:** List of message dictionaries in OpenAI format:
```python
[
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."},
    # ... more messages
]
```

**Example:**

```python
from bot.context.manager import ContextManager

context_manager = ContextManager(
    chat_id=-1001234567890,
    user_id=12345678,
    bot=bot,
    chat_title="My Group",
    chat_type="supergroup"
)

context = await context_manager.build_context()
```

### `bot.context.permanent.load_system_prompt()`

Load and process system prompt with variable substitution.

```python
from bot.context.permanent import load_system_prompt

prompt = load_system_prompt(
    filename="default.md",
    variables={
        "username": "johndoe",
        "chatname": "My Chat",
        # ... more variables
    }
)
```

**Parameters:**

- `filename: str` - Prompt file name (from `prompts/` directory)
- `variables: dict[str, str]` - Variables to substitute

**Returns:** `str` - Processed prompt text

### `bot.context.summarizer.generate_summary()`

Generate context summary for a chat.

```python
from bot.context.summarizer import generate_summary

summary = await generate_summary(
    chat_id=-1001234567890,
    summary_type="7day",  # or "30day"
    llm_client=llm_client
)
```

**Parameters:**

- `chat_id: int` - Chat ID
- `summary_type: str` - "7day" or "30day"
- `llm_client: LLMClient` - LLM client instance

**Returns:** `str | None` - Summary content or None if no messages

## LLM Client

### `bot.llm.client.LLMClient`

OpenAI-compatible LLM client with reliability features.

**Constructor:**

```python
from bot.llm import LLMClient

llm_client = LLMClient()
```

**Methods:**

#### `complete()`

Complete a chat conversation (no tool calling).

```python
response = await llm_client.complete(
    messages=[
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ],
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float = 0.7,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None
)
```

**Returns:** `str` - Assistant message content

**Example:**

```python
response = await llm_client.complete(
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=500
)
```

#### `complete_with_tools()`

Complete with tool calling support.

```python
result = await llm_client.complete_with_tools(
    messages=[...],
    tools=[...],
    model: str | None = None,
    max_tokens: int | None = None
)
```

**Returns:** `dict` with keys:
- `content: str` - Assistant message (may be empty)
- `tool_calls: list[dict]` - List of tool calls

**Tool Call Format:**

```python
{
    "id": "call_123",
    "name": "calculator",
    "arguments": '{"expression": "2+2"}'
}
```

**Example:**

```python
result = await llm_client.complete_with_tools(
    messages=[{"role": "user", "content": "Calculate 2+2"}],
    tools=tool_schemas
)

if result["tool_calls"]:
    # Execute tools
    pass
else:
    # Use result["content"]
    pass
```

#### `complete_with_vision()`

Complete a vision request with image content.

```python
response = await llm_client.complete_with_vision(
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "https://..."}}
            ]
        }
    ],
    max_tokens: int | None = None,
    temperature: float = 0.7
)
```

**Returns:** `str | None` - Response or None if vision disabled

#### `count_tokens()`

Estimate token count for text.

```python
count = await llm_client.count_tokens("Hello, world!")
```

**Returns:** `int` - Estimated token count

## Tools

### `bot.tools.base.BaseTool`

Abstract base class for all tools.

**Required Attributes:**

- `name: str` - Tool name (used in function calls)
- `description: str` - Human-readable description
- `parameters: dict` - JSON Schema for parameters

**Required Methods:**

- `execute(**kwargs) -> ToolResult` - Execute the tool

**Methods:**

- `to_openai_schema() -> dict` - Convert to OpenAI function calling schema

**Example:**

```python
from bot.tools.base import BaseTool, ToolResult

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something"
    parameters = {
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        },
        "required": ["param"]
    }
    
    async def execute(self, param: str, **kwargs) -> ToolResult:
        return ToolResult(
            success=True,
            output=f"Result: {param}",
            data={"param": param}
        )
```

### `bot.tools.base.ToolResult`

Result from tool execution.

**Attributes:**

- `success: bool` - Whether execution succeeded
- `output: str` - Human-readable output for LLM
- `data: dict[str, Any]` - Structured data (optional)
- `error: str | None` - Error message if failed

**Methods:**

- `to_message() -> str` - Convert to message for LLM

### `bot.tools.registry.ToolRegistry`

Registry for managing and discovering tools.

**Methods:**

- `register(tool: BaseTool) -> None` - Register a tool instance
- `register_class(tool_class: Type[BaseTool]) -> None` - Register a tool class
- `get(name: str) -> BaseTool | None` - Get tool by name
- `list_names() -> list[str]` - List all registered tool names
- `list_tools() -> list[BaseTool]` - List all registered tools
- `get_openai_schemas() -> list[dict]` - Get OpenAI function schemas
- `execute(name: str, **kwargs) -> ToolResult` - Execute a tool by name

**Global Registry:**

```python
from bot.tools.registry import get_registry

registry = get_registry()
tool = registry.get("calculator")
result = await registry.execute("calculator", expression="2+2")
```

## Handlers

### Handler Base Functions

#### `bot.handlers.base.extract_user_info()`

Extract user info from message.

```python
from bot.handlers.base import extract_user_info

user_info = extract_user_info(message)
# Returns: {"id": int, "username": str | None, "full_name": str}
```

#### `bot.handlers.base.extract_chat_info()`

Extract chat info from message.

```python
from bot.handlers.base import extract_chat_info

chat_info = extract_chat_info(message)
# Returns: {"id": int, "title": str | None, "type": str}
```

#### `bot.handlers.base.send_typing_action()`

Send typing indicator if enabled.

```python
from bot.handlers.base import send_typing_action

await send_typing_action(bot, chat_id=123456)
```

#### `bot.handlers.base.is_admin()`

Check if user is an admin.

```python
from bot.handlers.base import is_admin

if is_admin(user_id):
    # Admin logic
    pass
```

### Router Structure

Handlers are organized into routers:

- `commands_router` - Bot commands:
  - `/start` - Start the bot (greeting message)
  - `/help` - Show help message and available commands
  - `/memories` - Display stored memories about the user (with pagination)
  - `/stats` - Show bot statistics (user count, chat count, message count)
- `admin_router` - Admin-only commands (private chats)
- `private_router` - Private chat message handling
- `group_router` - Group chat message handling

**Example Handler:**

```python
from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text.startswith("/hello"))
async def handle_hello(message: Message):
    await message.answer("Hello!")
```

## Middlewares

### `bot.middlewares.access_control.AccessControlMiddleware`

Multi-layer access control middleware.

**Layers:**

1. Admin bypass
2. User restriction check (bans/restrictions)
3. Blacklist check
4. Access mode check (global/private/whitelist)

**Usage:**

```python
from bot.middlewares import AccessControlMiddleware

dp.message.middleware(AccessControlMiddleware())
```

### `bot.middlewares.rate_limit.RateLimitMiddleware`

Rate limiting middleware for non-admins.

**Configuration:**

- `RATE_LIMIT_ENABLED` - Enable/disable
- `RATE_LIMIT_PROMPTS` - Max requests per window
- `RATE_LIMIT_WINDOW_HOURS` - Time window

**Usage:**

```python
from bot.middlewares import RateLimitMiddleware

dp.message.middleware(RateLimitMiddleware())
```

### `bot.middlewares.logging.LoggingMiddleware`

Logging middleware for all messages.

**Usage:**

```python
from bot.middlewares import LoggingMiddleware

dp.message.middleware(LoggingMiddleware())
```

## Utilities

### `bot.utils.errors.LLMError`

Custom exception for LLM errors.

```python
from bot.utils.errors import LLMError, ERROR_MESSAGES

try:
    # LLM operation
    pass
except LLMError as e:
    error_msg = ERROR_MESSAGES.get(e.error_type, ERROR_MESSAGES["unknown"])
    # Handle error
```

**Error Types:**

- `llm_rate_limit` - Rate limit exceeded
- `llm_timeout` - Request timeout
- `model_unavailable` - Model not available
- `moderation_blocked` - Content blocked by moderation
- `unknown` - Unknown error

### `bot.utils.formatting`

Formatting utilities for messages and responses.

### `bot.utils.triggers`

Trigger detection utilities for group chats.

### `bot.utils.commands`

Command setup utilities.

```python
from bot.utils.commands import setup_bot_commands

await setup_bot_commands(bot)
```

### `bot.utils.logging.setup_logging()`

Setup logging configuration.

```python
from bot.utils.logging import setup_logging

setup_logging()
```

## Main Entry Point

### `bot.main`

Main entry point for the bot.

**Functions:**

- `create_bot() -> Bot` - Create and configure bot instance
- `create_dispatcher() -> Dispatcher` - Create and configure dispatcher
- `main() -> None` - Main entry point (async)

**Startup Sequence:**

1. Setup logging
2. Create bot and dispatcher
3. Register startup/shutdown hooks
4. Initialize database
5. Initialize Redis
6. Start scheduler
7. Start polling

**Usage:**

```python
# Run directly
python -m bot.main

# Or use asyncio
import asyncio
from bot.main import main

asyncio.run(main())
```

## Related Documentation

- [Architecture](architecture.md) - System architecture overview
- [Development Guide](development.md) - Development setup and guidelines
- [Database Schema](database.md) - Complete database documentation