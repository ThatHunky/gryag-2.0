# Configuration

The project uses Pydantic Settings for configuration management via environment variables or a `.env` file. All configuration is loaded from environment variables, with support for a `.env` file for local development.

## Configuration Loading

Configuration is loaded in the following order (later values override earlier ones):

1. Environment variables
2. `.env` file (if present)
3. Default values (if specified)

## General Settings

### Telegram Bot

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | **Required** | Must be valid Telegram bot token |
| `BOT_TRIGGER_KEYWORDS` | Keywords that trigger the bot in group chats (comma-separated) | `gryag,гряг,griag` | Case-insensitive matching |
| `ADMIN_IDS` | Telegram user IDs with admin privileges (comma-separated) | `""` | Integer IDs separated by commas |

**Example:**

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_TRIGGER_KEYWORDS=gryag,гряг,griag,бот
ADMIN_IDS=12345678,87654321,11111111
```

## LLM Configuration

### Primary LLM Settings

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `LLM_API_KEY` | API key for the LLM provider | **Required** | Must be valid API key |
| `LLM_BASE_URL` | Base URL for OpenAI-compatible API | `https://api.openai.com/v1` | Must be valid HTTP(S) URL |
| `LLM_MODEL` | Primary AI model | `gpt-4o` | Model name supported by provider |
| `LLM_MAX_RESPONSE_TOKENS` | Maximum tokens in LLM response | `2048` | 256-16384 |
| `LLM_TIMEOUT_SECONDS` | Request timeout in seconds | `60` | 10-300 |
| `LLM_MAX_RETRIES` | Maximum retry attempts on failure | `3` | 0-10 |
| `LLM_FALLBACK_MODEL` | Fallback model if primary fails | `None` | Optional model name |

### Vision Configuration

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `LLM_VISION_ENABLED` | Enable vision capabilities | `True` | Boolean |
| `LLM_VISION_MODEL` | Model for image recognition | `None` | Falls back to `LLM_MODEL` if not set |
| `LLM_VISION_BASE_URL` | Base URL for vision API | `None` | Falls back to `LLM_BASE_URL` if not set |
| `LLM_VISION_API_KEY` | API key for vision API | `None` | Falls back to `LLM_API_KEY` if not set |

### Summarization

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `LLM_SUMMARIZATION_MODEL` | Model for context summarization | `gpt-4o-mini` | Typically a cheaper/faster model |

### Reasoning Mode

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `LLM_REASONING_ENABLED` | Enable extended thinking/reasoning | `True` | Boolean |
| `LLM_REASONING_EFFORT` | Reasoning effort level | `medium` | `low`, `medium`, or `high` |

**Note:** Reasoning mode is only used with models that support it (e.g., o1, o3 series).

### Structured Output

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `LLM_STRUCTURED_OUTPUT` | Use JSON schema for responses | `True` | Boolean |
| `LLM_STRUCTURED_INPUT` | Use structured input format | `False` | Boolean |

**Example LLM Configuration:**

```env
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_VISION_MODEL=gpt-4o
LLM_SUMMARIZATION_MODEL=gpt-4o-mini
LLM_REASONING_ENABLED=True
LLM_REASONING_EFFORT=medium
LLM_MAX_RESPONSE_TOKENS=2048
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=3
```

## Database & Redis

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql+asyncpg://bot:bot@postgres:5432/gryag` | Must use `asyncpg` driver |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379/0` | Standard Redis URL format |

**Example Database URLs:**

```env
# Docker Compose (default)
DATABASE_URL=postgresql+asyncpg://bot:bot@postgres:5432/gryag

# Local PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/gryag

# Remote PostgreSQL with SSL
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/gryag?ssl=require

# Redis with password
REDIS_URL=redis://:password@redis:6379/0
```

## Context Management

### Immediate Context

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `IMMEDIATE_CONTEXT_MESSAGES` | Number of recent messages in context | `100` | 10-500 |
| `CONTEXT_MAX_TOKENS` | Maximum tokens for entire context | `8000` | 2000-128000 |

### Summarization

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `RECENT_SUMMARY_TOKENS` | Max tokens for 7-day summary | `1024` | 256-4096 |
| `RECENT_SUMMARY_INTERVAL_DAYS` | Days between 7-day summaries | `3` | 1-7 |
| `LONG_SUMMARY_TOKENS` | Max tokens for 30-day summary | `4096` | 1024-16384 |
| `LONG_SUMMARY_INTERVAL_DAYS` | Days between 30-day summaries | `14` | 7-30 |

