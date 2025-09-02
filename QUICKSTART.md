# Quick Start Guide - Logic Voice Control

## 🚀 Schnellstart

### 1. Installation (einmalig)
```bash
# Python 3.10+ installieren (falls noch nicht vorhanden)
brew install python@3.11

# Setup ausführen
chmod +x setup_with_python_check.sh
./setup_with_python_check.sh
```

### 2. Starten
```bash
# Start-Skript ausführbar machen
chmod +x start.sh

# Anwendung starten
./start.sh
```

### 3. Test-Modus Befehle

Im Test-Modus (ohne Logic Pro) funktionieren diese Befehle:

#### Wake Words (zum Aktivieren):
- "Hey Logic"
- "Hallo Logic"  
- "Computer"
- "Hi Logic"

#### Verfügbare Befehle:
- **"Test"** - Testet das System
- **"Hallo"** - Begrüßung
- **"Zeit"** oder **"Uhrzeit"** - Zeigt aktuelle Zeit
- **"Hilfe"** - Zeigt Hilfe
- **"Stop"** oder **"Beenden"** - Beendet das Programm

## 📝 Beispiel-Workflow

1. Starte die Anwendung im Test-Modus
2. Sage: **"Hey Logic"**
3. Warte auf: "Ja, ich höre"
4. Sage einen Befehl: **"Hallo"**
5. Erhalte Antwort: "Hallo! Wie kann ich helfen?"

## 🔧 Troubleshooting

### Audio-Geräte prüfen:
```bash
python -c "import pyaudio; p = pyaudio.PyAudio(); print([p.get_device_info_by_index(i)['name'] for i in range(p.get_device_count())])"
```

### Komponenten einzeln testen:
```bash
python test_components.py
```

### Verbose Mode für Debug:
```bash
python cli.py --dry-run --verbose
```

## 📊 Status

✅ **Implementiert:**
- Audio Capture (16kHz unified)
- Wake Word Detection  
- Speech-to-Text (Whisper)
- Intent Parser
- Command Dispatcher (Test Mode)
- Text-to-Speech (macOS)
- Config System

⏳ **TODO für Production:**
- Logic Pro Integration
- AppleScript Commands
- Key Commands
- Advanced NLU

## 🎯 Aktuelle Version: 0.0.1 (Test Mode)
