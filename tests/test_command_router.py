import pytest
import asyncio
from commands.command_router import CommandRouter

@pytest.mark.asyncio
async def test_command_router_register_and_handle():
    router = CommandRouter()
    
    async def mock_handler(entities):
        return f"Handled {entities.get('name')}"
    
    router.register_command("greet", mock_handler)
    result = await router.handle_intent("greet", {"name": "User"})
    
    assert result == "Handled User"

@pytest.mark.asyncio
async def test_command_router_no_handler():
    router = CommandRouter()
    result = await router.handle_intent("unknown")
    assert "don't know how to handle" in result
