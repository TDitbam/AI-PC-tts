# Jarvis AI Assistant - Architectural Mandates

## Core Principles
- **Async First:** Use `asyncio` for all I/O bound operations and the main event loop.
- **Modular Design:** Keep components decoupled. Communication between modules should happen via an `EventBus`.
- **Thread Safety:** Ensure audio processing and long-running AI tasks don't block the GUI or the main loop. Use `threading` or `multiprocessing` where appropriate, managed by async wrappers.
- **Low Latency:** Optimize audio pipelines and AI streaming for real-time interaction.
- **Clean Architecture:** Separate concerns. Logic should not be leaked between modules.

## Module Responsibilities
- `core/`: Event bus, configuration, and main application orchestrator.
- `audio/`: Queue-based audio capture and playback pipeline.
- `stt/`: Speech-to-text implementation (Faster-Whisper).
- `tts/`: Text-to-speech implementation.
- `ai/`: AI client implementation (Ollama qwen3:8b).
- `memory/`: Short-term and long-term memory management.
- `commands/`: Intent classification and command routing.
- `gui/`: PySide6-based user interface.

## Implementation Guidelines
- Avoid circular imports by using the `EventBus` for cross-module communication.
- Every module must have corresponding unit tests in the `tests/` directory.
- Use type hints for all function signatures.
- Streaming responses from AI should be handled as async generators.
- Windows optimization: Ensure paths and audio drivers are handled correctly for Win32.

## Technology Stack
- **Language:** Python 3.10+
- **AI:** Ollama (qwen3:8b)
- **STT:** Faster-Whisper
- **GUI:** PySide6
- **Concurrency:** asyncio + threading
