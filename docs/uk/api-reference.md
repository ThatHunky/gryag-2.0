# API Reference

Цей документ надає детальну довідку API для ключових модулів, класів та методів у коді Гряг 2.0.

## Зміст

- [Конфігурація](#конфігурація)
- [База даних](#база-даних)
- [Керування контекстом](#керування-контекстом)
- [LLM клієнт](#llm-клієнт)
- [Інструменти](#інструменти)
- [Обробники](#обробники)
- [Middlewares](#middlewares)
- [Утиліти](#утиліти)

## Конфігурація

### `bot.config.Settings`

Основний клас конфігурації, що використовує Pydantic Settings.

```python
from bot.config import get_settings

settings = get_settings()
```

**Ключові властивості:**

- `telegram_bot_token: str` - Токен Telegram бота (обов'язково)
- `llm_api_key: str` - API ключ LLM (обов'язково)
- `llm_base_url: str` - Базова URL API LLM
- `llm_model: str` - Основна модель LLM
- `database_url: str` - URL підключення до PostgreSQL
- `admin_ids: list[int]` - ID адмінів (властивість, парситься з рядка через кому)

## База даних

### Керування сесіями

#### `bot.db.session.get_session()`

Асинхронний контекстний менеджер для сесій бази даних.

```python
from bot.db.session import get_session

async with get_session() as session:
    # Використовуйте сесію
    pass
```

### Репозиторії

Всі репозиторії слідують тому ж патерну: вони приймають `AsyncSession` у конструкторі та надають асинхронні методи для операцій з базою даних.

#### `bot.db.repositories.ChatRepository`

Репозиторій для операцій з чатами.

**Методи:**

- `get_by_id(chat_id: int) -> Chat | None` - Отримати чат за ID
- `get_or_create(...) -> Chat` - Отримати або створити чат
- `update(chat: Chat) -> Chat` - Оновити чат

#### `bot.db.repositories.MessageRepository`

Репозиторій для операцій з повідомленнями.

**Методи:**

- `add(...) -> Message` - Додати нове повідомлення
- `get_recent(chat_id: int, limit: int = 100) -> list[Message]` - Отримати останні повідомлення
- `get_since(chat_id: int, since: datetime) -> list[Message]` - Отримати повідомлення з дати

## Керування контекстом

### `bot.context.manager.ContextManager`

Керує збіркою контексту для запитів LLM.

**Конструктор:**

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

**Методи:**

- `build_context() -> list[dict]` - Побудувати повний контекст для LLM

## LLM клієнт

### `bot.llm.client.LLMClient`

LLM клієнт сумісний з OpenAI з функціями надійності.

**Конструктор:**

```python
from bot.llm import LLMClient

llm_client = LLMClient()
```

**Методи:**

#### `complete()`

Завершити розмову в чаті (без виклику інструментів).

```python
response = await llm_client.complete(
    messages=[{"role": "user", "content": "Привіт!"}],
    max_tokens=500
)
```

#### `complete_with_tools()`

Завершити з підтримкою виклику інструментів.

```python
result = await llm_client.complete_with_tools(
    messages=[...],
    tools=[...],
    max_tokens=2048
)
```

**Повертає:** `dict` з ключами:
- `content: str` - Повідомлення асистента (може бути порожнім)
- `tool_calls: list[dict]` - Список викликів інструментів

## Інструменти

### `bot.tools.base.BaseTool`

Абстрактний базовий клас для всіх інструментів.

**Обов'язкові атрибути:**

- `name: str` - Назва інструменту
- `description: str` - Опис
- `parameters: dict` - JSON Schema для параметрів

**Обов'язкові методи:**

- `execute(**kwargs) -> ToolResult` - Виконати інструмент

### `bot.tools.registry.ToolRegistry`

Реєстр для керування та виявлення інструментів.

**Методи:**

- `register(tool: BaseTool) -> None` - Зареєструвати інструмент
- `get(name: str) -> BaseTool | None` - Отримати інструмент за назвою
- `execute(name: str, **kwargs) -> ToolResult` - Виконати інструмент за назвою

## Обробники

### Базові функції обробників

#### `bot.handlers.base.extract_user_info()`

Витягти інформацію про користувача з повідомлення.

```python
from bot.handlers.base import extract_user_info

user_info = extract_user_info(message)
# Повертає: {"id": int, "username": str | None, "full_name": str}
```

## Middlewares

### `bot.middlewares.access_control.AccessControlMiddleware`

Middleware багатошарового контролю доступу.

**Шари:**

1. Обхід для адмінів
2. Перевірка обмежень користувачів (бани/обмеження)
3. Перевірка чорного списку
4. Перевірка режиму доступу (global/private/whitelist)

### `bot.middlewares.rate_limit.RateLimitMiddleware`

Middleware обмеження частоти для не-адмінів.

## Пов'язана документація

- [Архітектура](architecture.md) - Огляд архітектури системи
- [Посібник з розробки](development.md) - Налаштування середовища розробки та керівні принципи
- [Схема бази даних](database.md) - Повна документація бази даних
