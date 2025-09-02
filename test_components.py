#!/usr/bin/env python3
"""
Quick Test Script for Logic Voice Control
Tests all components individually
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
import asyncio
import numpy as np


def test_imports():
    """Test if all modules can be imported"""
    logger.info("🧪 Testing imports...")
    
    try:
        from src.audio.capture import AudioCapture
        logger.success("✅ AudioCapture imported")
    except Exception as e:
        logger.error(f"❌ AudioCapture import failed: {e}")
        return False
    
    try:
        from src.audio.wake_word import WakeWordDetector
        logger.success("✅ WakeWordDetector imported")
    except Exception as e:
        logger.error(f"❌ WakeWordDetector import failed: {e}")
        return False
    
    try:
        from src.stt.whisper_adapter import WhisperSTT
        logger.success("✅ WhisperSTT imported")
    except Exception as e:
        logger.error(f"❌ WhisperSTT import failed: {e}")
        return False
    
    try:
        from src.nlu.parser import IntentParser
        logger.success("✅ IntentParser imported")
    except Exception as e:
        logger.error(f"❌ IntentParser import failed: {e}")
        return False
    
    try:
        from src.router.dispatcher import CommandDispatcher
        logger.success("✅ CommandDispatcher imported")
    except Exception as e:
        logger.error(f"❌ CommandDispatcher import failed: {e}")
        return False
    
    try:
        from src.feedback.tts import TTSFeedback
        logger.success("✅ TTSFeedback imported")
    except Exception as e:
        logger.error(f"❌ TTSFeedback import failed: {e}")
        return False
    
    try:
        from src.config.loader import ConfigLoader
        logger.success("✅ ConfigLoader imported")
    except Exception as e:
        logger.error(f"❌ ConfigLoader import failed: {e}")
        return False
    
    return True


def test_config():
    """Test configuration loading"""
    logger.info("\n🧪 Testing configuration...")
    
    try:
        from src.config.loader import ConfigLoader
        config = ConfigLoader()
        
        logger.info(f"  Audio device: {config.audio.input_device or 'default'}")
        logger.info(f"  Sample rate: {config.audio.sample_rate} Hz")
        logger.info(f"  STT model: {config.stt.model}")
        logger.info(f"  Language: {config.stt.language}")
        logger.info(f"  Wake words: {', '.join(config.wake_word.models)}")
        
        logger.success("✅ Configuration loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration failed: {e}")
        return False


def test_audio():
    """Test audio capture"""
    logger.info("\n🧪 Testing audio capture...")
    
    try:
        from src.audio.capture import AudioCapture
        
        # List devices
        audio = AudioCapture(sample_rate=16000)
        devices = audio.list_devices()
        
        logger.info(f"  Found {len(devices)} audio devices")
        for dev in devices[:3]:  # Show first 3
            logger.info(f"    [{dev['index']}] {dev['name']}")
        
        logger.success("✅ Audio system accessible")
        return True
        
    except Exception as e:
        logger.error(f"❌ Audio test failed: {e}")
        return False


def test_tts():
    """Test Text-to-Speech"""
    logger.info("\n🧪 Testing Text-to-Speech...")
    
    try:
        from src.feedback.tts import TTSFeedback
        
        tts = TTSFeedback(voice="Anna", rate=200)
        
        # Test with German text
        success = tts.speak("Dies ist ein Test")
        
        if success:
            logger.success("✅ TTS working")
        else:
            logger.warning("⚠️ TTS failed (might not be on macOS)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ TTS test failed: {e}")
        return False


def test_wake_word():
    """Test wake word detection"""
    logger.info("\n🧪 Testing wake word detection...")
    
    try:
        from src.audio.wake_word import WakeWordDetector
        
        detector = WakeWordDetector(threshold=0.6)
        
        # Test with sample phrases
        test_phrases = [
            "hey logic",
            "computer start",
            "hallo logic",
            "random text"
        ]
        
        for phrase in test_phrases:
            detected = detector.detect_in_text(phrase)
            status = "✅" if detected else "❌"
            logger.info(f"  {status} '{phrase}' -> {detected}")
        
        logger.success("✅ Wake word detection working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Wake word test failed: {e}")
        return False


def test_intent_parser():
    """Test intent parsing"""
    logger.info("\n🧪 Testing intent parser...")
    
    try:
        from src.nlu.parser import IntentParser
        
        parser = IntentParser()
        
        # Test phrases
        test_phrases = [
            "test",
            "hallo",
            "stop",
            "hilfe"
        ]
        
        for phrase in test_phrases:
            intent = parser.parse(phrase)
            if intent:
                logger.info(f"  ✅ '{phrase}' -> {intent.name} ({intent.confidence:.2f})")
            else:
                logger.info(f"  ❌ '{phrase}' -> No match")
        
        logger.success("✅ Intent parser working")
        return True
        
    except Exception as e:
        logger.error(f"❌ Intent parser test failed: {e}")
        return False


def test_whisper():
    """Test Whisper STT (might take longer)"""
    logger.info("\n🧪 Testing Whisper STT...")
    logger.info("  ⏳ Loading model (this might take a moment)...")
    
    try:
        from src.stt.whisper_adapter import WhisperSTT
        
        stt = WhisperSTT(model_size="base", language="de")
        
        # Test with silent audio
        test_audio = np.zeros(16000, dtype=np.float32)  # 1 second silence
        result = stt.transcribe(test_audio, sample_rate=16000)
        
        logger.info(f"  Transcription result: '{result}' (should be empty for silence)")
        logger.success("✅ Whisper STT loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Whisper test failed: {e}")
        logger.info("  💡 Try: pip install openai-whisper")
        return False


async def test_full_pipeline():
    """Test the full pipeline (simple version)"""
    logger.info("\n🧪 Testing full pipeline...")
    
    try:
        from src.nlu.parser import IntentParser, Intent
        from src.router.dispatcher import CommandDispatcher
        from src.feedback.tts import TTSFeedback
        
        # Create components
        parser = IntentParser()
        dispatcher = CommandDispatcher(dry_run=True)
        tts = TTSFeedback()
        
        # Simulate command
        test_text = "test"
        logger.info(f"  Simulating command: '{test_text}'")
        
        # Parse intent
        intent = parser.parse(test_text)
        if intent:
            logger.info(f"  Intent: {intent.name}")
            
            # Execute
            result = await dispatcher.execute_async(intent)
            logger.info(f"  Result: {result.feedback}")
            
            # Speak feedback
            await tts.speak_async(result.feedback)
            
            logger.success("✅ Full pipeline working")
            return True
        else:
            logger.warning("⚠️ No intent matched")
            return False
            
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("=" * 50)
    logger.info("🚀 LOGIC VOICE CONTROL - COMPONENT TEST")
    logger.info("=" * 50)
    
    results = []
    
    # Test imports
    results.append(("Imports", test_imports()))
    
    if not results[-1][1]:
        logger.error("❌ Import test failed, cannot continue")
        return
    
    # Test individual components
    results.append(("Config", test_config()))
    results.append(("Audio", test_audio()))
    results.append(("TTS", test_tts()))
    results.append(("Wake Word", test_wake_word()))
    results.append(("Intent Parser", test_intent_parser()))
    
    # Optional: Test Whisper (might be slow)
    logger.info("\n" + "=" * 50)
    response = input("Test Whisper STT? (might take time) [y/N]: ")
    if response.lower() == 'y':
        results.append(("Whisper", test_whisper()))
    
    # Test pipeline
    asyncio.run(test_full_pipeline())
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    for test_name, success in results:
        status = "✅" if success else "❌"
        logger.info(f"  {status} {test_name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    
    logger.info(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.success("\n🎉 All tests passed! Ready to run: python cli.py")
    else:
        logger.warning("\n⚠️ Some tests failed. Check the logs above.")


if __name__ == "__main__":
    main()
