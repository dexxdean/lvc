#!/usr/bin/env python3
"""
Configuration Loader
Loads and manages application configuration
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import yaml
import json

from loguru import logger


@dataclass
class AudioConfig:
    """Audio configuration"""
    input_device: Optional[str] = None
    sample_rate: int = 16000
    channels: int = 1
    buffer_size: int = 256


@dataclass
class WakeWordConfig:
    """Wake word detection configuration"""
    models: List[str] = field(default_factory=lambda: ["hey logic", "logic", "computer"])
    threshold: float = 0.8


@dataclass
class STTConfig:
    """Speech-to-Text configuration"""
    model: str = "small"
    language: str = "de"
    device: Optional[str] = None


@dataclass
class FeedbackConfig:
    """Text-to-Speech feedback configuration"""
    voice: str = "default"
    rate: int = 200
    enabled: bool = True


@dataclass
class LogicProConfig:
    """Logic Pro integration configuration"""
    enabled: bool = True
    app_name: str = "Logic Pro"
    check_running: bool = True


@dataclass
class CommandsConfig:
    """Commands configuration"""
    timeout: float = 5.0
    confirmation: bool = False
    custom_commands: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AppConfig:
    """Main application configuration"""
    audio: AudioConfig = field(default_factory=AudioConfig)
    wake_word: WakeWordConfig = field(default_factory=WakeWordConfig)
    stt: STTConfig = field(default_factory=STTConfig)
    feedback: FeedbackConfig = field(default_factory=FeedbackConfig)
    logic_pro: LogicProConfig = field(default_factory=LogicProConfig)
    commands: CommandsConfig = field(default_factory=CommandsConfig)
    
    # Global settings
    debug: bool = False
    dry_run: bool = False
    log_level: str = "INFO"


class ConfigLoader:
    """Configuration loader and manager"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration loader
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        self.config = AppConfig()
        
        # Load configuration
        self._load_config()
        self._load_env_overrides()
        
        logger.info(f"⚙️ Configuration loaded")
        logger.debug(f"🔧 STT Model: {self.config.stt.model}")
        logger.debug(f"🌐 Language: {self.config.stt.language}")
        logger.debug(f"🎤 Audio Device: {self.config.audio.input_device or 'default'}")
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path and self.config_path.exists():
            logger.info(f"📋 Loading config from: {self.config_path}")
            
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() == '.json':
                        config_data = json.load(f)
                    else:
                        config_data = yaml.safe_load(f)
                
                self._apply_config_data(config_data)
                logger.success("✅ Configuration file loaded")
                
            except Exception as e:
                logger.error(f"❌ Failed to load config file: {e}")
                logger.info("🔄 Using default configuration")
        else:
            logger.info("📋 Using default configuration")
            
            # Try to find default config files
            self._try_load_default_configs()
    
    def _try_load_default_configs(self):
        """Try to load from default config locations"""
        default_paths = [
            Path("config.yml"),
            Path("config.yaml"),
            Path("configs/config.yml"),
            Path("configs/default.yml"),
        ]
        
        for path in default_paths:
            if path.exists():
                logger.info(f"📋 Found default config: {path}")
                self.config_path = path
                self._load_config()
                break
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to config object"""
        
        # Audio configuration
        if 'audio' in config_data:
            audio_data = config_data['audio']
            self.config.audio.input_device = audio_data.get('input_device', self.config.audio.input_device)
            self.config.audio.sample_rate = audio_data.get('sample_rate', self.config.audio.sample_rate)
            self.config.audio.channels = audio_data.get('channels', self.config.audio.channels)
            self.config.audio.buffer_size = audio_data.get('buffer_size', self.config.audio.buffer_size)
        
        # Wake word configuration
        if 'wake_word' in config_data:
            wake_data = config_data['wake_word']
            self.config.wake_word.models = wake_data.get('models', self.config.wake_word.models)
            self.config.wake_word.threshold = wake_data.get('threshold', self.config.wake_word.threshold)
        
        # STT configuration
        if 'stt' in config_data:
            stt_data = config_data['stt']
            self.config.stt.model = stt_data.get('model', self.config.stt.model)
            self.config.stt.language = stt_data.get('language', self.config.stt.language)
            self.config.stt.device = stt_data.get('device', self.config.stt.device)
        
        # Feedback configuration
        if 'feedback' in config_data:
            feedback_data = config_data['feedback']
            self.config.feedback.voice = feedback_data.get('voice', self.config.feedback.voice)
            self.config.feedback.rate = feedback_data.get('rate', self.config.feedback.rate)
            self.config.feedback.enabled = feedback_data.get('enabled', self.config.feedback.enabled)
        
        # Logic Pro configuration
        if 'logic_pro' in config_data:
            logic_data = config_data['logic_pro']
            self.config.logic_pro.enabled = logic_data.get('enabled', self.config.logic_pro.enabled)
            self.config.logic_pro.app_name = logic_data.get('app_name', self.config.logic_pro.app_name)
            self.config.logic_pro.check_running = logic_data.get('check_running', self.config.logic_pro.check_running)
        
        # Commands configuration
        if 'commands' in config_data:
            cmd_data = config_data['commands']
            self.config.commands.timeout = cmd_data.get('timeout', self.config.commands.timeout)
            self.config.commands.confirmation = cmd_data.get('confirmation', self.config.commands.confirmation)
            # Store all command data for parser
            self.config.commands.custom_commands = cmd_data
        
        # System/Global settings
        if 'system' in config_data:
            sys_data = config_data['system']
            self.config.debug = sys_data.get('debug', self.config.debug)
            self.config.dry_run = sys_data.get('dry_run', self.config.dry_run)
            self.config.log_level = sys_data.get('log_level', self.config.log_level)
        else:
            # Fallback to root level
            self.config.debug = config_data.get('debug', self.config.debug)
            self.config.dry_run = config_data.get('dry_run', self.config.dry_run)
            self.config.log_level = config_data.get('log_level', self.config.log_level)
    
    def _load_env_overrides(self):
        """Load environment variable overrides"""
        
        # Audio device override
        if os.getenv('AUDIO_DEVICE'):
            self.config.audio.input_device = os.getenv('AUDIO_DEVICE')
            logger.debug(f"🔧 Audio device override: {self.config.audio.input_device}")
        
        # STT language override
        if os.getenv('STT_LANGUAGE'):
            self.config.stt.language = os.getenv('STT_LANGUAGE')
            logger.debug(f"🌐 Language override: {self.config.stt.language}")
        
        # STT model override
        if os.getenv('STT_MODEL'):
            self.config.stt.model = os.getenv('STT_MODEL')
            logger.debug(f"🤖 Model override: {self.config.stt.model}")
        
        # Sample rate override
        if os.getenv('AUDIO_SAMPLE_RATE'):
            try:
                self.config.audio.sample_rate = int(os.getenv('AUDIO_SAMPLE_RATE'))
                logger.debug(f"🎵 Sample rate override: {self.config.audio.sample_rate}")
            except ValueError:
                logger.warning(f"⚠️ Invalid sample rate in AUDIO_SAMPLE_RATE: {os.getenv('AUDIO_SAMPLE_RATE')}")
        
        # Debug mode override
        if os.getenv('DEBUG_MODE', '').lower() in ('true', '1', 'yes'):
            self.config.debug = True
            logger.debug("🐛 Debug mode enabled via environment")
        
        # Dry run override
        if os.getenv('DRY_RUN', '').lower() in ('true', '1', 'yes'):
            self.config.dry_run = True
            logger.debug("🧪 Dry run mode enabled via environment")
        
        # Log level override
        if os.getenv('LOG_LEVEL'):
            self.config.log_level = os.getenv('LOG_LEVEL').upper()
            logger.debug(f"📝 Log level override: {self.config.log_level}")
    
    def save_config(self, path: Optional[Path] = None):
        """Save current configuration to file"""
        save_path = path or self.config_path or Path("config.yml")
        
        config_dict = {
            'audio': {
                'input_device': self.config.audio.input_device,
                'sample_rate': self.config.audio.sample_rate,
                'channels': self.config.audio.channels,
                'buffer_size': self.config.audio.buffer_size,
            },
            'wake_word': {
                'models': self.config.wake_word.models,
                'threshold': self.config.wake_word.threshold,
            },
            'stt': {
                'model': self.config.stt.model,
                'language': self.config.stt.language,
                'device': self.config.stt.device,
            },
            'feedback': {
                'voice': self.config.feedback.voice,
                'rate': self.config.feedback.rate,
                'enabled': self.config.feedback.enabled,
            },
            'logic_pro': {
                'enabled': self.config.logic_pro.enabled,
                'app_name': self.config.logic_pro.app_name,
                'check_running': self.config.logic_pro.check_running,
            },
            'commands': {
                'timeout': self.config.commands.timeout,
                'confirmation': self.config.commands.confirmation,
                'custom_commands': self.config.commands.custom_commands,
            },
            'debug': self.config.debug,
            'dry_run': self.config.dry_run,
            'log_level': self.config.log_level,
        }
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
            
            logger.success(f"✅ Configuration saved to: {save_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save configuration: {e}")
    
    def get_config_summary(self) -> str:
        """Get human-readable configuration summary"""
        lines = [
            "📋 Configuration Summary",
            "=" * 30,
            f"🎤 Audio Device: {self.config.audio.input_device or 'Default'}",
            f"🔊 Sample Rate: {self.config.audio.sample_rate} Hz",
            f"🤖 STT Model: {self.config.stt.model}",
            f"🌐 Language: {self.config.stt.language}",
            f"🎯 Wake Words: {', '.join(self.config.wake_word.models)}",
            f"🎚️ Wake Threshold: {self.config.wake_word.threshold}",
            f"💬 TTS Enabled: {self.config.feedback.enabled}",
            f"🎮 Logic Pro: {'Enabled' if self.config.logic_pro.enabled else 'Disabled'}",
            f"🐛 Debug Mode: {self.config.debug}",
            f"🧪 Dry Run: {self.config.dry_run}",
        ]
        
        return "\n".join(lines)
    
    # Property accessors for easier access
    @property
    def audio(self) -> AudioConfig:
        return self.config.audio
    
    @property
    def wake_word(self) -> WakeWordConfig:
        return self.config.wake_word
    
    @property
    def stt(self) -> STTConfig:
        return self.config.stt
    
    @property
    def feedback(self) -> FeedbackConfig:
        return self.config.feedback
    
    @property
    def logic_pro(self) -> LogicProConfig:
        return self.config.logic_pro
    
    @property
    def commands(self) -> CommandsConfig:
        return self.config.commands


if __name__ == "__main__":
    # Test configuration loader
    logger.info("🧪 Testing Configuration Loader...")
    
    config = ConfigLoader()
    
    # Print summary
    print(config.get_config_summary())
    
    # Test saving
    config.save_config(Path("test_config.yml"))
    
    logger.success("✅ Configuration loader test completed")
