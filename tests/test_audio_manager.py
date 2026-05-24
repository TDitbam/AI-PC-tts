import numpy as np
import pytest
import time
from audio.audio_manager import AudioManager

def test_audio_manager_init():
    am = AudioManager()
    assert am.sample_rate == 16000
    assert am.channels == 1
    assert not am.is_recording
    assert not am.is_playing

# Note: Testing actual recording/playback requires hardware and can be flaky in CI.
# We test the queue logic.

def test_audio_manager_queue_logic():
    am = AudioManager()
    test_data = np.zeros(1024, dtype=np.float32)
    am.input_queue.put(test_data)
    
    chunk = am.get_audio_chunk(timeout=0.1)
    assert np.array_equal(chunk, test_data)

def test_audio_manager_playback_queue(monkeypatch):
    am = AudioManager()
    # Mock start_playback to prevent the worker thread from starting and consuming the queue
    monkeypatch.setattr(am, "start_playback", lambda: None)
    
    test_data = np.zeros(1024, dtype=np.float32)
    am.play_audio(test_data)
    
    assert am.output_queue.qsize() == 1
