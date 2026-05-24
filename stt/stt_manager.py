import threading
import queue
import numpy as np
import speech_recognition as sr
import logging
import io
import wave
from typing import Optional

logger = logging.getLogger(__name__)

class STTManager:
    """
    Manages Speech-to-Text transcription using Google Speech Recognition.
    """
    def __init__(self, language: str = "th-TH"):
        self.recognizer = sr.Recognizer()
        self.language = language
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.is_running = False
        self.always_listen = False
        
        # Adjust recognizer sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

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
        logger.info(f"Google STT transcription started (Language: {self.language}).")

    def stop(self):
        """Stop the transcription thread."""
        self.is_running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)
        logger.info("STT transcription stopped.")

    def _worker(self, audio_queue: queue.Queue, callback: callable):
        """
        Worker thread that converts raw chunks to AudioData and sends to Google.
        Optimized for lower latency and better sensitivity.
        """
        audio_buffer = []
        wake_words = ["jarvis", "จาร์วิส", "จารวิส", "จา วิ ส", "ชา วิ ส", "service"]
        
        # Parameters for conversion
        sample_rate = 16000
        sample_width = 2 # 16-bit
        
        # We accumulate chunks until we have enough for recognition
        # reduced accumulation size for faster response (approx 1.0 - 1.2s)
        target_samples = 18000 
        
        logger.info("STT Worker is active.")
        
        while self.is_running and not self._stop_event.is_set():
            try:
                # Use a shorter timeout for more frequent checks
                chunk = audio_queue.get(timeout=0.05)
                audio_buffer.append(chunk)
                
                current_samples = sum(len(c) for c in audio_buffer)
                if current_samples >= target_samples:
                    raw_data = np.concatenate(audio_buffer).flatten()
                    audio_buffer = []
                    
                    # More sensitive threshold for "Always Listen"
                    rms = np.sqrt(np.mean(raw_data**2))
                    threshold = 0.003 if self.always_listen else 0.005
                    
                    if rms < threshold:
                        continue
                    
                    logger.debug(f"Processing audio chunk, RMS: {rms:.5f}")
                    
                    try:
                        int_data = (raw_data * 32767).astype(np.int16).tobytes()
                        audio_data = sr.AudioData(int_data, sample_rate, sample_width)
                        
                        # Use recognize_google for broad Thai language support
                        text = self.recognizer.recognize_google(audio_data, language=self.language)
                        
                        if text:
                            text = text.strip()
                            logger.info(f"STT Recognized: {text}")
                            
                            if self.always_listen:
                                callback(text)
                                continue

                            text_lower = text.lower()
                            triggered = False
                            for word in wake_words:
                                if word in text_lower:
                                    logger.info(f"Wake word '{word}' detected!")
                                    clean_text = text_lower.replace(word, "").strip()
                                    if clean_text:
                                        callback(clean_text)
                                    else:
                                        callback("สวัสดี")
                                    triggered = True
                                    break
                                
                    except sr.UnknownValueError:
                        # Silently ignore noise that doesn't sound like speech
                        pass
                    except sr.RequestError as e:
                        logger.error(f"Google STT Request Error: {e}")
                    except Exception as e:
                        logger.error(f"STT Recognition logic error: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Critical error in STT worker: {e}")
                break
        
        self.is_running = False
        logger.info("STT worker finished.")
