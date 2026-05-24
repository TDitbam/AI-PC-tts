import customtkinter as ctk
import queue
import threading
import asyncio
import sounddevice as sd
import logging
from core.event_bus import EventBus

logger = logging.getLogger(__name__)

class JarvisGUI(ctk.CTk):
    def __init__(self, orchestrator, loop):
        super().__init__()
        self.orchestrator = orchestrator
        self.event_bus = orchestrator.event_bus
        self.loop = loop
        self.queue = queue.Queue()

        self.title("Jarvis AI Assistant - Control Center")
        self.geometry("800x700")

        # Tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        self.tabview.add("Chat")
        self.tabview.add("Settings")

        # Chat Tab
        self.tabview.tab("Chat").grid_columnconfigure(0, weight=1)
        self.tabview.tab("Chat").grid_rowconfigure(2, weight=1)

        self.device_frame = ctk.CTkFrame(self.tabview.tab("Chat"))
        self.device_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(self.device_frame, text="Audio Input:").pack(side="left", padx=10)
        self.devices = self._get_audio_devices()
        self.device_dropdown = ctk.CTkOptionMenu(
            self.device_frame, 
            values=[d['name'] for d in self.devices],
            command=self._on_device_changed
        )
        self.device_dropdown.pack(side="left", padx=10, fill="x", expand=True)
        
        self.test_btn = ctk.CTkButton(self.device_frame, text="Test Sound", width=100, command=self._test_tts)
        self.test_btn.pack(side="left", padx=10)

        # Control Buttons
        self.control_frame = ctk.CTkFrame(self.tabview.tab("Chat"))
        self.control_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.start_btn = ctk.CTkButton(self.control_frame, text="START JARVIS", fg_color="green", hover_color="darkgreen", command=self._start_jarvis)
        self.start_btn.pack(side="left", padx=20, pady=10, expand=True)

        self.stop_btn = ctk.CTkButton(self.control_frame, text="STOP JARVIS", fg_color="red", hover_color="darkred", command=self._stop_jarvis)
        self.stop_btn.pack(side="left", padx=20, pady=10, expand=True)

        self.status_label = ctk.CTkLabel(self.tabview.tab("Chat"), text="System: Stopped", font=("Arial", 16, "bold"), text_color="gray")
        self.status_label.grid(row=2, column=0, padx=10, pady=5, sticky="ew")

        self.chat_display = ctk.CTkTextbox(self.tabview.tab("Chat"), font=("Arial", 12))
        self.chat_display.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        self.chat_display.configure(state="disabled")

        # Manual Command Input
        self.input_frame = ctk.CTkFrame(self.tabview.tab("Chat"))
        self.input_frame.grid(row=4, column=0, padx=10, pady=10, sticky="ew")
        
        self.command_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Type command here (e.g., What time is it?)")
        self.command_entry.pack(side="left", padx=10, fill="x", expand=True)
        self.command_entry.bind("<Return>", lambda e: self._send_manual_command())
        
        self.send_btn = ctk.CTkButton(self.input_frame, text="Send", width=80, command=self._send_manual_command)
        self.send_btn.pack(side="left", padx=10)

        # Settings Tab
        self.tabview.tab("Settings").grid_columnconfigure(1, weight=1)

        # TTS Voice
        ctk.CTkLabel(self.tabview.tab("Settings"), text="TTS Voice:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.voice_dropdown = ctk.CTkOptionMenu(
            self.tabview.tab("Settings"),
            values=["th-TH-PremwadeeNeural", "th-TH-NiwatNeural", "en-US-AriaNeural", "en-US-GuyNeural"],
            command=self._update_tts_config
        )
        self.voice_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        # Auto Translate
        ctk.CTkLabel(self.tabview.tab("Settings"), text="Auto Translate:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.translate_switch = ctk.CTkSwitch(
            self.tabview.tab("Settings"),
            text="Off/On",
            command=self._update_tts_config
        )
        self.translate_switch.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Delay Per Char
        ctk.CTkLabel(self.tabview.tab("Settings"), text="Delay/Char (s):").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.delay_slider = ctk.CTkSlider(
            self.tabview.tab("Settings"),
            from_=0, to=0.2,
            command=lambda v: self._update_tts_config()
        )
        self.delay_slider.set(0.03)
        self.delay_slider.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

        # Always Listen
        ctk.CTkLabel(self.tabview.tab("Settings"), text="Always Listen:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.always_listen_switch = ctk.CTkSwitch(
            self.tabview.tab("Settings"),
            text="Off/On (Skip Wake Word)",
            command=self._update_stt_config
        )
        self.always_listen_switch.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        self._current_ai_msg = ""
        self._ai_is_typing = False
        
        # Subscribe to events
        self.event_bus.subscribe("user_speech", self._on_user_speech)
        self.event_bus.subscribe("ai_response", self._on_ai_response)
        self.event_bus.subscribe("ai_response_chunk", self._on_ai_chunk)
        self.event_bus.subscribe("system_status", self._on_system_status)

        # Start checking the queue
        self.after(100, self._process_queue)

    def _start_jarvis(self):
        """Start the orchestrator."""
        asyncio.run_coroutine_threadsafe(
            self.orchestrator.start(),
            self.loop
        )

    def _stop_jarvis(self):
        """Stop the orchestrator."""
        asyncio.run_coroutine_threadsafe(
            self.orchestrator.stop(),
            self.loop
        )

    def _on_system_status(self, status):
        """Update the status label in the GUI thread."""
        self.queue.put(("status", status))

    def _get_audio_devices(self):
        devices = sd.query_devices()
        input_devices = []
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                input_devices.append({'id': i, 'name': f"{i}: {d['name']}"})
        return input_devices

    def _on_device_changed(self, selected_name):
        device_id = int(selected_name.split(":")[0])
        self.orchestrator.change_audio_device(device_id)

    def _update_tts_config(self, *args):
        config = {
            "voice": self.voice_dropdown.get(),
            "auto_translate": "True" if self.translate_switch.get() else "False",
            "delay_per_char": str(self.delay_slider.get())
        }
        self.orchestrator.tts.update_config(config)

    def _update_stt_config(self, *args):
        self.orchestrator.stt.always_listen = self.always_listen_switch.get()
        logger.info(f"STT Always Listen: {self.orchestrator.stt.always_listen}")

    def _test_tts(self):
        """Manually trigger a TTS test."""
        test_text = "ทดสอบระบบเสียงครับ"
        asyncio.run_coroutine_threadsafe(
            self.orchestrator.tts.speak(test_text),
            self.loop
        )

    def _send_manual_command(self):
        """Send a text command directly to the orchestrator."""
        text = self.command_entry.get().strip()
        if text:
            self.command_entry.delete(0, "end")
            asyncio.run_coroutine_threadsafe(
                self.orchestrator.event_bus.emit("user_speech", text),
                self.loop
            )

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
                    self._append_text(f"You: {data}\n")
                elif msg_type == "ai_chunk":
                    if not data:
                        continue
                    if not self._ai_is_typing:
                        self._append_text("Jarvis: ")
                        self._ai_is_typing = True
                    self._current_ai_msg += data
                    self._append_text(data)
                elif msg_type == "ai_done":
                    if self._ai_is_typing:
                        self._append_text("\n\n")
                    self._current_ai_msg = ""
                    self._ai_is_typing = False
                elif msg_type == "status":
                    self._update_status_ui(data)
                self.queue.task_done()
        except queue.Empty:
            pass
        finally:
            self.after(100, self._process_queue)

    def _update_status_ui(self, status):
        """Update status label and button states based on orchestrator status."""
        self.status_label.configure(text=f"System: {status}")
        
        if status == "Active":
            self.status_label.configure(text_color="green")
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        elif status == "Thinking":
            self.status_label.configure(text_color="yellow")
        elif status == "Stopped":
            self.status_label.configure(text_color="gray")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
        elif status == "Error":
            self.status_label.configure(text_color="red")
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")

    def _append_text(self, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", text)
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

def run_gui(orchestrator):
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # We need to run the orchestrator in a background thread 
    # but capture its loop to communicate with it.
    loop_holder = {}
    ready_event = threading.Event()

    def run_async_loop():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop_holder['loop'] = loop
        ready_event.set()
        loop.run_until_complete(orchestrator.start())
        loop.run_forever()

    threading.Thread(target=run_async_loop, daemon=True).start()
    
    # Wait for loop to be ready
    ready_event.wait()
    
    gui = JarvisGUI(orchestrator, loop_holder['loop'])
    gui.mainloop()
