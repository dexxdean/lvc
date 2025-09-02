#!/usr/bin/env python3
"""
Command Dispatcher Module
Executes recognized commands and returns results
"""

import asyncio
import subprocess
from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    feedback: str
    error: Optional[str] = None
    data: Optional[Any] = None


class CommandDispatcher:
    """Dispatches and executes recognized commands"""
    
    def __init__(self, dry_run: bool = True):
        """
        Initialize command dispatcher
        
        Args:
            dry_run: If True, only log commands without executing
        """
        self.dry_run = dry_run
        self.command_history = []
        
        logger.info(f"🎮 Command dispatcher initialized (dry_run: {dry_run})")
    
    def execute(self, intent) -> CommandResult:
        """
        Execute a command based on intent
        
        Args:
            intent: Intent object with command details
            
        Returns:
            CommandResult with execution status
        """
        if not intent:
            return CommandResult(
                success=False,
                feedback="Kein Befehl erkannt",
                error="No intent provided"
            )
        
        # Log command
        self.command_history.append({
            'time': datetime.now(),
            'intent': intent.name,
            'text': intent.text
        })
        
        logger.info(f"🚀 Executing: {intent.name}")
        
        # Handle different action types
        action = intent.action
        
        if isinstance(action, str):
            # Simple string action
            return self._execute_simple_action(action, intent)
        elif isinstance(action, dict):
            # Complex action with type and value
            return self._execute_complex_action(action, intent)
        else:
            # Default log action
            return self._execute_log_action(intent)
    
    async def execute_async(self, intent) -> CommandResult:
        """Async version of execute"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, intent)
    
    def _execute_simple_action(self, action: str, intent) -> CommandResult:
        """Execute simple string action"""
        
        if action == "log":
            # Just log the command
            logger.info(f"📝 Command logged: {intent.name}")
            return CommandResult(
                success=True,
                feedback=intent.feedback or f"Befehl {intent.name} ausgeführt"
            )
        
        elif action == "exit":
            # Exit command
            logger.info("👋 Exit command received")
            return CommandResult(
                success=True,
                feedback=intent.feedback or "Auf Wiedersehen"
            )
        
        elif action == "help":
            # Help command
            help_text = self._get_help_text()
            return CommandResult(
                success=True,
                feedback=help_text
            )
        
        elif action == "time":
            # Get current time
            current_time = datetime.now().strftime("%H:%M Uhr")
            feedback = intent.feedback.replace("{time}", current_time) if intent.feedback else f"Es ist {current_time}"
            return CommandResult(
                success=True,
                feedback=feedback,
                data={'time': current_time}
            )
        
        else:
            # Unknown action
            logger.warning(f"⚠️ Unknown action: {action}")
            return CommandResult(
                success=False,
                feedback="Unbekannte Aktion",
                error=f"Unknown action: {action}"
            )
    
    def _execute_complex_action(self, action: dict, intent) -> CommandResult:
        """Execute complex action with type and parameters"""
        
        action_type = action.get('type')
        
        if action_type == "key_command":
            # Keyboard command
            if self.dry_run:
                logger.info(f"🎹 [DRY RUN] Would send key: {action.get('value')}")
                return CommandResult(
                    success=True,
                    feedback=f"[TEST] {intent.feedback or 'Tastenkombination gesendet'}"
                )
            else:
                # In production, would use pyautogui
                return self._send_key_command(action.get('value'), intent)
        
        elif action_type == "applescript":
            # AppleScript command
            if self.dry_run:
                logger.info(f"📜 [DRY RUN] Would run AppleScript")
                return CommandResult(
                    success=True,
                    feedback=f"[TEST] {intent.feedback or 'AppleScript ausgeführt'}"
                )
            else:
                # In production, would execute AppleScript
                return self._run_applescript(action.get('value'), intent)
        
        else:
            logger.warning(f"⚠️ Unknown action type: {action_type}")
            return CommandResult(
                success=False,
                feedback="Unbekannter Aktionstyp",
                error=f"Unknown action type: {action_type}"
            )
    
    def _execute_log_action(self, intent) -> CommandResult:
        """Default action - just log"""
        logger.info(f"📝 Default action for: {intent.name}")
        return CommandResult(
            success=True,
            feedback=intent.feedback or f"Befehl {intent.name} erkannt"
        )
    
    def _send_key_command(self, keys: str, intent) -> CommandResult:
        """Send keyboard command (production only)"""
        try:
            import pyautogui
            
            # Parse key combination
            keys = keys.replace("Cmd", "command")
            keys = keys.replace("Shift", "shift")
            keys = keys.replace("Space", "space")
            
            # Send keys
            pyautogui.hotkey(*keys.split("+"))
            
            logger.success(f"✅ Sent keys: {keys}")
            return CommandResult(
                success=True,
                feedback=intent.feedback or "Tastenkombination gesendet"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to send keys: {e}")
            return CommandResult(
                success=False,
                feedback="Fehler beim Senden der Tastenkombination",
                error=str(e)
            )
    
    def _run_applescript(self, script: str, intent) -> CommandResult:
        """Run AppleScript (production only)"""
        try:
            # Execute AppleScript
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                logger.success("✅ AppleScript executed successfully")
                return CommandResult(
                    success=True,
                    feedback=intent.feedback or "AppleScript ausgeführt"
                )
            else:
                logger.error(f"❌ AppleScript failed: {result.stderr}")
                return CommandResult(
                    success=False,
                    feedback="AppleScript Fehler",
                    error=result.stderr
                )
                
        except Exception as e:
            logger.error(f"❌ Failed to run AppleScript: {e}")
            return CommandResult(
                success=False,
                feedback="Fehler beim Ausführen von AppleScript",
                error=str(e)
            )
    
    def _get_help_text(self) -> str:
        """Get help text"""
        return (
            "Verfügbare Befehle im Test-Modus:\n"
            "• Test - Testet das System\n"
            "• Hallo - Begrüßung\n"
            "• Zeit/Uhrzeit - Aktuelle Zeit\n"
            "• Hilfe - Diese Hilfe\n"
            "• Stop/Beenden - Programm beenden"
        )
    
    def get_history(self) -> list:
        """Get command history"""
        return self.command_history.copy()
    
    def clear_history(self):
        """Clear command history"""
        self.command_history.clear()
        logger.info("📜 Command history cleared")


# Test functions
if __name__ == "__main__":
    logger.info("🧪 Testing Command Dispatcher...")
    
    from src.nlu.parser import Intent
    
    dispatcher = CommandDispatcher(dry_run=True)
    
    # Test different actions
    test_intents = [
        Intent(name="test", confidence=0.9, text="test", action="log", feedback="Test erfolgreich"),
        Intent(name="time", confidence=0.9, text="zeit", action="time", feedback="Es ist {time}"),
        Intent(name="help", confidence=0.9, text="hilfe", action="help"),
        Intent(name="play", confidence=0.9, text="play", action={"type": "key_command", "value": "Space"}),
    ]
    
    for intent in test_intents:
        result = dispatcher.execute(intent)
        logger.info(f"  {intent.name} -> Success: {result.success}, Feedback: {result.feedback}")
    
    logger.success("✅ Dispatcher test completed")
