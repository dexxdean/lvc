#!/usr/bin/env python3
"""
Intent Parser Module
Parses transcribed text to identify commands and extract parameters
"""

import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from difflib import SequenceMatcher
from loguru import logger


@dataclass
class Intent:
    """Represents a recognized intent"""
    name: str
    confidence: float
    text: str
    slots: Dict[str, Any] = None
    action: Any = None
    feedback: str = ""


class IntentParser:
    """Parse text to identify intents and extract slots"""
    
    def __init__(self, commands_config: Dict[str, Any] = None):
        """
        Initialize intent parser
        
        Args:
            commands_config: Commands configuration dictionary
        """
        self.commands = []
        self.min_confidence = 0.6
        
        if commands_config:
            self._load_commands(commands_config)
        else:
            self._load_default_commands()
        
        logger.info(f"📝 Intent parser initialized with {len(self.commands)} commands")
    
    def _load_commands(self, config: Dict[str, Any]):
        """Load commands from configuration"""
        # Load test commands if in test mode
        if config.get('test_commands'):
            for cmd in config['test_commands']:
                self.commands.append(cmd)
                logger.debug(f"  Loaded test command: {cmd['intent']}")
        
        # Load production commands if not in test mode
        if config.get('production_commands') and not config.get('test_mode', True):
            for cmd in config['production_commands']:
                self.commands.append(cmd)
                logger.debug(f"  Loaded production command: {cmd['intent']}")
    
    def _load_default_commands(self):
        """Load default test commands"""
        self.commands = [
            {
                'intent': 'test',
                'patterns': ['test', 'teste', 'testing'],
                'action': 'log',
                'feedback': 'Test erfolgreich'
            },
            {
                'intent': 'hello',
                'patterns': ['hallo', 'guten tag', 'hi', 'servus'],
                'action': 'log',
                'feedback': 'Hallo! Wie kann ich helfen?'
            },
            {
                'intent': 'stop',
                'patterns': ['stop', 'stopp', 'beenden', 'ende', 'ausschalten'],
                'action': 'exit',
                'feedback': 'Auf Wiedersehen'
            },
            {
                'intent': 'help',
                'patterns': ['hilfe', 'help', 'was kannst du'],
                'action': 'help',
                'feedback': 'Ich kann dir mit folgenden Befehlen helfen: Test, Hallo, Stop'
            }
        ]
    
    def parse(self, text: str) -> Optional[Intent]:
        """
        Parse text to identify intent
        
        Args:
            text: Transcribed text to parse
            
        Returns:
            Intent object if found, None otherwise
        """
        if not text:
            return None
        
        # Normalize text
        normalized_text = self._normalize_text(text)
        logger.debug(f"🔍 Parsing: '{normalized_text}'")
        
        best_match = None
        best_confidence = 0
        
        # Check each command
        for command in self.commands:
            # Check patterns
            for pattern in command.get('patterns', []):
                normalized_pattern = self._normalize_text(pattern)
                
                # Calculate similarity
                confidence = self._calculate_similarity(
                    normalized_pattern,
                    normalized_text
                )
                
                # Check for exact containment
                if normalized_pattern in normalized_text:
                    confidence = max(confidence, 0.9)
                
                # Update best match
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = command
                    
                    logger.debug(f"  Pattern '{pattern}' -> confidence: {confidence:.2f}")
        
        # Return intent if confidence is high enough
        if best_match and best_confidence >= self.min_confidence:
            intent = Intent(
                name=best_match['intent'],
                confidence=best_confidence,
                text=text,
                slots={},
                action=best_match.get('action'),
                feedback=best_match.get('feedback', '')
            )
            
            logger.info(f"✅ Intent recognized: {intent.name} (confidence: {intent.confidence:.2f})")
            return intent
        
        logger.debug(f"❌ No intent matched (best: {best_confidence:.2f})")
        return None
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _calculate_similarity(self, pattern: str, text: str) -> float:
        """Calculate similarity between pattern and text"""
        # Direct similarity
        direct_sim = SequenceMatcher(None, pattern, text).ratio()
        
        # Word-based similarity
        pattern_words = set(pattern.split())
        text_words = set(text.split())
        
        if pattern_words and text_words:
            # Calculate Jaccard similarity
            intersection = pattern_words.intersection(text_words)
            union = pattern_words.union(text_words)
            word_sim = len(intersection) / len(union) if union else 0
            
            # Boost if all pattern words are in text
            if pattern_words.issubset(text_words):
                word_sim = min(1.0, word_sim + 0.3)
            
            # Combined similarity
            return max(direct_sim, word_sim)
        
        return direct_sim
    
    def add_command(self, intent: str, patterns: List[str], action: Any = None, feedback: str = ""):
        """Add a new command"""
        self.commands.append({
            'intent': intent,
            'patterns': patterns,
            'action': action,
            'feedback': feedback
        })
        logger.info(f"➕ Added command: {intent}")
    
    def set_min_confidence(self, confidence: float):
        """Set minimum confidence threshold"""
        self.min_confidence = max(0.0, min(1.0, confidence))
        logger.info(f"🎚️ Min confidence set to: {self.min_confidence}")


# Test functions
if __name__ == "__main__":
    logger.info("🧪 Testing Intent Parser...")
    
    parser = IntentParser()
    
    test_phrases = [
        "test",
        "hallo wie geht es",
        "stop bitte",
        "hilfe",
        "spiele musik",  # Should not match
        "teste das system",
        "beenden"
    ]
    
    for phrase in test_phrases:
        intent = parser.parse(phrase)
        if intent:
            logger.success(f"✅ '{phrase}' -> {intent.name} ({intent.confidence:.2f})")
        else:
            logger.warning(f"❌ '{phrase}' -> No match")
    
    logger.success("✅ Intent parser test completed")
