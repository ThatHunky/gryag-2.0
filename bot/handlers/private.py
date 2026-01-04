"""Private chat message handler."""

import logging

from aiogram import Bot, F, Router
from aiogram.types import Message

from bot.db.session import get_session
from bot.db.repositories import ChatRepository, MessageRepository, UserRepository
from bot.handlers.base import extract_chat_info, extract_user_info, send_typing_action

logger = logging.getLogger(__name__)

router = Router(name="private")

# Only handle private chats
router.message.filter(F.chat.type == "private")


@router.message(~F.text.startswith("/"))
async def handle_private_message(message: Message, bot: Bot) -> None:
    """Handle non-command messages in private chats."""
    if not message.text and not message.photo:
        return
    
    user_info = extract_user_info(message)
    chat_info = extract_chat_info(message)
    
    logger.info(f"Private message from {user_info['full_name']} ({user_info['id']})")
    
    # Send typing indicator
    await send_typing_action(bot, message.chat.id)
    
    # Store message in database
    async with get_session() as session:
        user_repo = UserRepository(session)
        chat_repo = ChatRepository(session)
        msg_repo = MessageRepository(session)
        
        # Get or create user and chat
        await user_repo.get_or_create(
            user_id=user_info["id"],
            username=user_info["username"],
            full_name=user_info["full_name"],
        )
        await chat_repo.get_or_create(
            chat_id=chat_info["id"],
            title=chat_info["title"],
            chat_type=chat_info["type"],
        )
        
        # Store the message
        content = message.text or "[Photo]"
        await msg_repo.add(
            telegram_message_id=message.message_id,
            chat_id=chat_info["id"],
            user_id=user_info["id"],
            content=content,
            content_type="text" if message.text else "photo",
            reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
        )
    
    # TODO: Integrate with LLM client for actual response
    # For now, placeholder response
    await message.answer(
        "Повідомлення отримано! 🤖\n"
        "(LLM інтеграція в процесі розробки)"
    )
