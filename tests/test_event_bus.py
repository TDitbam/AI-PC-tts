import asyncio
import pytest
from core.event_bus import EventBus

@pytest.mark.asyncio
async def test_event_bus_emit_subscribe():
    bus = EventBus()
    received_data = []

    async def listener(data):
        received_data.append(data)

    bus.subscribe("test_event", listener)
    await bus.emit("test_event", "hello")
    
    assert "hello" in received_data

@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    bus = EventBus()
    received_data = []

    async def listener(data):
        received_data.append(data)

    bus.subscribe("test_event", listener)
    bus.unsubscribe("test_event", listener)
    await bus.emit("test_event", "hello")
    
    assert len(received_data) == 0

@pytest.mark.asyncio
async def test_event_bus_multiple_listeners():
    bus = EventBus()
    count = 0

    async def listener1(data):
        nonlocal count
        count += 1

    async def listener2(data):
        nonlocal count
        count += 1

    bus.subscribe("test_event", listener1)
    bus.subscribe("test_event", listener2)
    await bus.emit("test_event", None)
    
    assert count == 2
