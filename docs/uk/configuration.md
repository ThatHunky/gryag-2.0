# Конфігурація

Проект використовує Pydantic Settings для керування конфігурацією через змінні оточення або файл `.env`. Вся конфігурація завантажується зі змінних оточення, з підтримкою файлу `.env` для локальної розробки.

## Завантаження конфігурації

Конфігурація завантажується в наступному порядку (пізніші значення перевизначають попередні):
1. Змінні оточення
2. Файл `.env` (якщо присутній)
3. Значення за замовчуванням (якщо вказані)

## Основні налаштування

### Telegram Бот

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Токен бота від @BotFather | **Обов'язково** | Має бути валідним токеном Telegram бота |
| `BOT_TRIGGER_KEYWORDS` | Ключові слова для виклику бота в групах (через кому) | `gryag,грягі,griag` | Регістронезалежне співставлення |
| `ADMIN_IDS` | ID користувачів Telegram з правами адміністратора (через кому) | `""` | Цілі числа, розділені комами |

**Приклад:**
```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
BOT_TRIGGER_KEYWORDS=gryag,грягі,griag,бот
ADMIN_IDS=12345678,87654321,11111111
```

## Налаштування LLM

### Основні налаштування LLM

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `LLM_API_KEY` | API ключ для провайдера LLM | **Обов'язково** | Має бути валідним API ключем |
| `LLM_BASE_URL` | Базова URL-адреса для OpenAI-сумісного API | `https://api.openai.com/v1` | Має бути валідною HTTP(S) URL |
| `LLM_MODEL` | Основна модель ШІ | `gpt-4o` | Назва моделі, підтримувана провайдером |
| `LLM_MAX_RESPONSE_TOKENS` | Максимальна кількість токенів у відповіді LLM | `2048` | 256-16384 |
| `LLM_TIMEOUT_SECONDS` | Таймаут запиту в секундах | `60` | 10-300 |
| `LLM_MAX_RETRIES` | Максимальна кількість повторних спроб при збої | `3` | 0-10 |
| `LLM_FALLBACK_MODEL` | Резервна модель, якщо основна не працює | `None` | Опціональна назва моделі |

### Налаштування зору

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `LLM_VISION_ENABLED` | Увімкнути можливості зору | `True` | Boolean |
| `LLM_VISION_MODEL` | Модель для розпізнавання зображень | `None` | Використовує `LLM_MODEL`, якщо не встановлено |
| `LLM_VISION_BASE_URL` | Базова URL для API зору | `None` | Використовує `LLM_BASE_URL`, якщо не встановлено |
| `LLM_VISION_API_KEY` | API ключ для API зору | `None` | Використовує `LLM_API_KEY`, якщо не встановлено |

### Сумаризація

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `LLM_SUMMARIZATION_MODEL` | Модель для сумаризації контексту | `gpt-4o-mini` | Зазвичай дешевша/швидша модель |

### Режим міркування

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `LLM_REASONING_ENABLED` | Увімкнути розширене міркування/думку | `True` | Boolean |
| `LLM_REASONING_EFFORT` | Рівень зусиль міркування | `medium` | `low`, `medium`, або `high` |

**Примітка:** Режим міркування використовується тільки з моделями, що його підтримують (наприклад, серія o1, o3).

### Структурований вивід

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `LLM_STRUCTURED_OUTPUT` | Використовувати JSON схему для відповідей | `True` | Boolean |
| `LLM_STRUCTURED_INPUT` | Використовувати структурований формат вводу | `False` | Boolean |

**Приклад конфігурації LLM:**
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

## База даних та Redis

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | URL підключення до PostgreSQL | `postgresql+asyncpg://bot:bot@postgres:5432/gryag` | Має використовувати драйвер `asyncpg` |
| `REDIS_URL` | URL підключення до Redis | `redis://redis:6379/0` | Стандартний формат URL Redis |

**Приклади URL бази даних:**
```env
# Docker Compose (за замовчуванням)
DATABASE_URL=postgresql+asyncpg://bot:bot@postgres:5432/gryag

# Локальний PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/gryag

# Віддалений PostgreSQL з SSL
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/gryag?ssl=require

# Redis з паролем
REDIS_URL=redis://:password@redis:6379/0
```

## Керування контекстом

### Негайний контекст

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `IMMEDIATE_CONTEXT_MESSAGES` | Кількість останніх повідомлень у контексті | `100` | 10-500 |
| `CONTEXT_MAX_TOKENS` | Максимальна кількість токенів для всього контексту | `8000` | 2000-128000 |

### Сумаризація

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `RECENT_SUMMARY_TOKENS` | Макс. токенів для 7-денного підсумку | `1024` | 256-4096 |
| `RECENT_SUMMARY_INTERVAL_DAYS` | Днів між 7-денними підсумками | `3` | 1-7 |
| `LONG_SUMMARY_TOKENS` | Макс. токенів для 30-денного підсумку | `4096` | 1024-16384 |
| `LONG_SUMMARY_INTERVAL_DAYS` | Днів між 30-денними підсумками | `14` | 7-30 |

