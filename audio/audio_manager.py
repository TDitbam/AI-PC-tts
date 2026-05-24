import queue
import threading
import numpy as np
import sounddevice as sd
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class AudioManager:
    """
    Manages audio recording and playback using a queue-based pipeline.
    """
    def __init__(self, sample_rate: int = 16000, channels: int = 1, block_size: int = 1024):
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_size = block_size
        
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        self._recording_thread: Optional[threading.Thread] = None
        self._playback_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        self.is_recording = False
        self.is_playing = False

    def start_recording(self):
        """Start the audio recording thread."""
        if self.is_recording:
            return
            
        self._stop_event.clear()
        self.is_recording = True
        self._recording_thread = threading.Thread(target=self._record_worker, daemon=True)
        self._recording_thread.start()
        logger.info("Audio recording started.")

    def stop_recording(self):
        """Stop the audio recording thread."""
        self.is_recording = False
        self._stop_event.set()
        if self._recording_thread:
            self._recording_thread.join(timeout=1)
        logger.info("Audio recording stopped.")

    def _record_worker(self):
        """Worker thread for recording audio."""
        def callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio record status: {status}")
            if self.is_recording:
                self.input_queue.put(indata.copy())

        try:
            with sd.InputStream(samplerate=self.sample_rate, 
                                channels=self.channels, 
                                callback=callback, 
                                blocksize=self.block_size):
                while not self._stop_event.is_set() and self.is_recording:
                    self._stop_event.wait(0.1)
        except Exception as e:
            logger.exception("Error in recording worker")
            self.is_recording = False

    def play_audio(self, data: np.ndarray):
        """Add audio data to the playback queue."""
        self.output_queue.put(data)
        if not self.is_playing:
            self.start_playback()

    def start_playback(self):
        """Start the audio playback thread."""
        if self.is_playing:
            return
            
        self.is_playing = True
        self._playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self._playback_thread.start()
        logger.info("Audio playback started.")

    def _playback_worker(self):
        """Worker thread for playing audio."""
        try:
            while self.is_playing:
                try:
                    data = self.output_queue.get(timeout=0.5)
                    sd.play(data, self.sample_rate)
                    sd.wait() # Wait for current block to finish
                    self.output_queue.task_done()
                except queue.Empty:
                    # If queue is empty for a while, we can stop the thread or keep waiting
                    if not self.is_playing:
                        break
                    continue
        except Exception as e:
            logger.exception("Error in playback worker")
        finally:
            self.is_playing = False
            logger.info("Audio playback worker finished.")

    def get_audio_chunk(self, timeout: Optional[float] = None) -> Optional[np.ndarray]:
        """Get a chunk of recorded audio from the queue."""
        try:
            return self.input_queue.get(timeout=timeout)
        except queue.Empty:
            return None
