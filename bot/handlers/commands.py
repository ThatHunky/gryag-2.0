"""Bot commands handler (/start, /help, etc.)."""

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from bot.handlers.base import extract_user_info, is_admin

router = Router(name="commands")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user_info = extract_user_info(message)
    
    if message.chat.type == "private":
        await message.answer(
            f"Привіт, {user_info['full_name']}! 👋\n\n"
            "Я Грягі — AI-бот для розмов. "
            "Просто напиши мені щось, і я відповім!\n\n"
            "Для отримання допомоги: /help"
        )
    else:
        await message.answer(
            "Привіт! Я тут. Щоб поговорити зі мною, "
            "використовуй моє ім'я або відповідай на мої повідомлення."
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Handle /help command."""
    help_text = (
        "🤖 **Грягі — AI-бот**\n\n"
        "**У приватних чатах:**\n"
        "Просто пиши — я відповім на все.\n\n"
        "**У групах:**\n"
        "• Згадай моє ім'я (грягі)\n"
        "• Тегни мене (@username)\n"
        "• Відповідай на мої повідомлення\n\n"
        "**Команди:**\n"
        "/start — Почати\n"
        "/help — Ця допомога\n"
        "/stats — Моя статистика"
    )
    
    if is_admin(message.from_user.id if message.from_user else 0):
        help_text += "\n\n**Адмін-команди:** /status, /config"
    
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Handle /stats command."""
    # TODO: Implement actual stats from database
    await message.answer(
        "📊 **Статистика**\n\n"
        "Ця функція скоро буде доступна!",
        parse_mode="Markdown"
    )
