"""
language.py — Language detection and translation for MDM records.

Uses langdetect for detection and deep-translator (Google Translate backend)
for translating non-English company names and addresses to English.

Why translate? Our embedding model and LLM agents work best in English,
and a lot of the multilingual duplicates are just the same company name
written in different scripts/languages.
"""

from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator
from src.utils.logger import get_logger

logger = get_logger(__name__)


def detect_language(text: str) -> str:
    """
    Detect the language of a string. Returns a BCP-47 language code (e.g. "en", "de", "zh-cn").
    Returns "unknown" if detection fails (short strings are unreliable).
    """
    if not text or len(text.strip()) < 5:
        return "unknown"
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"


def translate_to_english(text: str, source_lang: str = "auto") -> str:
    """
    Translate text to English using Google Translate.
    If the text is already English (or detection returns 'en'), returns as-is.

    Args:
        text: Input text to translate
        source_lang: BCP-47 code of the source language, or "auto" for auto-detect

    Returns:
        Translated (or original) text string
    """
    if not text or not text.strip():
        return text

    if source_lang == "en":
        return text

    try:
        translator = GoogleTranslator(source=source_lang, target="en")
        translated = translator.translate(text)
        return translated if translated else text
    except Exception as e:
        logger.warning(f"Translation failed for '{text[:50]}': {e}")
        return text  # fall back to original if translation fails


def detect_and_translate(text: str) -> dict:
    """
    Convenience function: detect language, then translate if non-English.

    Returns a dict with:
        - original: original text
        - detected_lang: detected language code
        - translated: translated text (same as original if already English)
        - was_translated: bool
    """
    lang = detect_language(text)
    if lang in ("en", "unknown"):
        return {
            "original": text,
            "detected_lang": lang,
            "translated": text,
            "was_translated": False,
        }

    translated = translate_to_english(text, source_lang=lang)
    was_translated = translated.lower() != text.lower()

    if was_translated:
        logger.info(f"Translated [{lang}] '{text[:50]}' → '{translated[:50]}'")

    return {
        "original": text,
        "detected_lang": lang,
        "translated": translated,
        "was_translated": was_translated,
    }


def enrich_record_with_translations(record: dict) -> dict:
    """
    Takes a cleaned record dict and adds translated versions of name and address fields.
    Mutates and returns the same dict (adds new keys, doesn't overwrite originals).
    """
    name_result = detect_and_translate(record.get("name_clean", ""))
    addr_result = detect_and_translate(record.get("address_clean", ""))
    city_result = detect_and_translate(record.get("city_clean", ""))

    record["name_lang"] = name_result["detected_lang"]
    record["name_translated"] = name_result["translated"]
    record["address_translated"] = addr_result["translated"]
    record["city_translated"] = city_result["translated"]

    return record


if __name__ == "__main__":
    tests = [
        "Siemens AG",
        "株式会社トヨタ自動車",    # Toyota Motor Corporation in Japanese
        "Société Générale",
        "Газпром",                # Gazprom in Russian
        "Deutsche Bahn GmbH",
    ]

    for t in tests:
        result = detect_and_translate(t)
        print(f"[{result['detected_lang']}] {t!r:40} → {result['translated']!r}")
