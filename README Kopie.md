# Logic Voice Control 🎙️

Voice control system for Logic Pro with accessibility focus. Control your DAW hands-free with natural language commands.

## 🎯 Features

- **Wake Word Detection**: "Hey Logic", "Hallo Logic", "Hi Logic"
- **Natural Language Processing**: Speak naturally or use short commands
- **Low Latency**: < 500ms response time
- **Offline Operation**: No cloud dependencies
- **Accessibility First**: Full VoiceOver compatibility

## 🛠️ Requirements

- macOS 15.6.1 or later (Apple Silicon optimized)
- Logic Pro 11.2.2 or later
- Python 3.10+
- PreSonus Quantum 2 (or compatible audio interface)

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/logic-voice-control.git
cd logic-voice-control
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Download Whisper model (first run only)
```bash
python -c "import whisper; whisper.load_model('small')"
```

### 5. Configure audio interface
Edit `configs/audio.yml` to match your setup:
```yaml
input_device: "PreSonus Quantum 2"
channel: 1
sample_rate: 48000
bit_depth: 24
```

## 🚀 Usage

### Basic usage
```bash
python cli.py
```

### With options
```bash
# Low latency mode
python cli.py --low-latency

# Dry run (no actions executed)
python cli.py --dry-run

# Custom config
python cli.py --config configs/custom.yml

# Verbose logging
python cli.py --verbose
```

## 🗣️ Available Commands

### Transport Controls
- "Play" / "Wiedergabe"
- "Stop"
- "Record" / "Aufnahme"
- "Rewind" / "Zurück"
- "Forward" / "Vor"
- "Loop an/aus"

### Track Operations
- "Spur [Nummer] wählen"
- "Spur [Nummer] stumm"
- "Spur [Nummer] solo"
- "Lautstärke hoch/runter"

### Markers
- "Marker setzen"
- "Zum nächsten Marker"
- "Zum vorigen Marker"

### System
- "Rückgängig" / "Undo"
- "Metronom an/aus"
- "Zähler an/aus"

## 🧪 Testing

```bash
# Run all tests
pytest

# Unit tests only
pytest tests/unit/

# With coverage
pytest --cov=src --cov-report=html

# Dry run mode for testing without Logic Pro
python cli.py --dry-run
```

## 📁 Project Structure

```
logic-voice-control/
├── src/
│   ├── audio/         # Audio capture & wake word
│   ├── stt/          # Speech-to-text
│   ├── nlu/          # Natural language understanding
│   ├── router/       # Command routing
│   ├── actions/      # Logic Pro actions
│   ├── integrations/ # System integration
│   ├── feedback/     # TTS & audio feedback
│   └── config/       # Configuration management
├── configs/          # YAML configurations
├── tests/           # Test suites
└── cli.py          # Main entry point
```

## ⚙️ Configuration

### commands.yml
Define custom commands and their actions:
```yaml
commands:
  - intent: "custom_command"
    patterns: ["mein befehl", "custom action"]
    action:
      type: "key_command"
      value: "Cmd+Shift+A"
    feedback: "Befehl ausgeführt"
```

### audio.yml
Configure audio hardware:
```yaml
wake_word:
  models: ["hey_logic", "hallo_logic", "hi_logic"]
  threshold: 0.8
  
vad:
  aggressiveness: 2  # 0-3, higher = more aggressive
  
buffer:
  size: 256  # samples
  channels: 1
```

## 🐛 Troubleshooting

### Audio Issues
- Check interface in Audio MIDI Setup
- Verify sample rate matches (48kHz)
- Test with `python -m src.audio.test_capture`

### Wake Word Not Detected
- Increase microphone gain
- Reduce `wake_word.threshold` in config
- Train custom model with your voice

### High Latency
- Use `--low-latency` flag
- Reduce buffer size in audio.yml
- Close other audio applications

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 🔗 Links

- [Logic Pro Scripting Guide](https://help.apple.com/logicpro-scripting-guide/)
- [Whisper Documentation](https://github.com/openai/whisper)
- [OpenWakeWord](https://github.com/dscripka/openwakeword)

## ✨ Acknowledgments

Developed with accessibility in mind for the Logic Pro community.

---

**Version:** 0.0.1 (MVP)  
**Status:** In Development  
**Author:** Petar Nikolic
