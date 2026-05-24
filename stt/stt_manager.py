import threading
import queue
import numpy as np
from faster_whisper import WhisperModel
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

class STTManager:
    """
    Manages Speech-to-Text transcription using Faster-Whisper.
    """
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.is_running = False

    def transcribe_stream(self, audio_queue: queue.Queue, callback: callable):
        """
        Start transcribing from an audio queue in a separate thread.
        """
        if self.is_running:
            return
            
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, args=(audio_queue, callback), daemon=True)
        self._thread.start()
        logger.info("STT transcription started.")

    def stop(self):
        """Stop the transcription thread."""
        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        logger.info("STT transcription stopped.")

    def _worker(self, audio_queue: queue.Queue, callback: callable):
        """
        Worker thread that accumulates audio and transcribes when enough is available.
        """
        audio_buffer = []
        is_awake = False
        wake_word = "jarvis"
        
        while self.is_running and not self._stop_event.is_set():
            try:
                # Get audio chunk (usually 1024 samples)
                chunk = audio_queue.get(timeout=0.1)
                audio_buffer.append(chunk)
                
                # If we have enough audio (e.g., 2 seconds at 16kHz = 32000 samples)
                current_samples = sum(len(c) for c in audio_buffer)
                if current_samples >= 32000:
                    audio_data = np.concatenate(audio_buffer).flatten()
                    audio_buffer = [] # Reset buffer
                    
                    segments, info = self.model.transcribe(audio_data, beam_size=5)
                    text = "".join([segment.text for segment in segments]).strip()
                    
                    if text:
                        if not is_awake:
                            if wake_word in text.lower():
                                logger.info("Wake word detected!")
                                is_awake = True
                                # Strip wake word for cleaner command
                                text = text.lower().replace(wake_word, "").strip()
                                if text:
                                    callback(text)
                        else:
                            logger.debug(f"Transcribed: {text}")
                            callback(text)
                            # Simple logic: stay awake for next command. 
                            # In real use, you'd reset is_awake after timeout or specific command.
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.exception("Error in STT worker")
                break
        
        self.is_running = False
        logger.info("STT worker finished.")

    def transcribe_file(self, file_path: str) -> str:
        """Transcribe an entire audio file."""
        segments, info = self.model.transcribe(file_path, beam_size=5)
        return "".join([segment.text for segment in segments]).strip()
