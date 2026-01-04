"""Base tool interface for LLM tool calling."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """Result from tool execution."""
    
    success: bool
    output: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    
    def to_message(self) -> str:
        """Convert result to message for LLM."""
        if self.success:
            return self.output
        return f"Error: {self.error or 'Unknown error'}"


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Subclasses must implement:
    - name: Tool name (used in function calls)
    - description: Human-readable description
    - parameters: JSON Schema for parameters
    - execute: Async execution method
    """
    
    name: str
    description: str
    parameters: dict[str, Any]
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def to_openai_schema(self) -> dict:
        """Convert to OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
    
    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
