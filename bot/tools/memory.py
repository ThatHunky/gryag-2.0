"""Memory management tools."""

from bot.db.repositories import MemoryRepository
from bot.db.session import get_session
from bot.tools.base import BaseTool, ToolResult


class SaveUserFactTool(BaseTool):
    """Save a fact about the user."""
    
    name = "save_user_fact"
    description = "MANDATORY: Save a fact about the user to long-term storage. You MUST call this when: (1) user says 'запам'ятай' / 'remember' / 'запам'ятай що', (2) user tells you a personal fact (location, preferences, name, etc.), (3) user says 'I live in...' / 'я живу в...' / 'I like...' / 'я люблю...'. DO NOT just say you remembered - YOU MUST CALL THIS TOOL. The fact is NOT saved until you call this function."
    parameters = {
        "type": "object",
        "properties": {
            "fact": {
                "type": "string",
                "description": "The fact to save.",
            },
        },
        "required": ["fact"],
    }
    
    async def execute(self, fact: str, user_id: int | None = None, **kwargs) -> ToolResult:
        """Execute save fact."""
        if not user_id:
            return ToolResult(
                success=False,
                output="",
                error="User ID required for memory operations.",
            )
            
        try:
            async with get_session() as session:
                repo = MemoryRepository(session)
                await repo.add_memory(user_id, fact)
                
            return ToolResult(
                success=True,
                output=f"Fact saved: {fact}",
                data={"fact": fact},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to save fact: {e}",
            )


class GetUserFactsTool(BaseTool):
    """Retrieve facts about the user."""
    
    name = "get_user_facts"
    description = "Retrieve all saved facts about the user."
    parameters = {
        "type": "object",
        "properties": {
             "query": {
                "type": "string",
                "description": "Optional search query.",
            },
        },
    }
    
    async def execute(self, query: str = None, user_id: int | None = None, **kwargs) -> ToolResult:
        """Execute get facts."""
        if not user_id:
            return ToolResult(
                success=False,
                output="",
                error="User ID required for memory operations.",
            )
            
        try:
            async with get_session() as session:
                repo = MemoryRepository(session)
                memories = await repo.get_memories(user_id)
                
            if not memories:
                return ToolResult(
                    success=True,
                    output="No facts found about this user.",
                    data=[],
                )
            
            results = [m.fact for m in memories]
            if query:
                results = [m for m in results if query.lower() in m.lower()]
                
            formatted = "\n".join([f"- {m}" for m in results])
            return ToolResult(
                success=True,
                output=f"Known facts:\n{formatted}",
                data=results,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to get facts: {e}",
            )


class DeleteUserFactTool(BaseTool):
    """Delete a fact about the user."""
    
    name = "delete_user_fact"
    description = "MANDATORY: Delete a specific fact about the user. You MUST call this when: (1) user says 'забудь' / 'forget' / 'забудь то' / 'забудь той факт', (2) user wants to remove incorrect information. ALWAYS call get_user_facts first to find the fact, then call this tool with the fact_text. DO NOT just say you forgot - YOU MUST CALL THIS TOOL. The fact is NOT deleted until you call this function."
    parameters = {
        "type": "object",
        "properties": {
            "fact_text": {
                "type": "string",
                "description": "The exact text of the fact to delete, or a partial match. If multiple facts match, the first one will be deleted.",
            },
        },
        "required": ["fact_text"],
    }
    
    async def execute(self, fact_text: str, user_id: int | None = None, **kwargs) -> ToolResult:
        """Execute delete fact."""
        if not user_id:
            return ToolResult(
                success=False,
                output="",
                error="User ID required for memory operations.",
            )
            
        try:
            async with get_session() as session:
                repo = MemoryRepository(session)
                memories = await repo.get_memories(user_id)
                
                if not memories:
                    return ToolResult(
                        success=False,
                        output="",
                        error="No facts found to delete.",
                    )
                
                # Find matching memory (exact match first, then partial, then keyword match)
                fact_lower = fact_text.lower().strip()
                # Extract keywords from fact_text (remove common words)
                keywords = [w for w in fact_lower.split() if w not in ["про", "то", "той", "той", "факт", "about", "the", "that", "fact"]]
                
                matched = None
                # 1. Exact match
                for mem in memories:
                    if mem.fact.lower().strip() == fact_lower:
                        matched = mem
                        break
                
                # 2. Partial match (substring)
                if not matched:
                    for mem in memories:
                        mem_lower = mem.fact.lower()
                        if fact_lower in mem_lower or mem_lower in fact_lower:
                            matched = mem
                            break
                
                # 3. Keyword match (if user says "гори" and fact contains "mountains" or "гори")
                if not matched and keywords:
                    for mem in memories:
                        mem_lower = mem.fact.lower()
                        # Check if any keyword appears in the stored fact
                        if any(kw in mem_lower for kw in keywords if len(kw) > 2):  # Only match words > 2 chars
                            matched = mem
                            break
                
                if not matched:
                    # Return list of available facts to help user
                    available = [f"- {m.fact}" for m in memories[:5]]
                    return ToolResult(
                        success=False,
                        output="",
                        error=f"Fact not found: '{fact_text}'. Available facts:\n" + "\n".join(available),
                    )
                
                deleted = await repo.delete_memory(matched.id)
                if deleted:
                    return ToolResult(
                        success=True,
                        output=f"Fact deleted: {matched.fact}",
                        data={"deleted_fact": matched.fact},
                    )
                else:
                    return ToolResult(
                        success=False,
                        output="",
                        error="Failed to delete fact.",
                    )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to delete fact: {e}",
            )


class DeleteAllUserFactsTool(BaseTool):
    """Delete all facts about the user."""
    
    name = "delete_all_user_facts"
    description = "MANDATORY: Delete ALL facts about the user. You MUST call this when: (1) user says 'забудь усе' / 'забудь все' / 'forget everything' / 'delete all', (2) user explicitly asks to forget everything they told you. DO NOT just say you deleted everything - YOU MUST CALL THIS TOOL. Nothing is deleted until you call this function."
    parameters = {
        "type": "object",
        "properties": {},
    }
    
    async def execute(self, user_id: int | None = None, **kwargs) -> ToolResult:
        """Execute delete all facts."""
        if not user_id:
            return ToolResult(
                success=False,
                output="",
                error="User ID required for memory operations.",
            )
            
        try:
            async with get_session() as session:
                repo = MemoryRepository(session)
                count = await repo.delete_all_for_user(user_id)
                
            return ToolResult(
                success=True,
                output=f"Deleted {count} facts about this user.",
                data={"deleted_count": count},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to delete facts: {e}",
            )