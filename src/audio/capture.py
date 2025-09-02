#!/usr/bin/env python3
"""
Audio Capture System
Handles microphone input and audio processing for voice control
"""

import asyncio
import numpy as np
from typing import Optional, Generator, Any
from dataclasses import dataclass
import threading
import queue

import pyaudio
import webrtcvad
from loguru import logger


@dataclass
class AudioConfig:
    """Audio configuration"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: Any = pyaudio.paInt16
    device_index: Optional[int] = None
    device_name: Optional[str] = None


class AudioCapture:
    """Audio capture and processing system"""
    
    def __init__(
        self,
        device_name: Optional[str] = None,
        sample_rate: int = 16000,  # Unified to 16kHz for Whisper
        channels: int = 1,
        buffer_size: int = 512  # Increased for stability
    ):
        """
        Initialize audio capture
        
        Args:
            device_name: Name of audio input device (None for default)
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1 for mono)
            buffer_size: Buffer size for audio chunks
        """
        self.device_name = device_name
        self.sample_rate = sample_rate
        self.channels = channels
        self.buffer_size = buffer_size
        
        self._audio = None
        self._stream = None
        self._is_recording = False
        self._audio_queue = queue.Queue()
        self._vad = webrtcvad.Vad(2)  # Aggressiveness level 0-3
        
        logger.info(f"🎤 Initializing audio capture (device: {device_name or 'default'})")
        
        # Initialize PyAudio
        self._init_audio()
        
    def _init_audio(self):
        """Initialize PyAudio and find device"""
        try:
            self._audio = pyaudio.PyAudio()
            
            # Find device index if name provided
            device_index = None
            if self.device_name:
                device_index = self._find_device_by_name(self.device_name)
                if device_index is None:
                    logger.warning(f"⚠️ Device '{self.device_name}' not found, using default")
            
            # Test device
            if device_index is not None:
                device_info = self._audio.get_device_info_by_index(device_index)
                logger.info(f"🎧 Using device: {device_info['name']}")
                logger.info(f"📊 Max input channels: {device_info['maxInputChannels']}")
                logger.info(f"🔊 Default sample rate: {device_info['defaultSampleRate']}")
            
            self.device_index = device_index
            logger.success("✅ Audio system initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize audio: {e}")
            raise
    
    def _find_device_by_name(self, device_name: str) -> Optional[int]:
        """Find device index by name"""
        for i in range(self._audio.get_device_count()):
            try:
                device_info = self._audio.get_device_info_by_index(i)
                if device_name.lower() in device_info['name'].lower():
                    logger.debug(f"🎯 Found device: {device_info['name']} (index {i})")
                    return i
            except Exception:
                continue
        return None
    
    def start_stream(self):
        """Start audio input stream"""
        if self._stream is not None:
            logger.warning("⚠️ Stream already active")
            return
        
        try:
            self._stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.buffer_size,
                stream_callback=self._audio_callback
            )
            
            self._stream.start_stream()
            self._is_recording = True
            
            logger.success("🎙️ Audio stream started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start audio stream: {e}")
            raise
    
    def stop_stream(self):
        """Stop audio input stream"""
        self._is_recording = False
        
        if self._stream is not None:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
            logger.info("⏹️ Audio stream stopped")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback for incoming audio"""
        if status:
            logger.warning(f"⚠️ Audio callback status: {status}")
        
        # Convert to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.int16)
        
        # Add to queue for processing
        if not self._audio_queue.full():
            self._audio_queue.put(audio_data)
        
        return (None, pyaudio.paContinue)
    
    def get_audio_chunk(self) -> Optional[np.ndarray]:
        """Get next audio chunk (non-blocking)"""
        try:
            return self._audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    async def capture_async(self, timeout: float = 0.1) -> Optional[np.ndarray]:
        """Async audio capture"""
        loop = asyncio.get_event_loop()
        
        def _get_chunk():
            try:
                return self._audio_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        
        return await loop.run_in_executor(None, _get_chunk)
    
    def is_speech(self, audio_data: np.ndarray) -> bool:
        """
        Check if audio contains speech using WebRTC VAD
        
        Args:
            audio_data: Audio data as int16 numpy array
            
        Returns:
            True if speech detected
        """
        try:
            # VAD requires specific frame sizes (10, 20, or 30 ms)
            frame_duration = 30  # ms
            frame_size = int(self.sample_rate * frame_duration / 1000)
            
            # Ensure we have enough data
            if len(audio_data) < frame_size:
                return False
            
            # Take first frame_size samples
            frame = audio_data[:frame_size]
            
            # Convert to bytes
            frame_bytes = frame.tobytes()
            
            # Use VAD
            return self._vad.is_speech(frame_bytes, self.sample_rate)
            
        except Exception as e:
            logger.debug(f"VAD error: {e}")
            return False
    
    async def capture_command(
        self,
        max_duration: float = 5.0,
        silence_timeout: float = 1.5
    ) -> np.ndarray:
        """
        Capture a voice command with silence detection
        
        Args:
            max_duration: Maximum recording duration in seconds
            silence_timeout: Stop recording after this much silence
            
        Returns:
            Audio data as numpy array
        """
        logger.info("🎤 Listening for command...")
        
        frames = []
        silent_chunks = 0
        max_silent_chunks = int(silence_timeout * self.sample_rate / self.buffer_size)
        max_chunks = int(max_duration * self.sample_rate / self.buffer_size)
        
        chunk_count = 0
        speech_detected = False
        
        while chunk_count < max_chunks:
            chunk = await self.capture_async(timeout=0.1)
            
            if chunk is None:
                await asyncio.sleep(0.01)
                continue
            
            frames.append(chunk)
            chunk_count += 1
            
            # Check for speech
            if self.is_speech(chunk):
                speech_detected = True
                silent_chunks = 0
                logger.debug("🗣️ Speech detected")
            else:
                if speech_detected:  # Only count silence after speech started
                    silent_chunks += 1
                    
                    # Stop if we've been silent long enough
                    if silent_chunks >= max_silent_chunks:
                        logger.info(f"🔇 Silence detected, stopping after {len(frames)} chunks")
                        break
        
        # Combine all frames
        if frames:
            audio_data = np.concatenate(frames)
            logger.info(f"🎵 Captured {len(audio_data)} samples ({len(audio_data)/self.sample_rate:.2f}s)")
            return audio_data
        else:
            logger.warning("⚠️ No audio captured")
            return np.array([], dtype=np.int16)
    
    def list_devices(self) -> list:
        """List all available audio devices"""
        devices = []
        
        for i in range(self._audio.get_device_count()):
            try:
                device_info = self._audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Only input devices
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'sample_rate': device_info['defaultSampleRate']
                    })
            except Exception:
                continue
        
        return devices
    
    async def stop(self):
        """Clean shutdown"""
        self.stop_stream()
        
        if self._audio is not None:
            self._audio.terminate()
            self._audio = None
            
        logger.info("🛑 Audio capture stopped")
    
    def __enter__(self):
        """Context manager entry"""
        self.start_stream()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        asyncio.create_task(self.stop())


