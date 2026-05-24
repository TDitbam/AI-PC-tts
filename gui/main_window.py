import sys
import asyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTextEdit, QWidget, QLabel
from PySide6.QtCore import Qt, Signal, QObject, QThread
from core.event_bus import EventBus

class AsyncEventBridge(QObject):
    """Bridge to connect async events to Qt signals."""
    user_speech_received = Signal(str)
    ai_response_received = Signal(str)
    ai_chunk_received = Signal(str)

    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        
    def start(self, loop):
        self.event_bus.subscribe("user_speech", self._on_user_speech)
        self.event_bus.subscribe("ai_response", self._on_ai_response)
        self.event_bus.subscribe("ai_response_chunk", self._on_ai_chunk)

    def _on_user_speech(self, text):
        self.user_speech_received.emit(text)

    def _on_ai_response(self, text):
        self.ai_response_received.emit(text)

    def _on_ai_chunk(self, chunk):
        self.ai_chunk_received.emit(chunk)

class JarvisGUI(QMainWindow):
    def __init__(self, bridge: AsyncEventBridge):
        super().__init__()
        self.bridge = bridge
        self.setWindowTitle("Jarvis AI Assistant")
        self.resize(600, 400)

        layout = QVBoxLayout()
        
        self.status_label = QLabel("Jarvis is listening...")
        layout.addWidget(self.status_label)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Connect signals
        self.bridge.user_speech_received.connect(self.display_user_speech)
        self.bridge.ai_response_received.connect(self.display_ai_response)
        self.bridge.ai_chunk_received.connect(self.display_ai_chunk)

        self._current_ai_msg = ""

    def display_user_speech(self, text):
        self.chat_display.append(f"<b>You:</b> {text}")

    def display_ai_response(self, text):
        # We handle chunks separately for streaming feel, 
        # but this can be used for final response.
        self._current_ai_msg = "" # Reset for next one

    def display_ai_chunk(self, chunk):
        if not self._current_ai_msg:
            self.chat_display.append("<b>Jarvis:</b> ")
        
        self._current_ai_msg += chunk
        # Moving cursor to end and inserting text
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.insertText(chunk)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

def run_gui(orchestrator):
    app = QApplication(sys.argv)
    
    loop = asyncio.get_event_loop()
    bridge = AsyncEventBridge(orchestrator.event_bus)
    bridge.start(loop)
    
    window = JarvisGUI(bridge)
    window.show()
    
    # Integration between Qt and asyncio can be tricky.
    # For a simple prototype, we can run Qt's event loop.
    # To properly integrate them, something like qasync is better.
    sys.exit(app.exec())
