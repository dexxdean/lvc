#!/usr/bin/env python3
"""
TTS Test - Test the Text-to-Speech system
"""

import sys
from pathlib import Path
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.feedback.tts import TTSFeedback
from loguru import logger
import asyncio

async def test_tts_system():
    """Test the TTS system thoroughly"""
    
    logger.info("🧪 Testing TTS System")
    print("\n" + "="*50)
    print("🗣️  TTS SYSTEM TEST")
    print("="*50)
    
    # Test 1: Direct macOS say command
    print("\n1. Testing direct macOS 'say' command:")
    try:
        result = subprocess.run(['say', 'Hello from macOS say command'], 
                               capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Direct 'say' command works")
        else:
            print(f"❌ Direct 'say' command failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Direct 'say' command error: {e}")
    
    # Test 2: TTSFeedback class
    print("\n2. Testing TTSFeedback class:")
    tts = TTSFeedback()
    
    # Test synchronous speech
    print("   Testing sync speech...")
    success = tts.speak("Hallo, das ist ein Test")
    if success:
        print("✅ Sync TTS works")
    else:
        print("❌ Sync TTS failed")
    
    # Test asynchronous speech
    print("   Testing async speech...")
    success = await tts.speak_async("Das ist ein asynchroner Test")
    if success:
        print("✅ Async TTS works")
    else:
        print("❌ Async TTS failed")
    
    # Test 3: The specific phrase from the main system
    print("\n3. Testing wake word response phrase:")
    success = await tts.speak_async("Ja, ich höre")
    if success:
        print("✅ Wake word response works")
    else:
        print("❌ Wake word response failed")
    
    # Test 4: List available voices
    print("\n4. Available voices:")
    voices = tts.list_voices()
    if voices:
        print(f"   Found {len(voices)} voices:")
        for voice in voices[:5]:  # Show first 5
            print(f"   - {voice}")
    else:
        print("   No voices found")
    
    print("\n" + "="*50)
    print("TTS Test completed")
    print("="*50)

if __name__ == '__main__':
    asyncio.run(test_tts_system())
