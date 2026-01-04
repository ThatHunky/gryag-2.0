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

router = Router(name="private")

# Only handle private chats
router.message.filter(F.chat.type == "private")

# Track which user-chat combinations are currently processing responses (prevent concurrent requests per user)
_processing_users: set[tuple[int, int]] = set()  # (chat_id, user_id) tuples
_processing_lock = asyncio.Lock()

MEMORY_TOOL_NAMES = {
    "save_user_fact", "get_user_facts",
    "delete_user_fact", "delete_all_user_facts",
    "remember_memory", "recall_memories",  # Legacy aliases
}


@router.message(~F.text.startswith("/"))
async def handle_private_message(message: Message, bot: Bot) -> None:
    """Handle non-command messages in private chats."""
    # Skip empty messages (e.g. pinned message notifications or media without text/photo)
    if not message.text and not message.photo and not message.caption:
        return
    
    user_info = extract_user_info(message)
    chat_info = extract_chat_info(message)
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    logger.info(f"Private message from {user_info['full_name']} ({user_info['id']})")
    
    # Store message in database
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
            await chat_repo.get_or_create(
                chat_id=chat_info["id"],
                title=chat_info["title"],
                chat_type=chat_info["type"],
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
        logger.error(f"Failed to store private message: {e}")

    # Check if this user is already processing a response in this chat (prevent concurrent requests per user)
    user_chat_key = (chat_info["id"], user_info["id"])
    async with _processing_lock:
        if user_chat_key in _processing_users:
            logger.debug(f"User {user_info['id']} in chat {chat_info['id']} is already processing, skipping duplicate request")
            return
        _processing_users.add(user_chat_key)

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
            reply_to_message=message.reply_to_message,
            chat_title=chat_info["title"],
            chat_type=chat_info["type"],
            member_count=None,
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
        
        # Check if we have visual context
        has_images = any(isinstance(msg.get("content"), list) for msg in context_messages)
        
        # Initial response
        final_response = None
        if has_images and settings.llm_vision_enabled:
            response_text = await llm_client.complete_with_vision(
                messages=context_messages,
                max_tokens=settings.llm_max_response_tokens,
            )
            if response_text is None:
                has_images = False
            else:
                final_response = response_text
        
        if not has_images:
             # Text + Tools loop (Multi-turn ReAct)
            max_turns = 10
            current_turn = 0
            
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
                    
                    logger.info(f"Executing tool {tool_name} with args: {tool_args}")
                    result = await registry.execute(tool_name, **tool_args)
                    logger.info(
                        f"Tool result {tool_name}: success={result.success} error={result.error}"
                    )
                    
                    context_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                        "content": result.output if result.success else f"Error: {result.error}"
                    })
                
                current_turn += 1

            if not final_response:
                final_response = "🤔 Я трохи заплутався..."

        # Send response
        if final_response:
            if hasattr(llm_client, "_filter_thinking"):
                 final_response = llm_client._filter_thinking(final_response)
                 
            sent = await message.reply(final_response)
            
            # Store bot response
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
        logger.error(f"LLM error in private chat: {e}")
        error_msg = ERROR_MESSAGES.get(e.error_type, ERROR_MESSAGES["unknown"])
        await message.reply(f"⚠️ {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error in private chat: {e}")
        await message.reply(f"❌ {ERROR_MESSAGES['unknown']}")
    finally:
        # Always clear processing flag, even on error
        async with _processing_lock:
            _processing_users.discard(user_chat_key)