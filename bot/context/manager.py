"""Context assembly manager."""

from datetime import datetime, timedelta
from typing import Any

from bot.config import get_settings
from bot.context.permanent import load_system_prompt
from bot.db.repositories import MessageRepository, MemoryRepository, SummaryRepository, UserRepository
from bot.db.session import get_session


class ContextManager:
    """Manages context assembly for LLM requests."""

    def __init__(
        self,
        chat_id: int,
        user_id: int,
        bot: Any = None,
        reply_to_message: Any = None,
        chat_title: str | None = None,
        chat_type: str = "private",
        member_count: int | None = None,
        bot_name: str = "Гряг",
        bot_username: str = "gryag_bot",
    ):
        self.chat_id = chat_id
        self.user_id = user_id
        self.bot = bot
        self.reply_to_message = reply_to_message
        self.chat_title = chat_title
        self.chat_type = chat_type
        self.member_count = member_count
        self.bot_name = bot_name
        self.bot_username = bot_username
        self.settings = get_settings()

    async def build_context(self) -> list[dict]:
        """
        Build complete context for LLM.
        """
        messages = []
        
        # 1. System prompt
        system_prompt = await self._get_system_prompt()
        
        # 2-3. Summaries (Keep in system prompt for background context)
        summaries = await self._get_summaries()
        if summaries:
            system_prompt += f"\n\n{summaries}"
        
        messages.append({"role": "system", "content": system_prompt})
        
        # 4. Immediate context as STRUCTURED MESSAGES
        chat_history = await self._get_immediate_context_messages()
        if chat_history:
            messages.extend(chat_history)
        
        # 5. Visual Context (if replying to an image)
        if self.reply_to_message and self.reply_to_message.photo and self.bot:
            try:
                # Get largest photo
                photo = self.reply_to_message.photo[-1]
                file = await self.bot.get_file(photo.file_id)
                # Construct accessible URL (Telegram Bot API)
                token = self.bot.token
                image_url = f"https://api.telegram.org/file/bot{token}/{file.file_path}"
                
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "I am replying to this image:"},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                })
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to process reply image: {e}")
        
        return messages

    async def _get_system_prompt(self) -> str:
        """Load and process system prompt with variables."""
        # Get user info for variables
        async with get_session() as session:
            user_repo = UserRepository(session)
            memory_repo = MemoryRepository(session, self.settings.user_memory_max_facts)
            
            user = await user_repo.get_by_id(self.user_id)
            memories = await memory_repo.get_memories(self.user_id)
        
        # Format memories
        user_memories = ""
        if memories:
            # Keep prompt compact and high-signal: include most recent facts only
            recent = memories[-15:]
            facts = [f"- {m.fact}" for m in recent]
            user_memories = "\n".join(facts)

        # Tool list (kept in sync with actual registry)
        try:
            from bot.tools.registry import get_registry
            registry = get_registry()
            tools_lines = [f"- `{t.name}`: {t.description}" for t in registry.list_tools()]
            tools_text = "\n".join(tools_lines)
        except Exception:
            tools_text = "Tools unavailable."
        
        # Build variables
        now = datetime.now()
        variables = {
            "chatname": self.chat_title or "Private Chat",
            "chatid": str(self.chat_id),
            "chattype": self.chat_type,
            "username": user.username if user else None,
            "userfullname": user.full_name if user else "Unknown",
            "userid": str(self.user_id),
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M"),
            "botname": self.bot_name,
            "botusername": self.bot_username,
            "membercount": str(self.member_count or 0),
            "tools": tools_text,
            "recent_summary": "",  # Filled separately
            "long_summary": "",  # Filled separately
            "user_memories": user_memories,
            "user_pronouns": user.pronouns if user else "",
        }
        
        return load_system_prompt(self.settings.system_prompt_file, variables)

    async def _get_summaries(self) -> str:
        """Get 7-day and 30-day summaries."""
        async with get_session() as session:
            summary_repo = SummaryRepository(session)
            
            parts = []
            
            # 30-day summary
            long_summary = await summary_repo.get_latest(self.chat_id, "30day")
            if long_summary:
                parts.append(f"## Контекст за місяць\n{long_summary.content}")
            
            # 7-day summary
            recent_summary = await summary_repo.get_latest(self.chat_id, "7day")
            if recent_summary:
                parts.append(f"## Контекст за тиждень\n{recent_summary.content}")
            
            return "\n\n".join(parts)

    async def _get_immediate_context_messages(self) -> list[dict]:
        """Get last N messages as structured messages."""
        async with get_session() as session:
            msg_repo = MessageRepository(session)
            user_repo = UserRepository(session)
            
            messages = await msg_repo.get_recent(
                self.chat_id,
                self.settings.immediate_context_messages,
            )
            
            if not messages:
                return []
            
            # Build a dict for quick lookup of messages by telegram_message_id
            msg_by_tg_id = {msg.telegram_message_id: msg for msg in messages}
            
            structured_messages = []
            # Track recent bot responses to prevent repetition loops
            recent_bot_responses = []
            seen_contents = set()  # Deduplication: skip exact duplicate messages
            
            for msg in messages:
                # Get user info
                user = await user_repo.get_by_id(msg.user_id) if msg.user_id else None
                
                if msg.is_bot_message:
                    # Skip if we've seen this exact bot response recently (prevent loops)
                    content_hash = hash(msg.content[:200])  # Hash first 200 chars
                    if content_hash in seen_contents:
                        continue
                    seen_contents.add(content_hash)
                    
                    # Limit recent bot responses in context (last 3 max)
                    if len(recent_bot_responses) >= 3:
                        continue
                    recent_bot_responses.append(msg.content)
                    
                    # Assistant message
                    structured_messages.append({
                        "role": "assistant",
                        "content": msg.content
                    })
                else:
                    # User message
                    user_name = user.full_name if user else "Unknown"
                    username = f"@{user.username}" if user and user.username else ""
                    user_id = msg.user_id or 0

                    # In group chats, strip trigger-only pings ("гряг", "@bot") from the content
                    # so the model answers the last meaningful message instead of looping/repeating.
                    content_for_llm = msg.content
                    if self.chat_type in {"group", "supergroup"}:
                        content_for_llm = self._strip_group_triggers(content_for_llm)
                        if not content_for_llm:
                            # Skip messages that are only a trigger word/mention
                            continue
                    
                    # Construct message prefix for group context
                    # Format: [Name (@username)]: message
                    if username:
                        prefix = f"[{user_name} ({username})]"
                    else:
                        prefix = f"[{user_name}]"
                    
                    # Handle replies
                    reply_info = ""
                    if msg.reply_to_message_id:
                        replied_msg = msg_by_tg_id.get(msg.reply_to_message_id)
                        if replied_msg:
                            reply_preview = replied_msg.content[:50]
                            if len(replied_msg.content) > 50:
                                reply_preview += "..."
                            reply_info = f" (replying to \"{reply_preview}\")"
                    
                    full_content = f"{prefix}{reply_info}: {content_for_llm}"
                    
                    structured_messages.append({
                        "role": "user",
                        "content": full_content,
                        # "name": str(user_id) # Optional: OpenAI supports this, helpful for separation
                    })
            
            return structured_messages

    def _strip_group_triggers(self, text: str) -> str:
        """Remove bot trigger keywords / mentions from group messages for LLM context."""
        import re

        result = text or ""

        # Remove @bot mention (case-insensitive)
        if self.bot_username:
            result = re.sub(
                rf"@{re.escape(self.bot_username)}\b",
                "",
                result,
                flags=re.IGNORECASE,
            )

        # Remove trigger keywords (case-insensitive)
        for keyword in self.settings.bot_trigger_keywords:
            kw = (keyword or "").strip()
            if not kw:
                continue
            result = re.sub(re.escape(kw), "", result, flags=re.IGNORECASE)

        # Clean up leftover punctuation/whitespace
        result = result.strip().strip(",.:-–—")
        return result.strip()
