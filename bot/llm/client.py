"""OpenAI-compatible LLM client with reliability features."""

import asyncio
import logging
from typing import Any

from openai import AsyncOpenAI, APIError, RateLimitError, APITimeoutError

from bot.config import get_settings
from bot.utils.errors import LLMError

logger = logging.getLogger(__name__)


class LLMClient:
    """
    OpenAI-compatible API client with reliability features.
    
    Features:
    - Configurable base URL for any OpenAI-compatible API
    - Retry with exponential backoff
    - Automatic fallback model
    - Request timeout
    - Response token limit
    - Typing indicator support
    """

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url,
            timeout=self.settings.llm_timeout_seconds,
        )
        
        # Vision client (separate endpoint or fallback to primary)
        vision_api_key = self.settings.llm_vision_api_key or self.settings.llm_api_key
        vision_base_url = self.settings.llm_vision_base_url or self.settings.llm_base_url
        self.vision_client = AsyncOpenAI(
            api_key=vision_api_key,
            base_url=vision_base_url,
            timeout=self.settings.llm_timeout_seconds,
        )
        self.vision_model = self.settings.llm_vision_model or self.settings.llm_model
        self.vision_enabled = self.settings.llm_vision_enabled

    async def complete(
        self,
        messages: list[dict],
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.7,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
    ) -> str:
        """
        Complete a chat conversation.
        
        Returns the assistant message content.
        """
        model = model or self.settings.llm_model
        max_tokens = max_tokens or self.settings.llm_max_response_tokens
        
        for attempt in range(self.settings.llm_max_retries + 1):
            try:
                response = await self._make_request(
                    messages=messages,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=tools,
                    tool_choice=tool_choice,
                )
                
                message = response.choices[0].message
                content = message.content or ""
                
                # Filter out reasoning/thinking tags
                content = self._filter_thinking(content)
                
                return content
                
            except RateLimitError as e:
                logger.warning(f"Rate limit hit (attempt {attempt + 1}): {e}")
                if attempt < self.settings.llm_max_retries:
                    await self._backoff(attempt)
                else:
                    raise LLMError(str(e), "llm_rate_limit")
                    
            except APITimeoutError as e:
                logger.warning(f"Timeout (attempt {attempt + 1}): {e}")
                if attempt < self.settings.llm_max_retries:
                    await self._backoff(attempt)
                else:
                    raise LLMError(str(e), "llm_timeout")
                    
            except APIError as e:
                logger.error(f"API error (attempt {attempt + 1}): {e}")
                
                # Try fallback model if available
                if (
                    self.settings.llm_fallback_model
                    and model != self.settings.llm_fallback_model
                ):
                    logger.info(f"Switching to fallback model: {self.settings.llm_fallback_model}")
                    model = self.settings.llm_fallback_model
                    continue
                
                if attempt < self.settings.llm_max_retries:
                    await self._backoff(attempt)
                else:
                    raise LLMError(str(e), "model_unavailable")
        
        raise LLMError("Max retries exceeded", "llm_timeout")

    async def complete_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        model: str | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        """
        Complete with tool calling support.
        
        Returns dict with 'content' and 'tool_calls'.
        """
        model = model or self.settings.llm_model
        max_tokens = max_tokens or self.settings.llm_max_response_tokens
        
        response = await self._make_request(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            tools=tools,
        )
        
        message = response.choices[0].message
        
        return {
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                for tc in (message.tool_calls or [])
            ],
        }

    async def _make_request(
        self,
        messages: list[dict],
        model: str,
        max_tokens: int,
        temperature: float = 0.7,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
    ):
        """Make the actual API request."""
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if tools:
            kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        
        # Add reasoning if enabled and supported
        if self.settings.llm_reasoning_enabled:
            # Some models use reasoning_effort parameter
            if "o1" in model or "o3" in model:
                kwargs["reasoning_effort"] = self.settings.llm_reasoning_effort
        
        return await self.client.chat.completions.create(**kwargs)

    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff with jitter."""
        import random
        base_delay = 2 ** attempt
        jitter = random.uniform(0, 1)
        delay = min(base_delay + jitter, 30)  # Cap at 30 seconds
        logger.debug(f"Backing off for {delay:.2f} seconds")
        await asyncio.sleep(delay)

    async def count_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimate: ~4 characters per token
        return len(text) // 4

    def _filter_thinking(self, content: str) -> str:
        """Filter out reasoning/thinking tags from LLM output.
        
        Some models output thinking in tags like:
        - <think>...</think>
        - <reasoning>...</reasoning>
        - <reflection>...</reflection>
        """
        import re
        
        # Remove common thinking/reasoning tags and their content
        patterns = [
            r'<think>.*?</think>',
            r'<thinking>.*?</thinking>',
            r'<reasoning>.*?</reasoning>',
            r'<reflection>.*?</reflection>',
            r'<internal>.*?</internal>',
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE)
        
        # Also handle unclosed tags (e.g., just </think> at start)
        content = re.sub(r'^</?(think|thinking|reasoning|reflection|internal)>\s*', '', content, flags=re.IGNORECASE)
        
        return content.strip()

    async def complete_with_vision(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float = 0.7,
    ) -> str | None:
        """
        Complete a vision request with image content.
        
        Uses the vision-specific endpoint/model if configured.
        Returns None if vision is disabled.
        """
        if not self.vision_enabled:
            return None
        
        max_tokens = max_tokens or self.settings.llm_max_response_tokens
        
        try:
            response = await self.vision_client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            content = response.choices[0].message.content or ""
            return self._filter_thinking(content)
            
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return None