### Пам'ять користувача

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `USER_MEMORY_MAX_FACTS` | Максимальна кількість фактів на користувача | `50` | 10-100 |

**Приклад конфігурації контексту:**
```env
IMMEDIATE_CONTEXT_MESSAGES=100
CONTEXT_MAX_TOKENS=8000
RECENT_SUMMARY_TOKENS=1024
RECENT_SUMMARY_INTERVAL_DAYS=3
LONG_SUMMARY_TOKENS=4096
LONG_SUMMARY_INTERVAL_DAYS=14
USER_MEMORY_MAX_FACTS=50
```

## Контроль доступу

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `ACCESS_MODE` | Режим контролю доступу | `global` | `global`, `private`, або `whitelist` |
| `WHITELIST_CHATS` | ID чатів у білому списку (через кому) | `""` | Цілі числа (використовується при `ACCESS_MODE=whitelist`) |
| `BLACKLIST_USERS` | ID користувачів у чорному списку (через кому) | `""` | Цілі числа |

**Режими доступу:**
- `global`: Бот відповідає в усіх чатах (за замовчуванням)
- `private`: Бот відповідає тільки в приватних чатах
- `whitelist`: Бот відповідає тільки в чатах з білого списку (та приватних чатах)

**Приклад:**
```env
ACCESS_MODE=whitelist
WHITELIST_CHATS=-1001234567890,-1009876543210
BLACKLIST_USERS=11111111,22222222
```

## Обмеження частоти

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `RATE_LIMIT_ENABLED` | Увімкнути обмеження частоти | `True` | Boolean |
| `RATE_LIMIT_PROMPTS` | Макс. запитів за період | `30` | 1-1000 |
| `RATE_LIMIT_WINDOW_HOURS` | Період у годинах | `1` | 1-24 |

**Примітка:** Адміністратори обходять обмеження частоти.

**Приклад:**
```env
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PROMPTS=30
RATE_LIMIT_WINDOW_HOURS=1
```

## Генерація зображень

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `IMAGE_GENERATION_ENABLED` | Увімкнути генерацію зображень | `True` | Boolean |
| `IMAGE_GENERATION_MODEL` | Модель генерації зображень | `dall-e-3` | Назва моделі |
| `IMAGE_GENERATION_BASE_URL` | Базова URL для API зображень | `None` | Використовує `LLM_BASE_URL` |

## Системний промпт

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `SYSTEM_PROMPT_FILE` | Ім'я файлу системного промпту | `default.md` | Має існувати в директорії `prompts/` |

Доступні файли промптів:
- `default.md`: Промпт за замовчуванням
- `assistant.md`: Промпт у стилі асистента
- `casual.md`: Промпт для неформальної розмови

## Логування

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `LOG_LEVEL` | Рівень логування | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | Формат логування | `json` | `json` або `text` |
| `LOG_FILE_ENABLED` | Увімкнути логування у файл | `True` | Boolean |
| `LOG_FILE_PATH` | Директорія файлів логів | `./data/logs` | Шлях до директорії |
| `LOG_FILE_RETENTION_DAYS` | Днів зберігання файлів логів | `7` | 1-30 |

**Приклад:**
```env
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=True
LOG_FILE_PATH=./data/logs
LOG_FILE_RETENTION_DAYS=7
```

## UX функції

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `TYPING_INDICATOR_ENABLED` | Показувати статус "друкує..." | `True` | Boolean |

## Модерація

| Змінна | Опис | За замовчуванням | Обмеження |
| :--- | :--- | :--- | :--- |
| `MODERATION_ENABLED` | Увімкнути модерацію контенту | `False` | Boolean |

## Повний приклад файлу .env

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

# База даних
DATABASE_URL=postgresql+asyncpg://bot:bot@postgres:5432/gryag
REDIS_URL=redis://redis:6379/0

# Контекст
IMMEDIATE_CONTEXT_MESSAGES=100
CONTEXT_MAX_TOKENS=8000
RECENT_SUMMARY_TOKENS=1024
LONG_SUMMARY_TOKENS=4096
USER_MEMORY_MAX_FACTS=50

# Контроль доступу
ACCESS_MODE=global
WHITELIST_CHATS=
BLACKLIST_USERS=

# Обмеження частоти
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PROMPTS=30
RATE_LIMIT_WINDOW_HOURS=1

# Функції
IMAGE_GENERATION_ENABLED=True
TYPING_INDICATOR_ENABLED=True
MODERATION_ENABLED=False

# Системний промпт
SYSTEM_PROMPT_FILE=default.md

