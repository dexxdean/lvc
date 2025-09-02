#!/usr/bin/env python3
"""
Whisper Speech-to-Text Adapter
Provides speech recognition using OpenAI's Whisper model
"""

# Force CPU usage to avoid MPS backend issues
import os
os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

# Disable tqdm progress bars
import sys
from contextlib import contextmanager

@contextmanager
def suppress_stdout():
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = devnull
        sys.stderr = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

import asyncio
import numpy as np
from pathlib import Path
from typing import Optional, Union
import tempfile
import wave

import whisper
import torch
from loguru import logger

# Disable MPS backend to prevent sparse tensor issues
torch.backends.mps.is_available = lambda: False


class WhisperSTT:
    """Whisper-based Speech-to-Text implementation"""
    
    def __init__(
        self,
        model_size: str = "small",
        language: str = "de",
        device: Optional[str] = None
    ):
        """
        Initialize Whisper STT
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Language code for transcription (de, en, etc.)
            device: Device to run on (cpu, cuda, mps). Auto-detected if None
        """
        self.model_size = model_size
        self.language = language
        
        # Auto-detect device if not specified (force CPU to avoid MPS issues)
        if device is None:
            if torch.cuda.is_available():
                self.device = "cuda"
            else:
                # Force CPU usage to avoid MPS backend compatibility issues
                self.device = "cpu"
                logger.info("🔧 Using CPU backend to avoid MPS compatibility issues")
        else:
            self.device = device
            
        logger.info(f"🤖 Initializing Whisper STT (model: {model_size}, device: {self.device})")
        
        # Load model
        try:
            # Suppress output during model loading
            with suppress_stdout():
                self.model = whisper.load_model(model_size, device=self.device)
            logger.success(f"✅ Whisper model '{model_size}' loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise
    
    def transcribe(
        self,
        audio_data: Union[np.ndarray, str, Path],
        sample_rate: int = 16000
    ) -> str:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Audio data as numpy array, file path, or audio file path
            sample_rate: Sample rate of audio data (if numpy array)
            
        Returns:
            Transcribed text
        """
        try:
            # Check for None or empty input
            if audio_data is None:
                logger.debug("⚠️ No audio data provided")
                return ""
            
            # Handle different input types
            if isinstance(audio_data, (str, Path)):
                # File path provided
                audio_path = str(audio_data)
            else:
                # Numpy array provided - check if empty
                if len(audio_data) == 0:
                    logger.debug("⚠️ Empty audio data")
                    return ""
                
                # Save to temporary file
                audio_path = self._save_audio_temp(audio_data, sample_rate)
            
            # Transcribe with Whisper (suppress progress output)
            with suppress_stdout():
                result = self.model.transcribe(
                    audio_path,
                    language=self.language,
                    task="transcribe",
                    fp16=False,  # Use FP32 for better compatibility
                    verbose=False,  # Disable progress output
                    no_speech_threshold=0.6,  # Higher threshold
                    logprob_threshold=-1.0,   # More strict
                    temperature=0.0,          # Most focused (no randomness)
                    compression_ratio_threshold=2.4,
                    condition_on_previous_text=False,  # Avoid repetitive text
                    suppress_blank=True,  # Suppress blank outputs
                    suppress_tokens="-1"  # Suppress common hallucination tokens
                )
            
            text = result["text"].strip()
            
            # Clean up temporary file if we created one
            if not isinstance(audio_data, (str, Path)):
                Path(audio_path).unlink(missing_ok=True)
            
            logger.debug(f"🎯 Transcribed: '{text}'")
            return text
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return ""
    
    async def transcribe_async(
        self,
        audio_data: Union[np.ndarray, str, Path],
        sample_rate: int = 16000
    ) -> str:
        """
        Async version of transcribe
        
        Args:
            audio_data: Audio data as numpy array, file path, or audio file path
            sample_rate: Sample rate of audio data (if numpy array)
            
        Returns:
            Transcribed text
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.transcribe, 
            audio_data, 
            sample_rate
        )
    
    def _save_audio_temp(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Save audio data to temporary WAV file
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate
            
        Returns:
            Path to temporary file
        """
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix='.wav', 
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()
        
        # Convert to 16-bit PCM if needed
        if audio_data.dtype != np.int16:
            # Normalize and convert to 16-bit
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                # Assume float audio is in range [-1, 1]
                audio_data = (audio_data * 32767).astype(np.int16)
            else:
                audio_data = audio_data.astype(np.int16)
        
        # Write WAV file
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return temp_path
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages"""
        return list(whisper.tokenizer.LANGUAGES.keys())
    
    def is_language_supported(self, language: str) -> bool:
        """Check if language is supported"""
        return language in self.get_supported_languages()


# Convenience function for quick transcription
def transcribe_file(
    file_path: Union[str, Path],
    model_size: str = "small",
    language: str = "de"
) -> str:
    """
    Quick transcription of audio file
    
    Args:
        file_path: Path to audio file
        model_size: Whisper model size
        language: Language code
        
    Returns:
        Transcribed text
    """
    stt = WhisperSTT(model_size=model_size, language=language)
    return stt.transcribe(file_path)


if __name__ == "__main__":
    # Test the STT adapter
    logger.info("🧪 Testing Whisper STT Adapter...")
    
    stt = WhisperSTT(model_size="small", language="de")
    
    # Test with a simple audio array (silence)
    test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
    result = stt.transcribe(test_audio, sample_rate=16000)
    
    logger.info(f"Test result: '{result}'")
    logger.success("✅ Whisper STT Adapter test completed")