# Utility functions
def list_audio_devices():
    """List all available audio input devices"""
    audio = pyaudio.PyAudio()
    
    print("Available Audio Input Devices:")
    print("=" * 50)
    
    for i in range(audio.get_device_count()):
        try:
            device_info = audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                print(f"[{i:2d}] {device_info['name']}")
                print(f"     Channels: {device_info['maxInputChannels']}")
                print(f"     Sample Rate: {device_info['defaultSampleRate']:.0f} Hz")
                print()
        except Exception:
            continue
    
    audio.terminate()


if __name__ == "__main__":
    # Test the audio capture
    logger.info("🧪 Testing Audio Capture...")
    
    # List devices
    list_audio_devices()
    
    # Test capture
    async def test_capture():
        capture = AudioCapture()
        capture.start_stream()
        
        logger.info("Recording 3 seconds of audio...")
        
        frames = []
        for _ in range(30):  # 3 seconds at ~10 chunks per second
            chunk = await capture.capture_async()
            if chunk is not None:
                frames.append(chunk)
            await asyncio.sleep(0.1)
        
        await capture.stop()
        
        if frames:
            audio_data = np.concatenate(frames)
            logger.success(f"✅ Captured {len(audio_data)} samples")
        else:
            logger.warning("⚠️ No audio captured")
    
    # Run test
    asyncio.run(test_capture())