# Логування
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE_ENABLED=True
LOG_FILE_PATH=./data/logs
```

## Сценарії конфігурації

### Сценарій 1: Налаштування для розробки

```env
LOG_LEVEL=DEBUG
LOG_FORMAT=text
ACCESS_MODE=private
RATE_LIMIT_ENABLED=False
```

### Сценарій 2: Продакшн з обмеженим доступом

```env
ACCESS_MODE=whitelist
WHITELIST_CHATS=-1001234567890
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PROMPTS=20
MODERATION_ENABLED=True
LOG_LEVEL=WARNING
```

### Сценарій 3: Високопродуктивне налаштування

```env
IMMEDIATE_CONTEXT_MESSAGES=200
CONTEXT_MAX_TOKENS=16000
LLM_MAX_RESPONSE_TOKENS=4096
LLM_TIMEOUT_SECONDS=120
```

### Сценарій 4: Оптимізоване за вартістю налаштування

```env
LLM_MODEL=gpt-4o-mini
LLM_SUMMARIZATION_MODEL=gpt-4o-mini
IMMEDIATE_CONTEXT_MESSAGES=50
CONTEXT_MAX_TOKENS=4000
RECENT_SUMMARY_TOKENS=512
LONG_SUMMARY_TOKENS=2048
```

## Усунення проблем конфігурації

### Проблема: Бот не запускається

**Симптоми:** Бот не запускається або падає одразу.

**Рішення:**
1. Перевірте, що `TELEGRAM_BOT_TOKEN` правильний і не застарів
2. Перевірте, що `LLM_API_KEY` валідний
3. Переконайтеся, що `DATABASE_URL` доступний
4. Перевірте файли логів у `LOG_FILE_PATH` на помилки

### Проблема: Помилки підключення до бази даних

**Симптоми:** Помилки `Failed to initialize database`.

**Рішення:**
1. Перевірте, що PostgreSQL запущений
2. Перевірте формат `DATABASE_URL`: `postgresql+asyncpg://user:pass@host:port/db`
3. Переконайтеся, що база даних існує
4. Перевірте мережеву з'єднуваність (файрвол, Docker мережа)

### Проблема: Помилки LLM API

**Симптоми:** Помилки `LLM error` або `model_unavailable`.

**Рішення:**
1. Перевірте, що `LLM_API_KEY` валідний
2. Перевірте, що `LLM_BASE_URL` правильний
3. Перевірте, що назва моделі існує: `LLM_MODEL`
4. Перевірте квоту/ліміти API
5. Увімкніть резервну модель: `LLM_FALLBACK_MODEL=gpt-4o-mini`

### Проблема: Обмеження частоти занадто суворі

**Симптоми:** Користувачі часто отримують помилки обмеження частоти.

**Рішення:**
1. Збільште `RATE_LIMIT_PROMPTS`
2. Збільште `RATE_LIMIT_WINDOW_HOURS`
3. Тимчасово вимкніть: `RATE_LIMIT_ENABLED=False` (не рекомендується для продакшн)

### Проблема: Контекст занадто великий

**Симптоми:** Помилки перевищення `context_max_tokens`.

**Рішення:**
1. Зменште `IMMEDIATE_CONTEXT_MESSAGES`
2. Зменште `CONTEXT_MAX_TOKENS`
3. Зменште ліміти токенів підсумків
4. Увімкніть більш часті підсумки

### Проблема: Бот не відповідає в групах

**Симптоми:** Бот працює в приватних чатах, але не в групах.

**Рішення:**
1. Перевірте, що `ACCESS_MODE` не `private`
2. Перевірте, що `BOT_TRIGGER_KEYWORDS` містить очікувані ключові слова
3. Переконайтеся, що бот доданий до групи
4. Перевірте, чи група в білому списку (якщо `ACCESS_MODE=whitelist`)

### Проблема: Зір не працює

**Симптоми:** Бот не обробляє зображення.

**Рішення:**
1. Перевірте, що `LLM_VISION_ENABLED=True`
2. Перевірте, що `LLM_VISION_MODEL` встановлено або правильно відступає
3. Перевірте API ключ зору, якщо окремий: `LLM_VISION_API_KEY`
4. Перевірте, що модель підтримує зір

## Пріоритет змінних оточення

Значення конфігурації вирішуються в такому порядку (від найвищого до найнижчого пріоритету):

1. Змінні оточення (система/оточення)
2. Файл `.env`
3. Значення за замовчуванням (з `bot/config.py`)

Це означає, що змінні оточення завжди перевизначають значення файлу `.env`, що корисно для продакшн розгортань.

## Валідація

Всі значення конфігурації валідуються при запуску:
- Перевірка типів (int, str, bool, тощо)
- Валідація діапазону (мін/макс для числових значень)
- Валідація enum (для виборів типу `ACCESS_MODE`)
- Перевірка обов'язкових полів

Невірна конфігурація призведе до збою бота при запуску з чітким повідомленням про помилку, що вказує, яка змінна невалідна.

## Пов'язана документація

- [Посібник з розгортання](deployment.md) - Розгляди розгортання в продакшн
- [Архітектура](architecture.md) - Огляд архітектури системи
- [Керування контекстом](context-management.md) - Деталі системи контексту
