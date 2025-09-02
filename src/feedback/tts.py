#!/usr/bin/env python3
"""
Text-to-Speech Feedback Module
Uses macOS 'say' command for voice output
"""

import asyncio
import subprocess
from typing import Optional
import platform
from loguru import logger


class TTSFeedback:
    """Text-to-Speech feedback using macOS say command"""
    
    def __init__(
        self,
        voice: str = "Anna",  # German voice on macOS
        rate: int = 200,
        enabled: bool = True,
        volume: float = 0.8
    ):
        """
        Initialize TTS feedback
        
        Args:
            voice: macOS voice name
            rate: Speech rate in words per minute
            enabled: Whether TTS is enabled
            volume: Volume level (0.0-1.0)
        """
        self.voice = voice
        self.rate = rate
        self.enabled = enabled
        self.volume = volume
        
        # Check if we're on macOS
        self.is_macos = platform.system() == "Darwin"
        
        if not self.is_macos:
            logger.warning("⚠️ TTS only supported on macOS, disabling")
            self.enabled = False
        
        if self.enabled:
            logger.info(f"🔊 TTS initialized (voice: {voice}, rate: {rate})")
        else:
            logger.info("🔇 TTS disabled")
    
    def speak(self, text: str) -> bool:
        """
        Speak text using macOS say command
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        if not self.enabled or not text:
            return False
        
        try:
            # Build say command
            cmd = ["say"]
            
            # Add voice if specified
            if self.voice:
                cmd.extend(["-v", self.voice])
            
            # Add rate if specified
            if self.rate:
                cmd.extend(["-r", str(self.rate)])
            
            # Add text
            cmd.append(text)
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.debug(f"🔊 Spoke: '{text}'")
                return True
            else:
                logger.warning(f"⚠️ Say command failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ TTS timeout")
            return False
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            return False
    
    async def speak_async(self, text: str) -> bool:
        """
        Async version of speak
        
        Args:
            text: Text to speak
            
        Returns:
            True if successful
        """
        if not self.enabled or not text:
            return False
        
        try:
            # Build say command
            cmd = ["say"]
            
            if self.voice:
                cmd.extend(["-v", self.voice])
            
            if self.rate:
                cmd.extend(["-r", str(self.rate)])
            
            cmd.append(text)
            
            # Execute asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                await asyncio.wait_for(process.wait(), timeout=10)
                
                if process.returncode == 0:
                    logger.debug(f"🔊 Spoke async: '{text}'")
                    return True
                else:
                    logger.warning("⚠️ Say command failed")
                    return False
                    
            except asyncio.TimeoutError:
                process.kill()
                logger.warning("⚠️ TTS timeout")
                return False
                
        except Exception as e:
            logger.error(f"❌ TTS async error: {e}")
            return False
    
    def list_voices(self) -> list:
        """List available macOS voices"""
        if not self.is_macos:
            return []
        
        try:
            result = subprocess.run(
                ["say", "-v", "?"],
                capture_output=True,
                text=True
            )
            
            voices = []
            for line in result.stdout.splitlines():
                if line:
                    # Parse voice info
                    parts = line.split()
                    if len(parts) >= 2:
                        voice_name = parts[0]
                        language = parts[1] if len(parts) > 1 else ""
                        voices.append({
                            "name": voice_name,
                            "language": language
                        })
            
            return voices
            
        except Exception as e:
            logger.error(f"❌ Failed to list voices: {e}")
            return []
    
    def test_voice(self, text: str = None):
        """Test TTS with sample text"""
        if text is None:
            text = "Hallo, dies ist ein Test der Sprachausgabe."
        
        logger.info(f"🧪 Testing TTS: '{text}'")
        return self.speak(text)


# Test functions
if __name__ == "__main__":
    # Test TTS
    import asyncio
    
    logger.info("🧪 Testing Text-to-Speech...")
    
    tts = TTSFeedback(voice="Anna", rate=180)
    
    # List available voices
    voices = tts.list_voices()
    logger.info(f"📝 Available voices: {len(voices)}")
    for v in voices[:5]:  # Show first 5
        logger.info(f"  - {v['name']} ({v['language']})")
    
    # Test sync speech
    tts.test_voice()
    
    # Test async speech
    async def test_async():
        await tts.speak_async("Dies ist ein asynchroner Test.")
    
    asyncio.run(test_async())
    
    logger.success("✅ TTS test completed")
