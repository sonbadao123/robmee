"""
ROB RUN - AI TRANSLATION ENGINE
Context-aware Vietnamese localization with tag preservation and gaming glossary.
"""

import os
import json
import re
import time
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GLOSSARY_PATH = os.path.join(CURRENT_DIR, "glossary.json")
CACHE_PATH = os.path.join(CURRENT_DIR, "cache.json")

class AiTranslator:
    def __init__(self):
        self.glossary = {}
        if os.path.exists(GLOSSARY_PATH):
            with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
                self.glossary = json.load(f)

        self.cache = {}
        if os.path.exists(CACHE_PATH):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                self.cache = json.load(f)

    def save_cache(self):
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def translate(self, text):
        if not text or not text.strip():
            return text

        # 1. Exact Glossary Match
        if text in self.glossary:
            return self.glossary[text]

        # 2. Check Cache
        if text in self.cache:
            return self.cache[text]

        # 3. Preserve Unity formatting tags and ICU placeholders
        # Replace <color=...>, </color>, <b>, </b>, {0}, {1}, etc. with tokens
        tokens = []
        def repl(match):
            tokens.append(match.group(0))
            return f"__TOK{len(tokens)-1}__"

        tag_pattern = re.compile(r"(<[^>]+>|\{[0-9]+[^}]*\})")
        tokenized_text = tag_pattern.sub(repl, text)

        # 4. Perform Neural Translation
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            "client": "gtx",
            "sl": "en",
            "tl": "vi",
            "dt": "t",
            "q": tokenized_text
        }

        translated = text
        try:
            r = requests.get(url, params=params, timeout=6)
            if r.status_code == 200:
                data = r.json()
                translated = "".join([part[0] for part in data[0] if part and part[0]])
                
                # Restore tokens
                for idx, token in enumerate(tokens):
                    tok_str = f"__TOK{idx}__"
                    # Handle possible lowercase or spaced tokens from translator
                    translated = re.sub(rf"__\s*TOK\s*{idx}\s*__", token, translated, flags=re.IGNORECASE)

                # Post-apply glossary terms
                for en_term, vi_term in self.glossary.items():
                    if len(en_term) >= 4 and en_term.lower() in text.lower():
                        translated = re.sub(re.escape(en_term), vi_term, translated, flags=re.IGNORECASE)

                self.cache[text] = translated
        except Exception:
            translated = text

        return translated

    def translate_batch(self, text_list, batch_size=20, delay=0.1):
        """Translates a list of strings with auto-saving cache."""
        results = []
        for i, text in enumerate(text_list):
            res = self.translate(text)
            results.append(res)
            if (i + 1) % batch_size == 0:
                self.save_cache()
                time.sleep(delay)
        self.save_cache()
        return results
