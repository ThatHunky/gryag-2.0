# Посібник з розробки

Цей посібник охоплює налаштування середовища розробки, розуміння структури проекту, стандарти коду, тестування та внесення змін до Гряг 2.0.

## Налаштування середовища розробки

### Передумови

- Python 3.13+
- Docker та Docker Compose (для сервісів)
- Git
- Редактор коду (VS Code, PyCharm, тощо)

### Початкове налаштування

1. **Клонуйте репозиторій:**

    ```bash
    git clone https://github.com/yourserver/gryag-2.0.git
    cd gryag-2.0
    ```

2. **Створіть віртуальне середовище:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # На Windows: venv\Scripts\activate
    ```

3. **Встановіть залежності:**

    ```bash
    pip install -e ".[dev]"
    ```

4. **Запустіть сервіси (Docker):**

    ```bash
    docker compose up -d postgres redis
    ```

5. **Створіть файл `.env`:**

    ```bash
    cp .env.example .env
    # Відредагуйте .env з вашими обліковими даними
    ```

6. **Запустіть міграції бази даних:**

    ```bash
    alembic upgrade head
    ```

7. **Запустіть бота:**

    ```bash
    python -m bot.main
    ```

## Структура проекту

```
gryag-2.0/
├── bot/                    # Основний код додатку
│   ├── handlers/          # Обробники повідомлень
│   ├── context/           # Керування контекстом
│   ├── db/                # Шар бази даних
│   ├── llm/               # LLM клієнт
│   ├── tools/             # Система інструментів
│   └── middlewares/       # Middleware
├── tests/                 # Тести
├── migrations/            # Міграції бази даних
├── prompts/               # Системні промпти
└── docs/                  # Документація
```

## Стандарти коду та конвенції

### Стиль Python

Проект використовує:

- **Python 3.13+** функції
- **Підказки типів** для всіх функцій та методів
- **Async/await** для всіх операцій I/O
- **Ruff** для лінтування та форматування

### Форматування коду

```bash
# Автоформатування
ruff format .

# Перевірка форматування
ruff check .
```

### Підказки типів

Завжди використовуйте підказки типів:

```python
from typing import Optional

async def get_user(user_id: int) -> Optional[User]:
    """Отримати користувача за ID."""
    pass
```

### Документація

Використовуйте docstrings у стилі Google:

```python
def calculate_total(items: list[float]) -> float:
    """Обчислити суму елементів.
    
    Args:
        items: Список цін елементів
        
    Returns:
        Загальна ціна
        
    Raises:
        ValueError: Якщо список елементів порожній
    """
    if not items:
        raise ValueError("Список елементів не може бути порожнім")
    return sum(items)
```

## Тестування

### Запуск тестів

```bash
# Запустити всі тести
pytest

# Запустити з покриттям
pytest --cov=bot --cov-report=html

# Запустити конкретний файл тестів
pytest tests/test_tools/test_calculator.py
```

### Написання тестів

Тести використовують pytest з підтримкою async:

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

## Додавання нових функцій

### 1. Додавання нового інструменту

1. Створіть файл інструменту в `bot/tools/`
2. Реалізуйте інтерфейс `BaseTool`
3. Зареєструйте в `bot/tools/registry.py`
4. Напишіть тести
5. Оновіть документацію

Дивіться [Посібник з інструментів](tools.md) для деталей.

### 2. Додавання нового обробника

1. Створіть обробник в `bot/handlers/`
2. Зареєструйте router в `bot/main.py`
3. Напишіть тести
4. Оновіть документацію

### 3. Додавання нової моделі бази даних

1. Додайте модель до `bot/db/models.py`
2. Створіть міграцію: `alembic revision --autogenerate -m "Опис"`
3. Перегляньте міграцію
4. Створіть репозиторій в `bot/db/repositories/`
5. Оновіть документацію

## Налагодження

### Режим налагодження

Встановіть в `.env`:

```env
LOG_LEVEL=DEBUG
```

### Логування

Використовуйте структуроване логування:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Повідомлення налагодження")
logger.info("Інформаційне повідомлення")
logger.error("Повідомлення про помилку", exc_info=True)
```

## Пов'язана документація

- [API Reference](api-reference.md) - Документація API на рівні коду
- [Архітектура](architecture.md) - Архітектура системи
- [Посібник з інструментів](tools.md) - Посібник з розробки інструментів
- [Схема бази даних](database.md) - Документація бази даних