### User Memory

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `USER_MEMORY_MAX_FACTS` | Maximum facts stored per user | `50` | 10-100 |

**Example Context Configuration:**

```env
IMMEDIATE_CONTEXT_MESSAGES=100
CONTEXT_MAX_TOKENS=8000
RECENT_SUMMARY_TOKENS=1024
RECENT_SUMMARY_INTERVAL_DAYS=3
LONG_SUMMARY_TOKENS=4096
LONG_SUMMARY_INTERVAL_DAYS=14
USER_MEMORY_MAX_FACTS=50
```

## Access Control

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `ACCESS_MODE` | Access control mode | `global` | `global`, `private`, or `whitelist` |
| `WHITELIST_CHATS` | Whitelisted chat IDs (comma-separated) | `""` | Integer IDs (used when `ACCESS_MODE=whitelist`) |
| `BLACKLIST_USERS` | Blacklisted user IDs (comma-separated) | `""` | Integer IDs |

**Access Modes:**

- `global`: Bot responds in all chats (default)
- `private`: Bot only responds in private chats
- `whitelist`: Bot only responds in whitelisted chats (and private chats)

**Example:**

```env
ACCESS_MODE=whitelist
WHITELIST_CHATS=-1001234567890,-1009876543210
BLACKLIST_USERS=11111111,22222222
```

## Rate Limiting

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `True` | Boolean |
| `RATE_LIMIT_PROMPTS` | Max requests per window | `30` | 1-1000 |
| `RATE_LIMIT_WINDOW_HOURS` | Time window in hours | `1` | 1-24 |

**Note:** Admins bypass rate limiting.

**Example:**

```env
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PROMPTS=30
RATE_LIMIT_WINDOW_HOURS=1
```

## Image Generation

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `IMAGE_GENERATION_ENABLED` | Enable image generation | `True` | Boolean |
| `IMAGE_GENERATION_MODEL` | Image generation model | `dall-e-3` | Model name |
| `IMAGE_GENERATION_BASE_URL` | Base URL for image API | `None` | Falls back to `LLM_BASE_URL` |

## System Prompt

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `SYSTEM_PROMPT_FILE` | System prompt file name | `default.md` | Must exist in `prompts/` directory |

Available prompt files:

- `default.md`: Default system prompt
- `assistant.md`: Assistant-style prompt
- `casual.md`: Casual conversation prompt

## Logging

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | Log format | `json` | `json` or `text` |
| `LOG_FILE_ENABLED` | Enable file logging | `True` | Boolean |
| `LOG_FILE_PATH` | Log file directory | `./data/logs` | Directory path |
| `LOG_FILE_RETENTION_DAYS` | Days to keep log files | `7` | 1-30 |

**Example:**

```env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=True
LOG_FILE_PATH=./data/logs
LOG_FILE_RETENTION_DAYS=7
```

## UX Features

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `TYPING_INDICATOR_ENABLED` | Show "typing..." status | `True` | Boolean |

## Moderation

| Variable | Description | Default | Constraints |
| :--- | :--- | :--- | :--- |
| `MODERATION_ENABLED` | Enable content moderation | `False` | Boolean |

## Complete Example .env File

```env
# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_TRIGGER_KEYWORDS=gryag,грягі,griag
ADMIN_IDS=12345678,87654321

# LLM
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
LLM_VISION_MODEL=gpt-4o
LLM_SUMMARIZATION_MODEL=gpt-4o-mini
LLM_REASONING_ENABLED=True
LLM_REASONING_EFFORT=medium
LLM_MAX_RESPONSE_TOKENS=2048
LLM_TIMEOUT_SECONDS=60
LLM_MAX_RETRIES=3

# Database
DATABASE_URL=postgresql+asyncpg://bot:bot@postgres:5432/gryag
REDIS_URL=redis://redis:6379/0

# Context
IMMEDIATE_CONTEXT_MESSAGES=100
CONTEXT_MAX_TOKENS=8000
RECENT_SUMMARY_TOKENS=1024
LONG_SUMMARY_TOKENS=4096
USER_MEMORY_MAX_FACTS=50

# Access Control
ACCESS_MODE=global
WHITELIST_CHATS=
BLACKLIST_USERS=

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PROMPTS=30
RATE_LIMIT_WINDOW_HOURS=1

# Features
IMAGE_GENERATION_ENABLED=True
TYPING_INDICATOR_ENABLED=True
MODERATION_ENABLED=False

# System Prompt
SYSTEM_PROMPT_FILE=default.md

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=True
LOG_FILE_PATH=./data/logs
```

