import json
import locale
import os

LOCALE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locale")

def load_language_list(language):
    file_path = os.path.join(LOCALE_DIR, f"{language}.json")
    if not os.path.exists(file_path):
        file_path = os.path.join(LOCALE_DIR, "id_ID.json")
    if not os.path.exists(file_path):
        file_path = os.path.join(LOCALE_DIR, "en_US.json")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            language_list = json.load(f)
        return language_list
    except Exception:
        return {}


class I18nAuto:
    def __init__(self, language="id_ID"):
        if language in ["Auto", None]:
            language = "id_ID"
        
        file_path = os.path.join(LOCALE_DIR, f"{language}.json")
        if not os.path.exists(file_path):
            language = "id_ID"
            
        self.language = language
        self.language_map = load_language_list(language)

    def __call__(self, key):
        return self.language_map.get(key, key)

    def __repr__(self):
        return "Use Language: " + self.language
