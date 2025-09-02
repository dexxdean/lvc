#!/usr/bin/env python3
"""
Wake Word Detection System
Simple keyword-based wake word detection
"""

import numpy as np
from typing import List, Optional
import re
from difflib import SequenceMatcher

from loguru import logger


class WakeWordDetector:
    """Simple wake word detection using keyword matching"""
    
    def __init__(
        self,
        models: Optional[List[str]] = None,
        threshold: float = 0.6  # Lower threshold for better detection
    ):
        """
        Initialize wake word detector
        
        Args:
            models: List of wake words/phrases
            threshold: Detection threshold (0.0 to 1.0)
        """
        self.threshold = threshold
        
        # Default German wake words if none provided
        if models is None:
            self.wake_words = [
                "hey logic",
                "hallo logic", 
                "logic",
                "computer",
                "hey computer",
                "aufnahme starten",
                "logik",  # German variant
                "hallo logik",
                "hey logik"
            ]
        else:
            self.wake_words = models
        
        logger.info(f"🎯 Wake word detector initialized")
        logger.info(f"📝 Wake words: {', '.join(self.wake_words)}")
        logger.info(f"🎚️ Threshold: {threshold}")
        
        # Preprocessing patterns
        self.cleanup_pattern = re.compile(r'[^\w\s]', re.UNICODE)
        
    def detect(self, audio_data: np.ndarray, stt_engine=None) -> bool:
        """
        Detect wake word in audio data
        
        Args:
            audio_data: Audio data as numpy array
            stt_engine: Speech-to-text engine for transcription
            
        Returns:
            True if wake word detected
        """
        # If no STT engine provided, fall back to text-based detection
        if stt_engine is None:
            logger.debug("🔍 No STT engine provided, using basic detection")
            return False
        
        try:
            # Convert audio to text using STT
            text = stt_engine.transcribe(audio_data)
            
            if text:
                logger.debug(f"🎤 Transcribed audio: '{text}'")
                return self.detect_in_text(text)
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Wake word detection error: {e}")
            return False
    
    def detect_in_text(self, text: str) -> bool:
        """
        Detect wake word in transcribed text
        
        Args:
            text: Transcribed text to check
            
        Returns:
            True if wake word detected
        """
        if not text:
            return False
        
        # Clean and normalize text
        cleaned_text = self._normalize_text(text)
        
        logger.debug(f"🔍 Checking text: '{cleaned_text}'")
        
        # Check each wake word
        for wake_word in self.wake_words:
            normalized_wake_word = self._normalize_text(wake_word)
            
            # Exact match
            if normalized_wake_word in cleaned_text:
                logger.info(f"🎯 Wake word detected: '{wake_word}' (exact match)")
                return True
            
            # Fuzzy match using sequence similarity
            similarity = self._calculate_similarity(normalized_wake_word, cleaned_text)
            if similarity >= self.threshold:
                logger.info(f"🎯 Wake word detected: '{wake_word}' (similarity: {similarity:.2f})")
                return True
        
        return False
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and extra whitespace
        text = self.cleanup_pattern.sub(' ', text)
        text = ' '.join(text.split())
        
        return text
    
    def _calculate_similarity(self, wake_word: str, text: str) -> float:
        """
        Calculate similarity between wake word and text
        
        Args:
            wake_word: Wake word to search for
            text: Text to search in
            
        Returns:
            Similarity score (0.0 to 1.0)
        """
        # Direct similarity
        direct_similarity = SequenceMatcher(None, wake_word, text).ratio()
        
        # Check if wake word is contained in text
        if wake_word in text:
            # Boost score for containment
            containment_boost = 0.3
            return min(1.0, direct_similarity + containment_boost)
        
        # Check word-by-word similarity for multi-word wake words
        wake_words = wake_word.split()
        text_words = text.split()
        
        if len(wake_words) > 1 and len(text_words) > 0:
            word_matches = 0
            for w_word in wake_words:
                best_match = 0
                for t_word in text_words:
                    similarity = SequenceMatcher(None, w_word, t_word).ratio()
                    best_match = max(best_match, similarity)
                if best_match > 0.7:  # Word similarity threshold
                    word_matches += 1
            
            word_similarity = word_matches / len(wake_words)
            return max(direct_similarity, word_similarity)
        
        return direct_similarity
    
    def add_wake_word(self, wake_word: str):
        """Add a new wake word"""
        if wake_word not in self.wake_words:
            self.wake_words.append(wake_word)
            logger.info(f"➕ Added wake word: '{wake_word}'")
    
    def remove_wake_word(self, wake_word: str):
        """Remove a wake word"""
        if wake_word in self.wake_words:
            self.wake_words.remove(wake_word)
            logger.info(f"➖ Removed wake word: '{wake_word}'")
    
    def set_threshold(self, threshold: float):
        """Set detection threshold"""
        self.threshold = max(0.0, min(1.0, threshold))
        logger.info(f"🎚️ Threshold set to: {self.threshold}")
    
    def get_wake_words(self) -> List[str]:
        """Get list of current wake words"""
        return self.wake_words.copy()


# Test functions
def test_text_detection():
    """Test wake word detection with text samples"""
    detector = WakeWordDetector(threshold=0.6)
    
    test_cases = [
        "Hey Logic, start recording",  # Should detect
        "Hallo Logic, wie geht's?",    # Should detect
        "Logic Pro ist super",         # Should detect "logic"
        "Computer, öffne das Projekt", # Should detect "computer"
        "Das ist ein Test",           # Should NOT detect
        "Hey Logik, starte auf",      # Might detect (fuzzy match)
        "aufnahme starten bitte",     # Should detect "aufnahme"
    ]
    
    logger.info("🧪 Testing wake word detection...")
    
    for text in test_cases:
        detected = detector.detect_in_text(text)
        status = "✅" if detected else "❌"
        logger.info(f"{status} '{text}' -> {detected}")


if __name__ == "__main__":
    # Run tests
    test_text_detection()
