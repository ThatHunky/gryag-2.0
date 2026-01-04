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
        bot_name: str = "Грягі",
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
        
        # 2-3. Summaries
        summaries = await self._get_summaries()
        if summaries:
            system_prompt += f"\n\n{summaries}"
        
        # 4. Immediate context as formatted text
        chat_history = await self._get_immediate_context_text()
        if chat_history:
            system_prompt += f"\n\n## Recent Chat History\n\n{chat_history}\n\n---\n\nRespond naturally to the last message above."
        
        messages.append({"role": "system", "content": system_prompt})
        
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
            facts = [f"- {m.fact}" for m in memories]
            user_memories = "\n".join(facts)
        
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
            "tools": "weather, calculator, search_web, generate_image, remember_memory, recall_memories",
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

    async def _get_immediate_context_text(self) -> str:
        """Get last N messages as formatted text for system prompt."""
        async with get_session() as session:
            msg_repo = MessageRepository(session)
            user_repo = UserRepository(session)
            
            messages = await msg_repo.get_recent(
                self.chat_id,
                self.settings.immediate_context_messages,
            )
            
            if not messages:
                return ""
            
            # Note: get_recent already returns messages in chronological order (Oldest -> Newest)
            # So the last message in the list is the most recent one.
            
            # Build a dict for quick lookup of messages by telegram_message_id
            msg_by_tg_id = {msg.telegram_message_id: msg for msg in messages}
            
            lines = []
            for msg in messages:
                # Get user info
                user = await user_repo.get_by_id(msg.user_id) if msg.user_id else None
                
                if msg.is_bot_message:
                    # Bot message
                    lines.append(f"[{self.bot_name}]: {msg.content}")
                else:
                    # Format user messages with full info for disambiguation
                    user_name = user.full_name if user else "Unknown"
                    username = f"@{user.username}" if user and user.username else ""
                    user_id = msg.user_id or 0
                    
                    # Format: [Name (@username, id:123)]: message
                    if username:
                        prefix = f"[{user_name} ({username}, id:{user_id})]"
                    else:
                        prefix = f"[{user_name} (id:{user_id})]"
                    
                    # Check if this is a reply to another message
                    reply_info = ""
                    if msg.reply_to_message_id:
                        replied_msg = msg_by_tg_id.get(msg.reply_to_message_id)
                        if replied_msg:
                            reply_preview = replied_msg.content[:80]
                            if len(replied_msg.content) > 80:
                                reply_preview += "..."
                            reply_info = f" (replying to: \"{reply_preview}\")"
                    
                    lines.append(f"{prefix}{reply_info}: {msg.content}")
            
            return "\n".join(lines)
