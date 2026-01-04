"""Tool registry for auto-discovery and management."""

import logging
from typing import Type

from bot.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

TOOL_ALIASES: dict[str, str] = {
    # Backwards compatibility for older prompts / model habits
    "remember_memory": "save_user_fact",
    "recall_memories": "get_user_facts",
}


class ToolRegistry:
    """Registry for managing and discovering tools."""
    
    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """Register a tool class (instantiates it)."""
        tool = tool_class()
        self.register(tool)
    
    def get(self, name: str) -> BaseTool | None:
        """Get tool by name."""
        return self._tools.get(name)
    
    def list_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())
    
    def list_tools(self) -> list[BaseTool]:
        """List all registered tools."""
        return list(self._tools.values())
    
    def get_openai_schemas(self) -> list[dict]:
        """Get OpenAI function schemas for all tools."""
        return [tool.to_openai_schema() for tool in self._tools.values()]
    
    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(name)
        if tool is None and name in TOOL_ALIASES:
            aliased = TOOL_ALIASES[name]
            logger.info(f"Tool alias applied: {name} -> {aliased}")
            name = aliased
            tool = self.get(name)
        if tool is None:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool not found: {name}",
            )
        
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool {name} execution failed: {e}")
            return ToolResult(
                success=False,
                output="",
                error=str(e),
            )


# Global registry instance
_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _register_default_tools(_registry)
    return _registry


def _register_default_tools(registry: ToolRegistry) -> None:
    """Register default tools."""
    # Import and register tools here
    # Tools will be added as they are implemented
    from bot.tools.calculator import CalculatorTool
    from bot.tools.weather import WeatherTool
    from bot.tools.search import SearchTool
    from bot.tools.image import GenerateImageTool
    from bot.tools.memory import (
        SaveUserFactTool,
        GetUserFactsTool,
        DeleteUserFactTool,
        DeleteAllUserFactsTool,
    )
    
    registry.register(CalculatorTool())
    registry.register(WeatherTool())
    registry.register(SearchTool())
    registry.register(GenerateImageTool())
    registry.register(SaveUserFactTool())
    registry.register(GetUserFactsTool())
    registry.register(DeleteUserFactTool())
    registry.register(DeleteAllUserFactsTool())
    
    logger.info(f"Registered {len(registry.list_names())} tools")
