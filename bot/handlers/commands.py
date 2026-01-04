"""Bot commands handler (/start, /help, etc.)."""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.handlers.base import extract_user_info, is_admin

router = Router(name="commands")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle /start command."""
    user_info = extract_user_info(message)
    
    if message.chat.type == "private":
        await message.answer(
            f"Привіт, {user_info['full_name']}! 👋\n\n"
            "Я Гряг — AI-бот для розмов. "
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
        "🤖 **Гряг — AI-бот**\n\n"
        "**У приватних чатах:**\n"
        "Просто пиши — я відповім на все.\n\n"
        "**У групах:**\n"
        "• Згадай моє ім'я (Гряг)\n"
        "• Тегни мене (@username)\n"
        "• Відповідай на мої повідомлення\n\n"
        "**Команди:**\n"
        "/memories — Що я пам'ятаю про тебе\n"
        "/start — Почати\n"
        "/help — Ця допомога\n"
        "/stats — Моя статистика"
    )
    
    if is_admin(message.from_user.id if message.from_user else 0):
        help_text += "\n\n**Адмін-команди:** /status, /config"
    
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("memories"))
async def cmd_memories(message: Message) -> None:
    """Show stored memories about the user."""
    if not message.from_user:
        return
    await show_memories_page(message, message.from_user.id, page=1)


@router.callback_query(F.data.startswith("memories:"))
async def on_memories_page(callback: CallbackQuery) -> None:
    """Handle memories pagination."""
    page = int(callback.data.split(":")[1])
    await show_memories_page(callback.message, callback.from_user.id, page=page, is_edit=True)
    await callback.answer()


async def show_memories_page(
    message: Message,
    user_id: int,
    page: int = 1,
    is_edit: bool = False,
    page_size: int = 5
) -> None:
    """Render memories page."""
    from bot.db.session import get_session
    from bot.db.repositories.memories import MemoryRepository
    import math

    async with get_session() as session:
        repo = MemoryRepository(session)
        memories = await repo.get_memories(user_id)
    
    if not memories:
        text = "🧠 Я поки що не пам'ятаю нічого особливого про тебе."
        if is_edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return

    total_pages = math.ceil(len(memories) / page_size)
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    current_memories = memories[start_idx:end_idx]

    text_lines = [f"🧠 **Що я пам'ятаю про тебе (стор. {page}/{total_pages}):**\n"]
    for i, mem in enumerate(current_memories, start=start_idx + 1):
        text_lines.append(f"{i}. {mem.fact}")
    
    response_text = "\n".join(text_lines)
    
    # Build keyboard
    keyboard = None
    if total_pages > 1:
        buttons = []
        if page > 1:
            buttons.append(
                InlineKeyboardButton(text="⬅️", callback_data=f"memories:{page - 1}")
            )
        
        # Add page count indicator (non-clickable) in middle if needed, 
        # or just navigation. Let's do simple Nav.
        
        if page < total_pages:
            buttons.append(
                InlineKeyboardButton(text="➡️", callback_data=f"memories:{page + 1}")
            )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

    if is_edit:
        # Check if text is same to avoid error
        if message.text == response_text.replace("**", ""):  # Markdown varies
            pass # Simplified check
        await message.edit_text(response_text, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await message.answer(response_text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    """Handle /stats command."""
    from bot.db.session import get_session
    from bot.db.models import User, Message as DBMessage, Chat
    from sqlalchemy import select, func

    async with get_session() as session:
        # Simple counters
        user_count = await session.scalar(select(func.count(User.id)))
        chat_count = await session.scalar(select(func.count(Chat.id)))
        msg_count = await session.scalar(select(func.count(DBMessage.id)))
    
    await message.answer(
        "📊 **Статистика**\n\n"
        f"👥 **Користувачі:** {user_count}\n"
        f"💬 **Чати:** {chat_count}\n"
        f"📨 **Повідомлення:** {msg_count}",
        parse_mode="Markdown"
    )
