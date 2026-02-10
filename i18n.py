import json
import os
import logging

from config import Config

logger = logging.getLogger(__name__)

_translator_cache = {}

def get_translator(config: Config) -> dict:
    if config.language not in _translator_cache:
        locale_path = os.path.join('locales', f'{config.language}.json')
        try:
            with open(locale_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Locale file not found: {locale_path}, falling back to English")
            with open(os.path.join('locales', 'en.json'), 'r', encoding='utf-8') as f:
                translations = json.load(f)
        _translator_cache[config.language] = translations
    return _translator_cache[config.language]
