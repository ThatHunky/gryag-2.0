# Архітектура

Цей документ надає комплексний огляд архітектури бота Гряг 2.0, включаючи системні компоненти, потоки даних та патерни проектування.

## Огляд системи

Гряг 2.0 — це складний Telegram бот, побудований на Python та aiogram 3.x, що має такі особливості:

- **Розширене керування контекстом**: Багатошаровий контекст з історією, підсумками та пам'яттю користувачів
- **Інтеграція LLM**: Клієнт сумісний з OpenAI API з функціями надійності
- **Виклик інструментів**: Розширювана система інструментів для калькулятора, погоди, генерації зображень та іншого
- **Контроль доступу**: Багатошаровий захист з адмін-контролем, обмеженням частоти та білими/чорними списками
- **Персистентність даних**: PostgreSQL для повідомлень, користувачів, чатів, підсумків та пам'яті
- **Кешування**: Інтеграція Redis для оптимізації продуктивності

## Високорівнева архітектура

```mermaid
graph TB
    Telegram[Telegram API] --> Bot[Bot Instance]
    Bot --> Dispatcher[Dispatcher]
    Dispatcher --> Middleware[Middleware Chain]
    Middleware --> Handlers[Message Handlers]
    Handlers --> ContextManager[Context Manager]
    ContextManager --> LLMClient[LLM Client]
    LLMClient --> Tools[Tool Registry]
    Tools --> ExternalAPIs[External APIs]
    ContextManager --> Database[(PostgreSQL)]
    Handlers --> Database
    Tools --> Database
    Middleware --> Redis[(Redis Cache)]
    LLMClient --> LLMProvider[LLM Provider API]
```

## Архітектура компонентів

### 1. Ініціалізація бота (`bot/main.py`)

Бот слідує структурованій послідовності запуску:

```mermaid
sequenceDiagram
    participant Main
    participant Bot
    participant DB
    participant Redis
    participant Scheduler
    participant LLM

    Main->>Bot: Create Bot & Dispatcher
    Main->>Bot: Register Middlewares
    Main->>Bot: Register Routers
    Main->>Bot: Start Polling
    Bot->>DB: Initialize Database
    Bot->>Redis: Connect to Redis
    Bot->>Scheduler: Start Background Tasks
    Bot->>LLM: Initialize LLM Client
    Bot->>Bot: Setup Commands
```

**Ключові обов'язки:**
- Аутентифікація та валідація бота
- Ініціалізація бази даних та міграції
- Налаштування підключення Redis
- Запуск фонового планувальника
- Реєстрація команд

### 2. Ланцюг Middleware

Повідомлення проходять через middleware у певному порядку:

```mermaid
graph LR
    Message[Incoming Message] --> Logging[LoggingMiddleware]
    Logging --> AccessControl[AccessControlMiddleware]
    AccessControl --> RateLimit[RateLimitMiddleware]
    RateLimit --> Handler[Message Handler]
```

**Компоненти Middleware:**

1. **LoggingMiddleware** (`bot/middlewares/logging.py`)
   - Логує всі вхідні повідомлення
   - Відстежує активність користувачів
   - Записує помилки

2. **AccessControlMiddleware** (`bot/middlewares/access_control.py`)
   - Обхід для адмінів
   - Валідація обмежень користувачів (бани/обмеження)
   - Перевірка чорного списку
   - Застосування режиму доступу (global/private/whitelist)

3. **RateLimitMiddleware** (`bot/middlewares/rate_limit.py`)
   - Обмеження частоти для не-адмінів
   - Налаштовувані ліміти (запитів за період)
   - Обхід для адмінів

### 3. Потік обробки повідомлень

```mermaid
sequenceDiagram
    participant User
    participant Telegram
    participant Middleware
    participant Handler
    participant ContextMgr
    participant LLM
    participant Tools
    participant DB

    User->>Telegram: Send Message
    Telegram->>Middleware: Process Message
    Middleware->>Middleware: Access Control
    Middleware->>Middleware: Rate Limit
    Middleware->>Handler: Route to Handler
    Handler->>DB: Store Message
    Handler->>ContextMgr: Build Context
    ContextMgr->>DB: Fetch History
    ContextMgr->>DB: Fetch Summaries
    ContextMgr->>DB: Fetch Memories
    ContextMgr->>Handler: Return Context
    Handler->>LLM: Request with Context
    LLM->>Tools: Tool Call (if needed)
    Tools->>ExternalAPIs: Execute Tool
    Tools->>LLM: Return Result
    LLM->>Handler: Final Response
    Handler->>DB: Store Response
    Handler->>Telegram: Send Response
    Telegram->>User: Display Message
```

### 4. Система керування контекстом

Система керування контекстом збирає комплексний контекст для LLM:

