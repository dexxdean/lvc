#!/usr/bin/env python3
"""
Microphone Test Tool
Test your microphone by recording and playing back audio
"""

import asyncio
import subprocess
import tempfile
import time
from pathlib import Path
import wave
import numpy as np
from typing import Optional
import sys

from loguru import logger
import click

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.audio.capture import AudioCapture
from src.stt.whisper_adapter import WhisperSTT


class MicrophoneTest:
    """Microphone testing utility"""
    
    def __init__(self, device_name: Optional[str] = None):
        """Initialize microphone test"""
        self.device_name = device_name
        self.audio_capture = None
        self.stt = None
        
    def initialize(self):
        """Initialize audio components"""
        logger.info("🎤 Initializing microphone test...")
        
        # Initialize audio capture
        self.audio_capture = AudioCapture(
            device_name=self.device_name,
            sample_rate=16000,
            channels=1,
            buffer_size=1024
        )
        
        # Initialize Whisper for transcription (optional)
        self.stt = WhisperSTT(model_size="base", language="de")
        
        logger.success("✅ Microphone test initialized")
    
    async def record_test(self, duration: float = 3.0) -> str:
        """
        Record audio for testing
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Path to recorded audio file
        """
        logger.info(f"🎤 Recording for {duration} seconds...")
        logger.info("👄 Please speak now!")
        
        # Start audio stream
        self.audio_capture.start_stream()
        
        # Record audio
        frames = []
        chunks_needed = int(duration * 16000 / 1024)  # Calculate chunks needed
        
        for i in range(chunks_needed):
            chunk = await self.audio_capture.capture_async(timeout=1.0)
            if chunk is not None and len(chunk) > 0:
                frames.append(chunk)
                
                # Show progress
                progress = (i + 1) / chunks_needed * 100
                print(f"\r🔴 Recording... {progress:.0f}% ", end="", flush=True)
            
            await asyncio.sleep(0.01)
        
        print("")  # New line after progress
        
        # Stop audio stream
        self.audio_capture.stop_stream()
        
        if not frames:
            logger.error("❌ No audio recorded!")
            return ""
        
        # Combine audio frames
        audio_data = np.concatenate(frames)
        
        # Calculate audio statistics
        audio_rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        audio_max = np.max(np.abs(audio_data))
        
        logger.info(f"📊 Audio stats: RMS={audio_rms:.2f}, Max={audio_max}, Samples={len(audio_data)}")
        
        # Save to temporary WAV file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        wav_path = temp_file.name
        temp_file.close()
        
        # Write WAV file
        with wave.open(wav_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16kHz
            wav_file.writeframes(audio_data.tobytes())
        
        logger.success(f"💾 Audio saved to: {wav_path}")
        return wav_path
    
    def play_audio(self, audio_path: str) -> bool:
        """
        Play back recorded audio
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            True if playback successful
        """
        if not audio_path or not Path(audio_path).exists():
            logger.error("❌ Audio file not found")
            return False
        
        logger.info("🔊 Playing back your recording...")
        
        try:
            # Use macOS afplay command (built-in)
            subprocess.run(['afplay', audio_path], check=True)
            logger.success("✅ Playback completed")
            return True
            
        except subprocess.CalledProcessError:
            logger.error("❌ Could not play audio file")
            return False
        except FileNotFoundError:
            logger.error("❌ Audio player not found (afplay)")
            return False
    
    async def transcribe_audio(self, audio_path: str) -> str:
        """
        Transcribe recorded audio
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        if not audio_path or not Path(audio_path).exists():
            return ""
        
        logger.info("🤖 Transcribing your speech...")
        
        try:
            text = await self.stt.transcribe_async(audio_path)
            return text.strip()
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return ""
    
    async def full_test(self, duration: float = 3.0, with_transcription: bool = True):
        """
        Run complete microphone test
        
        Args:
            duration: Recording duration
            with_transcription: Whether to include speech-to-text
        """
        logger.info("🧪 Starting complete microphone test")
        
        # Test 1: Record audio
        audio_path = await self.record_test(duration)
        
        if not audio_path:
            logger.error("❌ Recording failed - cannot continue")
            return
        
        # Test 2: Play back audio
        logger.info("\n" + "="*50)
        logger.info("🔊 PLAYBACK TEST - You should hear your voice:")
        logger.info("="*50)
        
        input("Press ENTER when ready to hear playback...")
        
        playback_success = self.play_audio(audio_path)
        
        if not playback_success:
            logger.warning("⚠️ Playback failed, but recording might still work")
        
        # Test 3: Transcription (optional)
        if with_transcription:
            logger.info("\n" + "="*50)
            logger.info("🤖 SPEECH RECOGNITION TEST:")
            logger.info("="*50)
            
            text = await self.transcribe_audio(audio_path)
            
            if text:
                logger.success(f"✅ Recognized: '{text}'")
                
                # Check for wake words
                wake_words = ["hey logic", "logic", "computer", "logik"]
                detected_wake_words = []
                
                text_lower = text.lower()
                for wake_word in wake_words:
                    if wake_word in text_lower:
                        detected_wake_words.append(wake_word)
                
                if detected_wake_words:
                    logger.success(f"🎯 Wake words detected: {detected_wake_words}")
                else:
                    logger.info("ℹ️ No wake words detected in this recording")
            else:
                logger.warning("⚠️ No speech recognized (audio might be too quiet or unclear)")
        
        # Cleanup
        try:
            Path(audio_path).unlink()
        except:
            pass
        
        # Test results summary
        logger.info("\n" + "="*50)
        logger.info("📋 TEST RESULTS SUMMARY:")
        logger.info("="*50)
        logger.success("✅ Recording: SUCCESS")
        
        if playback_success:
            logger.success("✅ Playback: SUCCESS")
        else:
            logger.warning("⚠️ Playback: FAILED (but recording works)")
        
        if with_transcription:
            if text:
                logger.success(f"✅ Speech Recognition: SUCCESS ('{text}')")
            else:
                logger.warning("⚠️ Speech Recognition: No speech detected")
        
        logger.info("="*50)
        
    async def cleanup(self):
        """Clean up resources"""
        if self.audio_capture:
            await self.audio_capture.stop()


@click.command()
@click.option(
    '--device',
    '-d',
    help='Audio input device name (leave empty for default)'
)
@click.option(
    '--duration',
    '-t',
    default=3.0,
    help='Recording duration in seconds (default: 3.0)'
)
@click.option(
    '--no-transcription',
    is_flag=True,
    help='Skip speech recognition test'
)
@click.option(
    '--list-devices',
    is_flag=True,
    help='List available audio devices'
)
def main(device, duration, no_transcription, list_devices):
    """
    Microphone Test Tool
    
    Test your microphone by recording and playing back audio.
    
    Examples:
        python microphone_test.py
        python microphone_test.py --duration 5
        python microphone_test.py --device "Built-in Microphone"
        python microphone_test.py --list-devices
    """
    
    # Setup logging
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Banner
    banner = """
    ╔══════════════════════════════════════════╗
    ║        🎤  MICROPHONE TEST  🎤           ║
    ║      Test your audio input system       ║
    ╚══════════════════════════════════════════╝
    """
    click.echo(click.style(banner, fg='cyan', bold=True))
    
    async def run_test():
        mic_test = MicrophoneTest(device_name=device)
        
        try:
            # List devices if requested
            if list_devices:
                mic_test.initialize()
                logger.info("📋 Available audio devices:")
                devices = mic_test.audio_capture.list_devices()
                for i, dev in enumerate(devices):
                    logger.info(f"  [{dev['index']}] {dev['name']} - {dev['channels']} channels")
                return
            
            # Initialize
            mic_test.initialize()
            
            # Run full test
            await mic_test.full_test(
                duration=duration,
                with_transcription=not no_transcription
            )
            
        except KeyboardInterrupt:
            logger.info("⏹️ Test interrupted by user")
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
        finally:
            await mic_test.cleanup()
    
    # Run the async test
    asyncio.run(run_test())


if __name__ == '__main__':
    main()
