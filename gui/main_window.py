import customtkinter as ctk
import queue
import threading
import asyncio
from core.event_bus import EventBus

class JarvisGUI(ctk.CTk):
    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        self.queue = queue.Queue()

        self.title("Jarvis AI Assistant")
        self.geometry("600x500")

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(self, text="Jarvis is listening...", font=("Arial", 14))
        self.status_label.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.chat_display = ctk.CTkTextbox(self, font=("Arial", 12))
        self.chat_display.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.chat_display.configure(state="disabled")

        self._current_ai_msg = ""
        
        # Subscribe to events
        self.event_bus.subscribe("user_speech", self._on_user_speech)
        self.event_bus.subscribe("ai_response", self._on_ai_response)
        self.event_bus.subscribe("ai_response_chunk", self._on_ai_chunk)

        # Start checking the queue
        self.after(100, self._process_queue)

    def _on_user_speech(self, text):
        self.queue.put(("user", text))

    def _on_ai_response(self, text):
        self.queue.put(("ai_done", text))

    def _on_ai_chunk(self, chunk):
        self.queue.put(("ai_chunk", chunk))

    def _process_queue(self):
        try:
            while True:
                msg_type, data = self.queue.get_nowait()
                if msg_type == "user":
                    self._append_text(f"You: {data}\n", "blue")
                elif msg_type == "ai_chunk":
                    if not self._current_ai_msg:
                        self._append_text("Jarvis: ", "green")
                    self._current_ai_msg += data
                    self._append_text(data)
                elif msg_type == "ai_done":
                    self._append_text("\n\n")
                    self._current_ai_msg = ""
                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_queue)

    def _append_text(self, text, color=None):
        self.chat_display.configure(state="normal")
        # Custom coloring is limited in CTkTextbox, but we can append text
        self.chat_display.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

def run_gui(orchestrator):
    # Set appearance mode
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    gui = JarvisGUI(orchestrator.event_bus)
    
    # We need to run the orchestrator in a background thread 
    # because tkinter.mainloop() is blocking.
    def run_async_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(orchestrator.start())
        loop.run_forever()

    threading.Thread(target=run_async_loop, daemon=True).start()
    
    gui.mainloop()
