"""Image generation tool."""

from bot.config import get_settings
from bot.tools.base import BaseTool, ToolResult
from openai import AsyncOpenAI


class GenerateImageTool(BaseTool):
    """Generate images using AI."""
    
    name = "generate_image"
    description = "Generate an image based on a text description."
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Detailed description of the image to generate.",
            },
            "size": {
                "type": "string",
                "enum": ["1024x1024"], # "256x256", "512x512" are not supported by DALL-E 3
                "default": "1024x1024",
                "description": "Size of the image.",
            },
        },
        "required": ["prompt"],
    }
    
    async def execute(self, prompt: str, size: str = "1024x1024") -> ToolResult:
        """Execute image generation."""
        settings = get_settings()
        
        if not settings.llm_vision_enabled: # Reuse vision flag or add new one? For now assume valid key exists
             # Fallback to LLM key if no specific image key
            pass

        api_key = settings.llm_vision_api_key or settings.llm_api_key
        base_url = settings.llm_vision_base_url or settings.llm_base_url
        
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        
        try:
            response = await client.images.generate(
                model="dall-e-3", # Hardcoded for now or add to settings
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            
            return ToolResult(
                success=True,
                output=f"Image generated successfully: {image_url}",
                data={"url": image_url},
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Image generation failed: {e}",
            )
