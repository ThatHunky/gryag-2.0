"""Tests for calculator tool."""

import pytest

from bot.tools.calculator import CalculatorTool


@pytest.fixture
def calculator():
    return CalculatorTool()


class TestCalculatorTool:
    """Test suite for CalculatorTool."""

    @pytest.mark.asyncio
    async def test_basic_addition(self, calculator):
        result = await calculator.execute(expression="2 + 2")
        assert result.success
        assert result.data["result"] == 4

    @pytest.mark.asyncio
    async def test_order_of_operations(self, calculator):
        result = await calculator.execute(expression="2 + 3 * 4")
        assert result.success
        assert result.data["result"] == 14

    @pytest.mark.asyncio
    async def test_parentheses(self, calculator):
        result = await calculator.execute(expression="(2 + 3) * 4")
        assert result.success
        assert result.data["result"] == 20

    @pytest.mark.asyncio
    async def test_power(self, calculator):
        result = await calculator.execute(expression="2 ** 8")
        assert result.success
        assert result.data["result"] == 256

    @pytest.mark.asyncio
    async def test_division(self, calculator):
        result = await calculator.execute(expression="10 / 4")
        assert result.success
        assert result.data["result"] == 2.5

    @pytest.mark.asyncio
    async def test_negative_numbers(self, calculator):
        result = await calculator.execute(expression="-5 + 3")
        assert result.success
        assert result.data["result"] == -2

    @pytest.mark.asyncio
    async def test_invalid_expression(self, calculator):
        result = await calculator.execute(expression="2 + + 3")
        assert not result.success
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_unsafe_code_blocked(self, calculator):
        result = await calculator.execute(expression="__import__('os')")
        assert not result.success
