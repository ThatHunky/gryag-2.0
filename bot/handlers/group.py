"""Group chat message handler with trigger detection."""

import logging

from aiogram import Bot, F, Router
from aiogram.types import Message

from bot.config import get_settings
from bot.context.manager import ContextManager
from bot.db.session import get_session
from bot.db.repositories import ChatRepository, MessageRepository, UserRepository
from bot.handlers.base import extract_chat_info, extract_user_info, send_typing_action
from bot.llm import LLMClient
from bot.utils.errors import LLMError, ERROR_MESSAGES

logger = logging.getLogger(__name__)

router = Router(name="group")

# Only handle group and supergroup chats
router.message.filter(F.chat.type.in_(["group", "supergroup"]))


def should_respond(message: Message, bot_username: str | None) -> bool:
    """Check if bot should respond to this message."""
    settings = get_settings()
    text = (message.text or message.caption or "").lower()
    
    # Check keywords
    for keyword in settings.bot_trigger_keywords:
        if keyword.lower() in text:
            logger.debug(f"Keyword match: '{keyword}' in '{text}'")
            return True
    
    # Check bot mention
    if bot_username and f"@{bot_username.lower()}" in text:
        logger.debug(f"Bot mention detected: @{bot_username}")
        return True
    
    # Check if reply to bot
    if message.reply_to_message and message.reply_to_message.from_user:
        if bot_username and message.reply_to_message.from_user.username == bot_username:
            logger.debug("Reply to bot detected")
            return True
    
    return False


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message, bot: Bot):
    """Handle messages in groups."""
    # Check if this is a command (handled by commands.py)
    if message.text and message.text.startswith("/"):
        return

    # Skip empty messages (e.g. pinned message notifications)
    if not message.text and not message.photo and not message.caption:
        return

    user_info = extract_user_info(message)
    chat_info = extract_chat_info(message)
    bot_info = await bot.get_me()
    bot_username = bot_info.username

    try:
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
            
            # Get member count
            try:
                member_count = await bot.get_chat_member_count(message.chat.id)
            except Exception:
                member_count = None
            
            await chat_repo.get_or_create(
                chat_id=chat_info["id"],
                title=chat_info["title"],
                chat_type=chat_info["type"],
                member_count=member_count,
            )
            
            # Store the message
            content = message.text or message.caption or "[Photo]"
            await msg_repo.add(
                telegram_message_id=message.message_id,
                chat_id=chat_info["id"],
                user_id=user_info["id"],
                content=content,
                content_type="text" if message.text else "photo",
                reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None,
            )
    except Exception as e:
        logger.error(f"Failed to store message: {e}")
    
    # Check if we should respond
    if not should_respond(message, bot_username):
        return
    
    logger.info(f"Triggered in {chat_info['title']} by {user_info['full_name']}")
    
    # Send typing indicator
    settings = get_settings()
    if settings.typing_indicator_enabled:
        await send_typing_action(bot, message.chat.id)
    
    try:
        # Build context
        context_manager = ContextManager(
            chat_id=chat_info["id"],
            user_id=user_info["id"],
            bot=bot,
            reply_to_message=message.reply_to_message,  # Pass reply object for vision context
            chat_title=chat_info["title"],
            chat_type=chat_info["type"],
            member_count=member_count if 'member_count' in dir() else None,
            bot_name=bot_info.full_name,
            bot_username=bot_username,
        )
        
        context_messages = await context_manager.build_context()
        
        # Note: Current message is already in context from DB storage above
        
        # Call LLM
        llm_client = LLMClient()
        
        # Check if we have visual context (multimodal messages)
        has_images = any(isinstance(msg.get("content"), list) for msg in context_messages)
        
        if has_images:
            response = await llm_client.complete_with_vision(
                messages=context_messages,
                max_tokens=settings.llm_max_response_tokens,
            )
            # If explicit None returned, vision is disabled or failed
            if response is None:
                logger.info("Vision failed or disabled. Falling back to text-only model with placeholder.")
                # Sanitize context: Replace image objects with text placeholders
                sanitized_messages = []
                for msg in context_messages:
                    content = msg.get("content")
                    if isinstance(content, list):
                        new_content = ""
                        for part in content:
                            if part.get("type") == "text":
                                new_content += part.get("text", "") + " "
                            elif part.get("type") == "image_url":
                                new_content += "[System: User replied to an image, but I cannot see it. I must respond based on text context only.] "
                        sanitized_messages.append({"role": msg["role"], "content": new_content.strip()})
                    else:
                        sanitized_messages.append(msg)
                
                # Call standard text completion with sanitized context
                response = await llm_client.complete(
                    messages=sanitized_messages,
                    max_tokens=settings.llm_max_response_tokens,
                )
        else:
            response = await llm_client.complete(
                messages=context_messages,
                max_tokens=settings.llm_max_response_tokens,
            )
        
        # Retry logic for empty responses (e.g. when only thinking tags were returned and filtered)
        if not response:
            logger.info("Empty response received (likely filtered thinking). Retrying with explicit instruction.")
            # Add explicit instruction to the CONTEXT (as a system/user note)
            context_messages.append({
                "role": "user", 
                "content": "Your previous response was empty (likely because you only outputted thinking tags). Please output the final answer text now."
            })
            response = await llm_client.complete(
                messages=context_messages,
                max_tokens=settings.llm_max_response_tokens,
            )

        
        # Send response
        if response:
            await message.reply(response)
            
            # Store bot response
            try:
                async with get_session() as session:
                    msg_repo = MessageRepository(session)
                    await msg_repo.add(
                        telegram_message_id=0,  # Will be updated
                        chat_id=chat_info["id"],
                        user_id=None,  # Bot messages have no user
                        content=response[:4000],
                        content_type="text",
                        is_bot_message=True,
                    )
            except Exception as e:
                logger.error(f"Failed to store bot response: {e}")
        else:
            await message.reply("🤔 Не можу відповісти зараз.")
            
    except LLMError as e:
        logger.error(f"LLM error: {e}")
        error_msg = ERROR_MESSAGES.get(e.error_type, ERROR_MESSAGES["unknown"])
        await message.reply(f"⚠️ {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await message.reply(f"❌ {ERROR_MESSAGES['unknown']}")


