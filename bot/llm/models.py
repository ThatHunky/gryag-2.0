"""Model capability detection."""

from dataclasses import dataclass


@dataclass
class ModelCapabilities:
    """Detected model capabilities."""
    
    supports_vision: bool = False
    supports_tools: bool = True
    supports_streaming: bool = True
    supports_reasoning: bool = False
    max_context_tokens: int = 8192
    max_output_tokens: int = 4096


# Known model capabilities
MODEL_CAPABILITIES: dict[str, ModelCapabilities] = {
    "gpt-4o": ModelCapabilities(
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        supports_reasoning=False,
        max_context_tokens=128000,
        max_output_tokens=16384,
    ),
    "gpt-4o-mini": ModelCapabilities(
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        supports_reasoning=False,
        max_context_tokens=128000,
        max_output_tokens=16384,
    ),
    "o1": ModelCapabilities(
        supports_vision=True,
        supports_tools=True,
        supports_streaming=False,
        supports_reasoning=True,
        max_context_tokens=200000,
        max_output_tokens=100000,
    ),
    "o1-mini": ModelCapabilities(
        supports_vision=False,
        supports_tools=True,
        supports_streaming=False,
        supports_reasoning=True,
        max_context_tokens=128000,
        max_output_tokens=65536,
    ),
    "o3-mini": ModelCapabilities(
        supports_vision=False,
        supports_tools=True,
        supports_streaming=False,
        supports_reasoning=True,
        max_context_tokens=200000,
        max_output_tokens=100000,
    ),
    "claude-3-opus": ModelCapabilities(
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        supports_reasoning=False,
        max_context_tokens=200000,
        max_output_tokens=4096,
    ),
    "claude-3-sonnet": ModelCapabilities(
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        supports_reasoning=False,
        max_context_tokens=200000,
        max_output_tokens=4096,
    ),
    "gemini-2.0-flash": ModelCapabilities(
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        supports_reasoning=True,
        max_context_tokens=1000000,
        max_output_tokens=8192,
    ),
}


def get_capabilities(model_name: str) -> ModelCapabilities:
    """Get capabilities for a model, with fallback defaults."""
    # Check exact match
    if model_name in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model_name]
    
    # Check partial match
    for known_model, caps in MODEL_CAPABILITIES.items():
        if known_model in model_name.lower():
            return caps
    
    # Default capabilities
    return ModelCapabilities()


def supports_vision(model_name: str) -> bool:
    """Check if model supports vision."""
    return get_capabilities(model_name).supports_vision


def supports_reasoning(model_name: str) -> bool:
    """Check if model supports extended thinking."""
    return get_capabilities(model_name).supports_reasoning