```mermaid
graph TB
    Request[User Message] --> ContextMgr[ContextManager]
    ContextMgr --> SystemPrompt[System Prompt]
    ContextMgr --> Summaries[Summaries]
    ContextMgr --> Immediate[Immediate Context]
    ContextMgr --> Memories[User Memories]
    ContextMgr --> Visual[Visual Context]
    
    SystemPrompt --> Variables[Variable Substitution]
    Summaries --> Recent[7-day Summary]
    Summaries --> Long[30-day Summary]
    Immediate --> LastN[Last N Messages]
    Memories --> UserFacts[User Facts]
    Visual --> Image[Image URL]
    
    Variables --> Final[Final Context]
    Recent --> Final
    Long --> Final
    LastN --> Final
    UserFacts --> Final
    Image --> Final
```

**Шари контексту:**

1. **System Prompt** (`bot/context/permanent.py`)
   - Базові інструкції для бота
   - Підстановка змінних (ім'я користувача, назва чату тощо)
   - Опис інструментів
   - Керівні принципи поведінки

2. **Summaries** (`bot/context/summarizer.py`)
   - 7-денний підсумок: Недавній контекст (за замовчуванням: 1024 токени)
   - 30-денний підсумок: Довгостроковий контекст (за замовчуванням: 4096 токенів)
   - Генерується періодично фоновим планувальником

3. **Immediate Context** (`bot/context/immediate.py`)
   - Останні N повідомлень (за замовчуванням: 100)
   - Форматовані з іменами користувачів та ланцюгами відповідей
   - Включає відповіді бота

4. **User Memories** (`bot/db/repositories/memories.py`)
   - Персистентні факти про користувачів (макс. 50 на користувача)
   - Зберігаються глобально в усіх чатах
   - Керуються через інструменти пам'яті

5. **Visual Context** (`bot/context/manager.py`)
   - URL зображень при відповіді на фото
   - Обробка моделлю зору

### 5. Система виклику інструментів

Бот використовує ітеративний цикл виклику інструментів:

```mermaid
sequenceDiagram
    participant Handler
    participant LLM
    participant Registry
    participant Tool
    participant External

    Handler->>LLM: Request with Tools
    LLM->>Handler: Response + Tool Calls
    alt Has Tool Calls
        Handler->>Registry: Execute Tool
        Registry->>Tool: Call execute()
        Tool->>External: API Call
        External->>Tool: Result
        Tool->>Registry: ToolResult
        Registry->>Handler: Result
        Handler->>LLM: Add Tool Result
        LLM->>Handler: New Response
    else No Tool Calls
        Handler->>Handler: Final Response
    end
```

**Tool Registry** (`bot/tools/registry.py`):
- Централізоване керування інструментами
- Автоматичне виявлення та реєстрація
- Генерація схем OpenAI
- Обробка помилок

**Доступні інструменти:**
1. **Calculator** (`bot/tools/calculator.py`): Безпечна математична обробка
2. **Weather** (`bot/tools/weather.py`): Інформація про погоду через Open-Meteo
3. **Search** (`bot/tools/search.py`): Веб-пошук через DuckDuckGo
4. **Image Generation** (`bot/tools/image.py`): Генерація зображень DALL-E 3
5. **Remember Memory** (`bot/tools/memory.py`): Зберігання фактів користувача
6. **Recall Memories** (`bot/tools/memory.py`): Отримання фактів користувача

### 6. Схема бази даних

```mermaid
erDiagram
    Chat ||--o{ Message : "has"
    Chat ||--o{ Summary : "has"
    User ||--o{ Message : "sends"
    User ||--o{ UserMemory : "has"
    User ||--o{ UserRestriction : "has"
    
    Chat {
        bigint id PK
        string title
        string chat_type
        int member_count
        bool is_active
        datetime created_at
        datetime updated_at
    }
    
    User {
        bigint id PK
        string username
        string full_name
        string pronouns
        bool is_admin
        datetime created_at
        datetime updated_at
    }
    
    Message {
        int id PK
        bigint telegram_message_id
        bigint chat_id FK
        bigint user_id FK
        text content
        string content_type
        bigint reply_to_message_id
        bool is_bot_message
        datetime created_at
    }
    
    Summary {
        int id PK
        bigint chat_id FK
        string summary_type
        text content
        int token_count
        datetime period_start
        datetime period_end
        datetime created_at
    }
    
    UserMemory {
        int id PK
        bigint user_id FK
        text fact
        datetime created_at
    }
    
    UserRestriction {
        int id PK
        bigint user_id FK
        string restriction_type
        text reason
        datetime expires_at
        bigint created_by
        bool is_active
        datetime created_at
    }
    
    AccessList {
        int id PK
        bigint entity_id
        string entity_type
        string list_type
        text reason
        bigint created_by
        datetime created_at
    }
```

**Патерн Repository:**
- Весь доступ до бази даних через класи репозиторіїв
- Розташовані в `bot/db/repositories/`
- Async SQLAlchemy 2.0 ORM
- Керування сесіями через контекстні менеджери

### 7. Архітектура LLM клієнта

```mermaid
graph TB
    Request[LLM Request] --> Client[LLMClient]
    Client --> Retry{Retry Logic}
    Retry --> API[API Call]
    API --> Success{Success?}
    Success -->|Yes| Response[Response]
    Success -->|No| Fallback{Fallback Model?}
    Fallback -->|Yes| Client
    Fallback -->|No| Error[Error]
    API --> RateLimit{Rate Limit?}
    RateLimit -->|Yes| Backoff[Exponential Backoff]
    Backoff --> Retry
    API --> Timeout{Timeout?}
    Timeout -->|Yes| Backoff
    
    Response --> Filter[Filter Thinking Tags]
    Filter --> Final[Final Response]
```

**Особливості:**
- Налаштовувана базова URL (сумісні з OpenAI API)
- Автоматичні повторні спроби з експоненційною затримкою
- Підтримка резервної моделі
- Обробка таймаутів запитів
- Керування лімітами токенів
- Підтримка моделей зору
- Підтримка режиму міркування (моделі o1/o3)

### 8. Архітектура обробників

**Структура Router:**
- `commands_router`: Команди бота (`/start`, `/help`, тощо)
- `admin_router`: Команди тільки для адмінів (приватні чати)
- `private_router`: Обробка повідомлень у приватних чатах
- `group_router`: Обробка повідомлень у групових чатах з тригерами

**Потік повідомлень у обробниках:**

1. **Витягти інформацію**: Інформація про користувача, чат, бота
2. **Зберегти повідомлення**: Зберегти в базу даних
3. **Побудувати контекст**: Зібрати повний контекст
4. **Обробка LLM**: 
   - Обробка зору (якщо є зображення)
   - Цикл виклику інструментів (до 5 ітерацій)
5. **Зберегти відповідь**: Зберегти повідомлення бота
6. **Надіслати відповідь**: Відповісти користувачу

### 9. Фоновий планувальник

Планувальник (`bot/context/scheduler.py`) виконує періодичні завдання:

- **Генерація підсумків**: Створює 7-денні та 30-денні підсумки
- **Завдання очищення**: Видаляє застарілі обмеження
- **Перевірки здоров'я**: Моніторить стан системи

## Патерни проектування

### 1. Патерн Repository
Всі операції з базою даних проходять через класи репозиторіїв:
- `ChatRepository`: Керування чатами
- `UserRepository`: Керування користувачами
- `MessageRepository`: Зберігання та отримання повідомлень
- `SummaryRepository`: Керування підсумками
- `MemoryRepository`: Керування пам'яттю користувачів

### 2. Патерн Middleware
Конвеєр обробки запитів з кількома шарами middleware для перехресних проблем.

### 3. Патерн Tool Registry
Централізоване керування інструментами з автоматичним виявленням та генерацією схем.

### 4. Патерн Context Builder
Структурована збірка контексту з кількох джерел даних.

### 5. Патерн Strategy
Різні обробники для різних типів чатів (приватний vs груповий).

## Приклади потоків даних

### Приклад 1: Просте текстове повідомлення

```
User → Telegram → LoggingMiddleware → AccessControlMiddleware → 
RateLimitMiddleware → PrivateRouter → Store Message → 
Build Context → LLM → Response → Store Response → Send
```

### Приклад 2: Повідомлення з викликом інструменту

```
User → Handler → Context → LLM → Tool Call Request →
Tool Registry → Calculator Tool → Result → 
LLM (with result) → Final Response → User
```

### Приклад 3: Групове повідомлення з тригером

```
User → GroupRouter → Trigger Check → 
(if triggered) → Same flow as private message
```

## Розгляди продуктивності

1. **Індексація бази даних**: Ключові поля індексовані для швидких запитів
2. **Ліміти контексту**: Налаштовувані ліміти токенів та повідомлень
3. **Кешування Redis**: Опціональна інтеграція Redis для кешування
4. **Пул підключень**: Пул підключень SQLAlchemy
5. **Асинхронні операції**: Всі операції I/O є асинхронними

## Архітектура безпеки

1. **Шари контролю доступу**:
   - Обхід для адмінів
   - Обмеження користувачів (бани/обмеження)
   - Чорний список
   - Режим доступу (global/private/whitelist)

2. **Обмеження частоти**: Запобігає зловживанням
3. **Валідація вводу**: Валідація параметрів інструментів
4. **Безпечне виконання**: Калькулятор використовує парсинг AST (без eval)

## Точки розширення

1. **Нові інструменти**: Реалізувати `BaseTool` та зареєструвати
2. **Нові обробники**: Створити router та зареєструвати в dispatcher
3. **Новий Middleware**: Реалізувати `BaseMiddleware`
4. **Користувацькі промпти**: Додати файли до директорії `prompts/`
5. **Моделі бази даних**: Додати до `bot/db/models.py` та створити міграцію

## Пов'язана документація

- [Керування контекстом](context-management.md) - Поглиблений розгляд системи контексту
- [Схема бази даних](database.md) - Повна документація бази даних
- [Розробка інструментів](tools.md) - Посібник зі створення нових інструментів
- [API Reference](api-reference.md) - Документація на рівні коду
