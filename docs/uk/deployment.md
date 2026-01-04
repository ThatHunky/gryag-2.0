# Розгортання

Бот Гряг повністю контейнеризований за допомогою Docker, що робить процес розгортання простим та надійним. Цей посібник охоплює розгортання від розробки до продакшн.

## Вимоги

### Мінімальні вимоги

- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM (4GB рекомендується)
- 10GB дискового простору
- Токен Telegram бота від [@BotFather](https://t.me/BotFather)
- API ключ LLM (OpenAI або сумісний провайдер)

### Вимоги для продакшн

- Docker 24.0+
- Docker Compose 2.20+
- 4GB+ RAM
- 20GB+ дискового простору (для бази даних та логів)
- PostgreSQL 15+ (якщо використовується зовнішня база даних)
- Redis 7+ (якщо використовується зовнішній Redis)
- SSL/TLS для безпечних з'єднань (рекомендується)

## Швидке розгортання

### Налаштування для розробки

1. **Клонуйте репозиторій:**

    ```bash
    git clone https://github.com/yourserver/gryag-2.0.git
    cd gryag-2.0
    ```

2. **Створіть файл середовища:**

    ```bash
    cp .env.example .env
    # Відредагуйте .env з вашими обліковими даними
    ```

3. **Запустіть сервіси:**

    ```bash
    docker compose up -d
    ```

4. **Перевірте логи:**

    ```bash
    docker compose logs -f bot
    ```

5. **Перевірте, що бот працює:**

    ```bash
    docker compose ps
    ```

## Структура сервісів

Налаштування Docker Compose включає три основні сервіси:

### Сервіс Bot

- **Образ**: Збирається з `Dockerfile`
- **Порти**: Немає (спілкується через Telegram API)
- **Томи**:
  - `./data:/app/data` - Логи та персистентні дані
  - `./prompts:/app/prompts:ro` - Системні промпти (тільки читання)
- **Залежності**: `postgres`, `redis`
- **Перевірка здоров'я**: Перевірка процесу Python

### Сервіс PostgreSQL

- **Образ**: `postgres:18-alpine`
- **Порти**: `5432` (тільки внутрішній)
- **Томи**: `./data/postgres:/var/lib/postgresql/data`
- **Оточення**: Попередньо налаштований користувач/пароль
- **Перевірка здоров'я**: Перевірка `pg_isready`

### Сервіс Redis

- **Образ**: `redis:alpine`
- **Порти**: `6379` (тільки внутрішній)
- **Томи**: Іменований том `redis_data`
- **Персистентність**: AOF (Append Only File) увімкнено
- **Перевірка здоров'я**: `redis-cli ping`

## Розгортання в продакшн

### Чек-лист перед розгортанням

- [ ] Захистити файл `.env` з надійними обліковими даними
- [ ] Налаштувати правила файрволу
- [ ] Налаштувати SSL/TLS (якщо використовуються зовнішні сервіси)
- [ ] Налаштувати стратегію резервного копіювання
- [ ] Налаштувати моніторинг та сповіщення
- [ ] Переглянути налаштування безпеки
- [ ] Протестувати в staging середовищі

### Конфігурація для продакшн

1. **Захищені змінні оточення:**

    ```bash
    # Використовуйте надійні паролі
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    
    # Зберігайте секрети безпечно (використовуйте керування секретами)
    # Ніколи не комітьте .env у систему контролю версій
    ```

2. **Оновіть docker-compose.yml для продакшн:**

    ```yaml
    services:
      bot:
        restart: always
        deploy:
          resources:
            limits:
              cpus: '2'
              memory: 2G
            reservations:
              cpus: '1'
              memory: 1G
    ```

3. **Налаштуйте логування:**

    ```env
    LOG_LEVEL=WARNING
    LOG_FORMAT=json
    LOG_FILE_ENABLED=True
    LOG_FILE_RETENTION_DAYS=30
    ```

4. **Встановіть контроль доступу:**

    ```env
    ACCESS_MODE=whitelist
    WHITELIST_CHATS=-1001234567890
    RATE_LIMIT_ENABLED=True
    RATE_LIMIT_PROMPTS=20
    ```

## Мережа Docker

Сервіси спілкуються через внутрішню мережу Docker:

- **Мережа**: Мережа за замовчуванням bridge (або користувацька мережа)
- **Виявлення сервісів**: Сервіси доступні за ім'ям (`postgres`, `redis`)
- **Експозиція портів**: Експортуйте порти тільки якщо потрібно зовні

## Міграції бази даних

Проект використовує Alembic для міграцій бази даних.

### Автоматичні міграції

Міграції виконуються автоматично при запуску бота, якщо база даних порожня або відсутні таблиці.

### Керування міграціями вручну

1. **Створити нову міграцію:**

    ```bash
    docker compose exec bot alembic revision --autogenerate -m "опис"
    ```

2. **Застосувати міграції:**

    ```bash
    docker compose exec bot alembic upgrade head
    ```

3. **Відкотити міграцію:**

    ```bash
    docker compose exec bot alembic downgrade -1
    ```

4. **Перевірити поточну версію:**

    ```bash
    docker compose exec bot alembic current
    ```

## Резервне копіювання та відновлення

### Резервне копіювання бази даних

1. **Повне резервне копіювання бази даних:**

    ```bash
    docker compose exec postgres pg_dump -U bot gryag > backup_$(date +%Y%m%d).sql
    ```

2. **Автоматизований скрипт резервного копіювання:**

    ```bash
    #!/bin/bash
    BACKUP_DIR="./backups"
    mkdir -p $BACKUP_DIR
    docker compose exec -T postgres pg_dump -U bot gryag | gzip > $BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql.gz
    ```

### Відновлення бази даних

1. **Відновити з резервної копії:**

    ```bash
    gunzip < backup_20240101.sql.gz | docker compose exec -T postgres psql -U bot gryag
    ```

## Моніторинг та перевірки здоров'я

### Перевірки здоров'я

Всі сервіси включають перевірки здоров'я:

- **Bot**: Перевірка процесу Python
- **Postgres**: Перевірка `pg_isready`
- **Redis**: Перевірка `redis-cli ping`

### Моніторинг логів

1. **Переглянути всі логи:**

    ```bash
    docker compose logs -f
    ```

2. **Переглянути конкретний сервіс:**

    ```bash
    docker compose logs -f bot
    docker compose logs -f postgres
    docker compose logs -f redis
    ```

## Оновлення бота

### Процес оновлення

1. **Отримати останні зміни:**

    ```bash
    git pull origin main
    ```

2. **Резервне копіювання бази даних:**

    ```bash
    # Дотримуйтеся процедури резервного копіювання вище
    ```

3. **Перебудувати та перезапустити:**

    ```bash
    docker compose build bot
    docker compose up -d
    ```

4. **Перевірити:**

    ```bash
    docker compose logs -f bot
    docker compose ps
    ```

## Пов'язана документація

- [Конфігурація](configuration.md) - Всі опції конфігурації
- [Архітектура](architecture.md) - Архітектура системи
- [Усунення проблем](troubleshooting.md) - Загальні проблеми та рішення
