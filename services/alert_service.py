"""
Alert service for PlayStation Management System.
"""

import os
import platform
import threading
import logging
from typing import Optional

from utils.app_path import get_resource_path

logger = logging.getLogger(__name__)

class AlertService:
    """Service for playing alert sounds."""
    
    _instance = None
    _sound_loaded = False
    _muted = False
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not AlertService._sound_loaded:
            self._setup_sound()
            AlertService._sound_loaded = True
    
    def _setup_sound(self):
        self._system = platform.system()
        self._alert_path = get_resource_path("resources/alert.wav")
        self._has_alert = os.path.exists(self._alert_path)
    
    def play_alert(self, async_play: bool = True):
        """Play the session expiration alert sound.
        
        Args:
            async_play: If True, play sound in background thread
        """
        if not self._has_alert or AlertService._muted:
            return
        
        if async_play:
            thread = threading.Thread(target=self._play_sound_sync, daemon=True)
            thread.start()
        else:
            self._play_sound_sync()
    
    def _play_sound_sync(self):
        """Play sound synchronously."""
        if self._system == "Windows":
            self._play_windows()
        elif self._system == "Linux":
            self._play_linux()
        elif self._system == "Darwin":
            self._play_mac()
    
    def _play_windows(self):
        """Play sound on Windows."""
        try:
            import winsound
            winsound.PlaySound(self._alert_path, winsound.SND_FILENAME)
            logger.debug(f"Played Windows alert sound: {self._alert_path}")
        except Exception as e:
            logger.warning(f"Failed to play Windows sound: {e}")
            self._fallback_beep_windows()
    
    def _play_linux(self):
        """Play sound on Linux."""
        try:
            import subprocess
            subprocess.run(['aplay', self._alert_path], check=True, capture_output=True)
            logger.debug(f"Played Linux alert sound with aplay: {self._alert_path}")
        except Exception as e:
            logger.debug(f"aplay failed, trying paplay: {e}")
            try:
                import subprocess
                subprocess.run(['paplay', self._alert_path], check=True, capture_output=True)
                logger.debug(f"Played Linux alert sound with paplay: {self._alert_path}")
            except Exception as e2:
                logger.warning(f"Failed to play Linux sound with both aplay and paplay: {e2}")
                self._fallback_beep_linux()
    
    def _play_mac(self):
        """Play sound on macOS."""
        try:
            import subprocess
            subprocess.run(['afplay', self._alert_path], check=True, capture_output=True)
            logger.debug(f"Played macOS alert sound: {self._alert_path}")
        except Exception as e:
            logger.warning(f"Failed to play macOS sound: {e}")
            self._fallback_beep_terminal()
    
    def _fallback_beep_windows(self):
        """Fallback beep for Windows."""
        try:
            import winsound
            for _ in range(3):
                winsound.Beep(800, 300)
            logger.debug("Played Windows fallback beep")
        except Exception as e:
            logger.error(f"Windows fallback beep failed: {e}")
    
    def _fallback_beep_linux(self):
        """Fallback beep for Linux."""
        try:
            import subprocess
            for _ in range(3):
                subprocess.run(['echo', '-e', '\a'], capture_output=True)
            logger.debug("Played Linux fallback beep")
        except Exception as e:
            logger.error(f"Linux fallback beep failed: {e}")
    
    def _fallback_beep_terminal(self):
        """Fallback beep for terminal."""
        try:
            import sys
            sys.stdout.write('\a')
            sys.stdout.flush()
            logger.debug("Played terminal fallback beep")
        except Exception as e:
            logger.error(f"Terminal fallback beep failed: {e}")
    
    @staticmethod
    def check_alert_exists() -> bool:
        alert_path = get_resource_path("resources/alert.wav")
        return os.path.exists(alert_path)

    @staticmethod
    def get_alert_path() -> Optional[str]:
        alert_path = get_resource_path("resources/alert.wav")
        if os.path.exists(alert_path):
            return alert_path
        return None
    
    @staticmethod
    def toggle_mute():
        """Toggle mute state."""
        AlertService._muted = not AlertService._muted
    
    @staticmethod
    def is_muted() -> bool:
        """Check if muted."""
        return AlertService._muted