"""Web search tool using DuckDuckGo."""

from ddgs import DDGS

from bot.tools.base import BaseTool, ToolResult


class SearchTool(BaseTool):
    """Search the web for information."""
    
    name = "search_web"
    description = "Search the web for current events, news, facts, and general information."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query (e.g. 'President of Ukraine', 'weather in Kyiv', 'latest tech news')",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "default": 5,
            },
        },
        "required": ["query"],
    }
    
    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        """Execute web search."""
        try:
            # Synchrnous DDGS used in async environment (should ideally be run in executor,
            # but for simple text search it's usually fast enough)
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                return ToolResult(
                    success=True,
                    output="No results found.",
                    data=[],
                )
            
            # Format output
            output_lines = [f"🔍 Results for '{query}':\n"]
            for i, res in enumerate(results, 1):
                title = res.get("title", "No title")
                body = res.get("body", "No description")
                href = res.get("href", "#")
                output_lines.append(f"{i}. [{title}]({href})\n   {body}\n")
            
            return ToolResult(
                success=True,
                output="\n".join(output_lines),
                data=results,
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Search failed: {e}",
            )