## Configuration Scenarios

### Scenario 1: Development Setup

```env
LOG_LEVEL=DEBUG
LOG_FORMAT=text
ACCESS_MODE=private
RATE_LIMIT_ENABLED=False
```

### Scenario 2: Production with Restricted Access

```env
ACCESS_MODE=whitelist
WHITELIST_CHATS=-1001234567890
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PROMPTS=20
MODERATION_ENABLED=True
LOG_LEVEL=WARNING
```

### Scenario 3: High-Performance Setup

```env
IMMEDIATE_CONTEXT_MESSAGES=200
CONTEXT_MAX_TOKENS=16000
LLM_MAX_RESPONSE_TOKENS=4096
LLM_TIMEOUT_SECONDS=120
```

### Scenario 4: Cost-Optimized Setup

```env
LLM_MODEL=gpt-4o-mini
LLM_SUMMARIZATION_MODEL=gpt-4o-mini
IMMEDIATE_CONTEXT_MESSAGES=50
CONTEXT_MAX_TOKENS=4000
RECENT_SUMMARY_TOKENS=512
LONG_SUMMARY_TOKENS=2048
```

## Troubleshooting Configuration Issues

### Issue: Bot Not Starting

**Symptoms:** Bot fails to start or crashes immediately.

**Solutions:**

1. Verify `TELEGRAM_BOT_TOKEN` is correct and not expired
2. Check `LLM_API_KEY` is valid
3. Ensure `DATABASE_URL` is accessible
4. Check log files in `LOG_FILE_PATH` for errors

### Issue: Database Connection Errors

**Symptoms:** `Failed to initialize database` errors.

**Solutions:**

1. Verify PostgreSQL is running
2. Check `DATABASE_URL` format: `postgresql+asyncpg://user:pass@host:port/db`
3. Ensure database exists
4. Check network connectivity (firewall, Docker networking)

### Issue: LLM API Errors

**Symptoms:** `LLM error` or `model_unavailable` errors.

**Solutions:**

1. Verify `LLM_API_KEY` is valid
2. Check `LLM_BASE_URL` is correct
3. Verify model name exists: `LLM_MODEL`
4. Check API quota/rate limits
5. Enable fallback model: `LLM_FALLBACK_MODEL=gpt-4o-mini`

### Issue: Rate Limiting Too Strict

**Symptoms:** Users getting rate limit errors frequently.

**Solutions:**

1. Increase `RATE_LIMIT_PROMPTS`
2. Increase `RATE_LIMIT_WINDOW_HOURS`
3. Disable temporarily: `RATE_LIMIT_ENABLED=False` (not recommended for production)

### Issue: Context Too Large

**Symptoms:** `context_max_tokens` exceeded errors.

**Solutions:**

1. Reduce `IMMEDIATE_CONTEXT_MESSAGES`
2. Reduce `CONTEXT_MAX_TOKENS`
3. Reduce summary token limits
4. Enable more frequent summarization

### Issue: Bot Not Responding in Groups

**Symptoms:** Bot works in private chats but not groups.

**Solutions:**

1. Check `ACCESS_MODE` is not `private`
2. Verify `BOT_TRIGGER_KEYWORDS` includes expected keywords
3. Ensure bot is added to group
4. Check if group is in whitelist (if `ACCESS_MODE=whitelist`)

### Issue: Vision Not Working

**Symptoms:** Bot doesn't process images.

**Solutions:**

1. Verify `LLM_VISION_ENABLED=True`
2. Check `LLM_VISION_MODEL` is set or falls back correctly
3. Verify vision API key if separate: `LLM_VISION_API_KEY`
4. Check model supports vision

## Environment Variable Precedence

Configuration values are resolved in this order (highest to lowest priority):

1. Environment variables (system/environment)
2. `.env` file
3. Default values (from `bot/config.py`)

This means environment variables always override `.env` file values, which is useful for production deployments.

## Validation

All configuration values are validated on startup:

- Type checking (int, str, bool, etc.)
- Range validation (min/max for numeric values)
- Enum validation (for choices like `ACCESS_MODE`)
- Required field checking

Invalid configuration will cause the bot to fail on startup with a clear error message indicating which variable is invalid.

## Related Documentation

- [Deployment Guide](deployment.md) - Production deployment considerations
- [Architecture](architecture.md) - System architecture overview
- [Context Management](context-management.md) - Context system details
