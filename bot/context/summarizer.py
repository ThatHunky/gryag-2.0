"""Context summarization for 7-day and 30-day summaries."""

from datetime import datetime, timedelta

from bot.config import get_settings
from bot.db.session import get_session
from bot.db.repositories import MessageRepository, SummaryRepository


async def generate_summary(
    chat_id: int,
    summary_type: str,  # "7day" or "30day"
    llm_client,  # LLM client instance
) -> str | None:
    """
    Generate a context summary for a chat.
    
    Uses LLM to summarize messages from the specified period.
    """
    settings = get_settings()
    
    if summary_type == "7day":
        days = 7
        max_tokens = settings.recent_summary_tokens
    else:  # 30day
        days = 30
        max_tokens = settings.long_summary_tokens
    
    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()
    
    async with get_session() as session:
        msg_repo = MessageRepository(session)
        summary_repo = SummaryRepository(session)
        
        # Get messages from period
        messages = await msg_repo.get_since(chat_id, period_start)
        
        if not messages:
            return None
        
        # Format messages for summarization
        content = "\n".join([
            f"[{msg.created_at.strftime('%Y-%m-%d')}] {msg.content[:200]}"
            for msg in messages[:500]  # Limit for token efficiency
        ])
        
        # Generate summary using LLM
        prompt = f"""Підсумуй наступний контекст чату за останні {days} днів.
Зосередься на ключових темах, учасниках та важливих подіях.
Будь лаконічним, але інформативним.

Контекст:
{content}

Підсумок:"""
        
        summary_content = await llm_client.complete(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            model=settings.llm_summarization_model,
        )
        
        # Store summary
        await summary_repo.add(
            chat_id=chat_id,
            summary_type=summary_type,
            content=summary_content,
            token_count=len(summary_content.split()),  # Rough estimate
            period_start=period_start,
            period_end=period_end,
        )
        
        return summary_content
