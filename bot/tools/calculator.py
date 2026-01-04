"""Calculator tool for safe math evaluation."""

import ast
import operator

from bot.tools.base import BaseTool, ToolResult


class CalculatorTool(BaseTool):
    """Safe math expression calculator."""
    
    name = "calculator"
    description = "Evaluate a mathematical expression. Supports basic arithmetic (+, -, *, /, **), parentheses, and common functions."
    parameters = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Math expression to evaluate (e.g., '2 + 2 * 3' or '(10 + 5) / 3')",
            },
        },
        "required": ["expression"],
    }
    
    # Safe operators
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    async def execute(self, expression: str) -> ToolResult:
        """Safely evaluate a math expression."""
        try:
            result = self._safe_eval(expression)
            return ToolResult(
                success=True,
                output=f"{expression} = {result}",
                data={"result": result},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Invalid expression: {e}",
            )
    
    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate expression using AST."""
        tree = ast.parse(expression, mode="eval")
        return self._eval_node(tree.body)
    
    def _eval_node(self, node) -> float:
        """Recursively evaluate AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant: {node.value}")
        
        elif isinstance(node, ast.BinOp):
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {node.op}")
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            return op(left, right)
        
        elif isinstance(node, ast.UnaryOp):
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {node.op}")
            return op(self._eval_node(node.operand))
        
        else:
            raise ValueError(f"Unsupported expression: {type(node)}")
