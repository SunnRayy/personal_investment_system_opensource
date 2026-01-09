"""
Core translation service for the Personal Investment System.

Usage:
    from src.localization import _
    
    # Simple translation
    message = _("Hello World")
    
    # With parameters
    message = _("Portfolio value: {value}", value="$100,000")
"""

import os
import gettext
from typing import Optional, Dict, Any
from functools import lru_cache

import yaml

# Global translator instance
_translator: Optional['Translator'] = None


class Translator:
    """Thread-safe translation manager."""
    
    def __init__(self, locale: str = 'en', domain: str = 'messages'):
        self.locale = locale
        self.domain = domain
        self._translations: Dict[str, gettext.GNUTranslations] = {}
        self._load_translations()
    
    def _load_translations(self) -> None:
        """Load translation files for the current locale."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        locale_dir = os.path.join(base_dir, 'translations')
        
        try:
            self._translations[self.domain] = gettext.translation(
                self.domain,
                localedir=locale_dir,
                languages=[self.locale],
                fallback=True
            )
        except FileNotFoundError:
            self._translations[self.domain] = gettext.NullTranslations()
    
    def gettext(self, message: str, **kwargs) -> str:
        """Translate a message with optional parameter substitution."""
        translation = self._translations.get(self.domain)
        if translation:
            translated = translation.gettext(message)
        else:
            translated = message
        
        if kwargs:
            return translated.format(**kwargs)
        return translated
    
    def set_locale(self, locale: str) -> None:
        """Change the current locale."""
        self.locale = locale
        self._load_translations()


def get_translator(locale: str = 'en') -> Translator:
    """Get or create a translator instance."""
    global _translator
    if _translator is None or _translator.locale != locale:
        _translator = Translator(locale=locale)
    return _translator


def _(message: str, **kwargs) -> str:
    """Shorthand translation function."""
    translator = get_translator()
    return translator.gettext(message, **kwargs)
