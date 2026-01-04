"""Group chat message handler with trigger detection."""

import asyncio
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

# Track which user-chat combinations are currently processing responses (prevent concurrent requests per user)
_processing_users: set[tuple[int, int]] = set()  # (chat_id, user_id) tuples
_processing_lock = asyncio.Lock()

MEMORY_TOOL_NAMES = {
    "save_user_fact", "get_user_facts",
    "delete_user_fact", "delete_all_user_facts",
    "remember_memory", "recall_memories",  # Legacy aliases
}


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


def _is_trigger_only_message(content: str, bot_username: str | None) -> bool:
    """Check if message is ONLY a trigger (no actual content)."""
    if not content:
        return False
    
    text = content.strip().lower()
    if not text:
        return False
    
    settings = get_settings()
    
    # Remove all trigger keywords
    for keyword in settings.bot_trigger_keywords:
        text = text.replace(keyword.lower(), "").strip()
    
    # Remove bot mention
    if bot_username:
        text = text.replace(f"@{bot_username.lower()}", "").strip()
    
    # Remove common punctuation/whitespace
    text = text.strip(".,:;!?- \n\t")
    
    # If nothing left, it was trigger-only
    return len(text) == 0


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

    # Check if we should respond BEFORE storing
    # This prevents storing trigger-only messages that would pollute context
    should_respond_to_this = should_respond(message, bot_username)
    
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
            
            # Only store non-trigger-only messages to avoid context pollution
            # If it's a trigger-only message (just "гряг" or @bot), we'll skip storing it
            content = message.text or message.caption or "[Photo]"
            is_trigger_only = should_respond_to_this and _is_trigger_only_message(content, bot_username)
            
            if not is_trigger_only:
                # Store the message (skip trigger-only pings)
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
    if not should_respond_to_this:
        return

    # Check if this user is already processing a response in this chat (prevent concurrent requests per user)
    user_chat_key = (chat_info["id"], user_info["id"])
    async with _processing_lock:
        if user_chat_key in _processing_users:
            logger.debug(f"User {user_info['id']} in chat {chat_info['id']} is already processing, skipping duplicate request")
            return
        _processing_users.add(user_chat_key)

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
        
        # Tool setup
        from bot.tools.registry import get_registry
        registry = get_registry()
        tool_schemas = registry.get_openai_schemas()
        
        # Call LLM
        llm_client = LLMClient()
        settings = get_settings()
        
        # Check if we have visual context (multimodal messages)
        has_images = any(isinstance(msg.get("content"), list) for msg in context_messages)
        
        # Initial response
        if has_images and settings.llm_vision_enabled:
            # Vision models often don't support tools, or support limited tools. 
            # For simplicity, we skip tools for vision requests for now unless model specific
            response_text = await llm_client.complete_with_vision(
                messages=context_messages,
                max_tokens=settings.llm_max_response_tokens,
            )
            # Fallback handled inside client or check for None
            if response_text is None:
                # Fallback to text + tools
                has_images = False
            else:
                final_response = response_text
        
        if not has_images:
            # Text + Tools loop
            max_turns = 10
            current_turn = 0
            final_response = None
            
            while current_turn < max_turns:
                response = await llm_client.complete_with_tools(
                    messages=context_messages,
                    tools=tool_schemas,
                    max_tokens=settings.llm_max_response_tokens,
                )
                
                content = response["content"]
                tool_calls = response["tool_calls"]
                
                # Extract and handle reasoning_content if present (Mimo Requirement)
                reasoning_content = response.get("reasoning_content")
                
                # CRITICAL: If model claims to remember but didn't call save_user_fact, force a retry
                user_message_lower = (message.text or message.caption or "").lower()
                claims_to_remember = any(phrase in content.lower() for phrase in [
                    "запам'ятав", "запам'ятала", "remembered", "i remember", "збережу", "saved", "готово"
                ])
                mentions_personal_fact = any(phrase in user_message_lower for phrase in [
                    "запам'ятай", "remember", "я живу", "i live", "я люблю", "i like", "я з", "i'm from"
                ])
                
                if claims_to_remember and mentions_personal_fact and not tool_calls:
                    logger.warning(
                        f"Model claimed to remember but didn't call save_user_fact. "
                        f"Content: {content[:100]}... Forcing tool call retry."
                    )
                    # Add a system message to force tool usage
                    context_messages.append({
                        "role": "system",
                        "content": "ERROR: You said you remembered but did NOT call save_user_fact. You MUST call the tool. The fact is NOT saved. Call save_user_fact NOW with the fact the user told you."
                    })
                    # Retry this turn
                    continue
                
                # CRITICAL: If model claims to forget/delete but didn't call delete tool, force a retry
                claims_to_forget = any(phrase in content.lower() for phrase in [
                    "забув", "забула", "forgot", "deleted", "видалено", "видалені", "removed", "видалив"
                ])
                mentions_forget = any(phrase in user_message_lower for phrase in [
                    "забудь", "forget", "видали", "delete", "забудь то", "забудь той"
                ])
                
                # Check if user wants to delete ALL facts
                wants_delete_all = any(phrase in user_message_lower for phrase in [
                    "забудь усе", "забудь все", "forget everything", "delete all", "видали все", 
                    "видали усе", "забудь усе що", "забудь все що", "forget all"
                ])
                
                if claims_to_forget and mentions_forget and not tool_calls:
                    # Check if any tool call was delete-related
                    has_delete_tool = any(
                        tc.get("name") in ["delete_user_fact", "delete_all_user_facts"]
                        for tc in tool_calls
                    ) if tool_calls else False
                    
                    if not has_delete_tool:
                        if wants_delete_all:
                            logger.warning(
                                f"Model claimed to delete all but didn't call delete_all_user_facts. "
                                f"Content: {content[:100]}... Forcing tool call retry."
                            )
                            context_messages.append({
                                "role": "system",
                                "content": "ERROR: User asked to forget EVERYTHING ('забудь усе'), but you did NOT call delete_all_user_facts. You MUST call delete_all_user_facts NOW. Nothing is deleted until you call this tool."
                            })
                        else:
                            logger.warning(
                                f"Model claimed to forget but didn't call delete_user_fact. "
                                f"Content: {content[:100]}... Forcing tool call retry."
                            )
                            context_messages.append({
                                "role": "system",
                                "content": "ERROR: You said you forgot/deleted but did NOT call delete_user_fact. You MUST call get_user_facts first to find the fact, then call delete_user_fact. The fact is NOT deleted. Call the tools NOW."
                            })
                        # Retry this turn
                        continue
                
                 # Construct the assistant message
                assistant_msg = {
                    "role": "assistant",
                    "content": content,
                }
                
                if tool_calls:
                    assistant_msg["tool_calls"] = [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments"]
                            }
                        } for tc in tool_calls
                    ]
                
                # CRITICAL: Preserve reasoning_content in history if present
                if reasoning_content:
                    assistant_msg["reasoning_content"] = reasoning_content
                
                # Add assistant response to history
                context_messages.append(assistant_msg)
                
                if not tool_calls:
                    final_response = content
                    break
                
                # Execute tools
                import json
                
                for tc in tool_calls:
                    tool_name = tc["name"]
                    tool_args_str = tc["arguments"]
                    tool_call_id = tc["id"]
                    
                    try:
                        tool_args = json.loads(tool_args_str)
                    except json.JSONDecodeError:
                        tool_args = {}
                    
                    # Inject user_id for memory tools
                    if tool_name in MEMORY_TOOL_NAMES:
                        tool_args["user_id"] = user_info["id"]
                        logger.info(f"Injecting user_id={user_info['id']} for {tool_name}")
                    
                    # Execute
                    logger.info(f"Executing tool {tool_name} in group chat with args: {tool_args}")
                    result = await registry.execute(tool_name, **tool_args)
                    logger.info(
                        f"Tool result {tool_name}: success={result.success} error={result.error}"
                    )
                    
                    # Append result
                    context_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                        "content": result.output if result.success else f"Error: {result.error}"
                    })
                
                current_turn += 1
            
            if not final_response:
                final_response = "🤔 Я трохи заплутався..."

        # Store and send response
        if final_response:
            # Clean up response (remove thinking tags just in case)
            if hasattr(llm_client, "_filter_thinking"):
                 final_response = llm_client._filter_thinking(final_response)
                 
            sent = await message.reply(final_response)
            
            try:
                async with get_session() as session:
                    msg_repo = MessageRepository(session)
                    await msg_repo.add(
                        telegram_message_id=sent.message_id,
                        chat_id=chat_info["id"],
                        user_id=None,
                        content=final_response[:4000],
                        content_type="text",
                        reply_to_message_id=message.message_id,
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
    finally:
        # Always clear processing flag, even on error
        async with _processing_lock:
            _processing_users.discard(user_chat_key)


