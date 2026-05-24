# Jarvis AI Assistant

Jarvis is a powerful, visually appealing, and modular AI Assistant designed for real-time voice interaction. It combines Speech-to-Text (STT), Large Language Models (LLMs) via Ollama, and Text-to-Speech (TTS) into a seamless, low-latency pipeline.

## 🚀 Features

- **Always Listen Mode**: No wake word required. Jarvis listens and responds directly to your voice commands.
- **Intuitive GUI**: A professional dark-mode control center built with PySide6 and CustomTkinter.
- **Persistent Configuration**: All settings (AI Model, TTS Voice, Audio Device, etc.) are saved automatically in `config.ini`.
- **Modular Architecture**: Decoupled components communicating via an asynchronous `EventBus`.
- **Low Latency**: Optimized audio processing and streaming AI responses.
- **Multilingual Support**: Strong support for Thai and English.

## 🛠️ Technology Stack

- **GUI**: PySide6, CustomTkinter
- **AI**: Ollama (supports any local model like `gemma`, `qwen`, `llama`)
- **STT**: Google Speech Recognition (Optimized for Thai)
- **TTS**: Edge-TTS (High-quality neural voices)
- **Audio**: Sounddevice, Pygame Mixer
- **Concurrency**: `asyncio` + `threading`

## 📋 Prerequisites

1. **Python 3.10+**
2. **Ollama**: [Download and install Ollama](https://ollama.ai/)
3. **Models**: Pull your preferred model (e.g., `ollama pull gemma2:9b` or use your custom `gemma4`)

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/TDitbam/AI-PC-tts.git
   cd AI-PC-tts
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 Usage

### Running the GUI
The easiest way to use Jarvis is via the Control Center:
```bash
gui.cmd
# OR
python main.py --gui
```

### Configuration
You can configure Jarvis directly from the **Settings** tab in the GUI:
- **AI Model**: Change the local model name.
- **Always Listen**: Toggle between continuous listening and wake-word mode.
- **TTS Voice**: Select from various high-quality neural voices.
- **Audio Input**: Switch between connected microphones.

## 🏗️ Project Structure

- `core/`: Event bus, configuration, and main orchestrator.
- `gui/`: UI components and main window.
- `ai/`: Ollama client and AI logic.
- `audio/`: Audio capture and playback management.
- `stt/`: Speech-to-Text processing.
- `tts/`: Text-to-Speech generation and engine.
- `commands/`: Intent routing and functional commands.
- `memory/`: Chat history and context management.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open-source. See the LICENSE file for details (if available).
