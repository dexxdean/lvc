#!/usr/bin/env python3
"""
Logic Voice Control - Main CLI Entry Point
Voice control system for Logic Pro with accessibility focus
"""

import sys
import signal
import asyncio
from pathlib import Path
from typing import Optional
import time

import click
import numpy as np
from loguru import logger
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.audio.capture import AudioCapture
from src.audio.wake_word import WakeWordDetector
from src.stt.whisper_adapter import WhisperSTT
from src.nlu.parser import IntentParser
from src.router.dispatcher import CommandDispatcher
from src.feedback.tts import TTSFeedback
from src.config.loader import ConfigLoader


class LogicVoiceControl:
    """Main application controller"""
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        dry_run: bool = False,
        low_latency: bool = False,
        verbose: bool = False
    ):
        """Initialize the voice control system"""
        self.dry_run = dry_run
        self.low_latency = low_latency
        self.running = False
        self.verbose = verbose
        
        # Setup logging
        log_level = "DEBUG" if verbose else "INFO"
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=log_level
        )
        
        # Log to file as well
        Path("logs").mkdir(exist_ok=True)
        logger.add(
            "logs/logic_voice_{time}.log",
            rotation="1 day",
            retention="7 days",
            level="DEBUG"
        )
        
        logger.info("🎙️ Logic Voice Control starting...")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        logger.info(f"Latency: {'LOW' if low_latency else 'NORMAL'}")
        
        # Load configuration
        self.config = ConfigLoader(config_path)
        
        # Initialize components
        self._init_components()
        
    def _init_components(self):
        """Initialize all system components"""
        try:
            # Audio capture - unified to 16kHz
            buffer_size = 128 if self.low_latency else 512
            self.audio_capture = AudioCapture(
                device_name=self.config.audio.input_device,
                sample_rate=16000,  # Force 16kHz for Whisper compatibility
                channels=self.config.audio.channels,
                buffer_size=buffer_size
            )
            
            # Wake word detector
            self.wake_word = WakeWordDetector(
                models=self.config.wake_word.models,
                threshold=self.config.wake_word.threshold
            )
            
            # Speech-to-text
            logger.info(f"📊 Loading Whisper model: {self.config.stt.model}")
            self.stt = WhisperSTT(
                model_size=self.config.stt.model,
                language=self.config.stt.language
            )
            
            # Intent parser with commands from config
            self.intent_parser = IntentParser(
                commands_config=self.config.commands.custom_commands
            )
            
            # Command dispatcher
            self.dispatcher = CommandDispatcher(
                dry_run=self.dry_run
            )
            
            # Feedback system
            self.tts = TTSFeedback(
                voice=self.config.feedback.voice,
                rate=self.config.feedback.rate
            )
            
            logger.success("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            sys.exit(1)
    
    async def run(self):
        """Main application loop with efficient wake word detection"""
        self.running = True
        
        # Start audio stream
        self.audio_capture.start_stream()
        
        logger.info("=" * 50)
        logger.info("👂 LISTENING FOR WAKE WORD")
        logger.info("💡 Say loudly and clearly:")
        logger.info("   • 'Computer'")
        logger.info("   • 'Hey Logic'")  
        logger.info("   • 'Hallo Logic'")
        logger.info("=" * 50)
        logger.info("")
        
        # Audio processing parameters
        energy_threshold = 0.02  # Increased threshold - need louder audio
        check_interval = 1.0  # Check less frequently (every 1 second)
        last_check_time = 0
        audio_buffer = []
        checks_count = 0
        
        try:
            while self.running:
                # Get audio chunk
                audio_chunk = await self.audio_capture.capture_async(timeout=0.1)
                
                if audio_chunk is None or len(audio_chunk) == 0:
                    await asyncio.sleep(0.01)
                    continue
                
                # Add to buffer
                audio_buffer.append(audio_chunk)
                
                # Keep buffer size manageable (last 2 seconds)
                max_buffer_chunks = int(2.0 * 16000 / self.audio_capture.buffer_size)
                if len(audio_buffer) > max_buffer_chunks:
                    audio_buffer.pop(0)
                
                # Check if enough time has passed for wake word check
                current_time = time.time()
                if current_time - last_check_time < check_interval:
                    continue
                
                last_check_time = current_time
                
                # Combine buffer for analysis
                if len(audio_buffer) < 4:  # Need at least 0.25 seconds
                    continue
                    
                combined_audio = np.concatenate(audio_buffer[-8:])  # Last 0.5 seconds
                
                # Check audio energy (efficiency optimization)
                audio_energy = np.sqrt(np.mean(combined_audio ** 2))
                
                # Show periodic status
                checks_count += 1
                if checks_count % 10 == 0:  # Every 10 seconds
                    logger.info(f"⏳ Still listening... (checked {checks_count} times)")
                
                if audio_energy < energy_threshold:
                    if self.verbose:
                        logger.debug(f"🔇 Too quiet (energy: {audio_energy:.4f} < {energy_threshold})")
                    continue  # Too quiet, skip processing
                
                # Show activity indicator
                logger.info(f"🎤 Audio detected (energy: {audio_energy:.4f}) - checking for wake word...")
                
                # Check for wake word (only when there's sufficient audio energy)
                # Transcribe the audio
                text = self.stt.transcribe(combined_audio, sample_rate=16000)
                
                if text:
                    logger.info(f"📝 Heard: '{text}'")
                    
                    # Check if wake word is in the transcription
                    if self.wake_word.detect_in_text(text):
                        logger.success("=" * 50)
                        logger.success("🎯 WAKE WORD DETECTED!")
                        logger.success("=" * 50)
                        
                        # Clear buffer after wake word
                        audio_buffer.clear()
                        
                        # Provide feedback
                        await self.tts.speak_async("Ja, ich höre")
                        
                        # Capture command
                        logger.info("🎤 Listening for command...")
                        logger.info("💬 Available commands: Test, Hallo, Zeit, Hilfe, Stop")
                        
                        command_audio = await self.audio_capture.capture_command(
                            max_duration=5.0,
                            silence_timeout=1.5
                        )
                        
                        if len(command_audio) > 0:
                            # Transcribe command
                            command_text = self.stt.transcribe(command_audio, sample_rate=16000)
                            
                            if command_text:
                                logger.info(f"📝 Command: '{command_text}'")
                                
                                # Parse intent
                                intent = self.intent_parser.parse(command_text)
                                
                                if intent:
                                    logger.info(f"🎯 Intent: {intent.name} ({intent.confidence:.2f})")
                                    
                                    # Execute command
                                    result = await self.dispatcher.execute_async(intent)
                                    
                                    # Provide feedback
                                    if result.success:
                                        await self.tts.speak_async(result.feedback)
                                        logger.success(f"✅ {result.feedback}")
                                        
                                        # Check for exit command
                                        if intent.action == "exit":
                                            logger.info("👋 Exit command received, shutting down...")
                                            self.running = False
                                    else:
                                        await self.tts.speak_async(f"Fehler: {result.error}")
                                        logger.error(f"❌ {result.error}")
                                else:
                                    await self.tts.speak_async("Befehl nicht verstanden")
                                    logger.warning("⚠️ No intent matched")
                            else:
                                await self.tts.speak_async("Nichts gehört")
                                logger.warning("⚠️ No command transcribed")
                        else:
                            logger.warning("⚠️ No command audio captured")
                        
                        # Reset for next wake word
                        logger.info("")
                        logger.info("=" * 50)
                        logger.info("👂 Listening for wake word again...")
                        logger.info("=" * 50)
                        checks_count = 0
                    else:
                        if self.verbose:
                            logger.debug(f"❌ No wake word in: '{text}'")
                
                # Small delay
                await asyncio.sleep(0.01)
                
        except KeyboardInterrupt:
            logger.info("⏹️ Stopping...")
        except Exception as e:
            logger.error(f"❌ Runtime error: {e}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        self.running = False
        self.audio_capture.stop_stream()
        await self.audio_capture.stop()
        logger.info("👋 Logic Voice Control stopped")
    
    def handle_signal(self, signum, frame):
        """Handle system signals"""
        logger.info(f"📡 Received signal {signum}")
        self.running = False


@click.command()
@click.option(
    '--config',
    '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Path to configuration file'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Run without executing actual commands (testing mode)'
)
@click.option(
    '--low-latency',
    is_flag=True,
    help='Use low-latency settings (may increase CPU usage)'
)
@click.option(
    '--verbose',
    '-v',
    is_flag=True,
    help='Enable verbose logging'
)
@click.version_option(version='0.0.1')
def main(config, dry_run, low_latency, verbose):
    """
    Logic Voice Control - Control Logic Pro with your voice
    
    Examples:
        python cli.py
        python cli.py --dry-run --verbose
        python cli.py --low-latency
        python cli.py --config config.yml
    """
    # Load environment variables
    load_dotenv()
    
    # ASCII Art Banner
    banner = """
    ╔══════════════════════════════════════════╗
    ║     🎙️  LOGIC VOICE CONTROL  🎙️         ║
    ║     Control Logic Pro with your voice    ║
    ╚══════════════════════════════════════════╝
    """
    click.echo(click.style(banner, fg='cyan', bold=True))
    
    # Create application instance
    app = LogicVoiceControl(
        config_path=config,
        dry_run=dry_run,
        low_latency=low_latency,
        verbose=verbose
    )
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, app.handle_signal)
    signal.signal(signal.SIGTERM, app.handle_signal)
    
    # Run the application
    try:
        asyncio.run(app.run())
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
