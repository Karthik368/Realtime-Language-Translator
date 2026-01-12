import os
import streamlit as st
import speech_recognition as sr
from gtts import gTTS, lang as gtts_langs
from googletrans import LANGUAGES, Translator
import tempfile

# ----------------------------------
# SAFE pygame import (Cloud compatible)
# ----------------------------------
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except Exception:
    PYGAME_AVAILABLE = False

# ----------------------------------
# Translator setup
# ----------------------------------
translator = Translator()

# ----------------------------------
# Streamlit UI notice
# ----------------------------------
st.warning(
    "⚠️ Note: Live microphone input and audio playback are limited on cloud deployment. "
    "For full functionality, please run this app locally."
)

st.title("Real-Time Language Translator")

# ----------------------------------
# Language filtering
# ----------------------------------
languages_to_remove = {
    'hy', 'az', 'eu', 'zh-tw', 'ny', 'nl', 'co', 'da', 'hr', 'cs', 'eo', 'et', 'am', 'sq', 'af',
    'ca', 'be', 'bs', 'bg', 'ceb', 'fi', 'fy', 'gl', 'ka', 'el', 'ht', 'ha', 'haw', 'hmn',
    'hu', 'is', 'ig', 'id', 'ga', 'kk', 'km', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt',
    'lb', 'mk', 'mg', 'ms', 'mt', 'mi', 'mn', 'my', 'no', 'ps', 'fa', 'pl', 'ro', 'sm',
    'gd', 'sr', 'st', 'sn', 'si', 'sk', 'sl', 'so', 'su', 'sw', 'sv', 'tg', 'zu', 'yo',
    'yi', 'xh', 'cy', 'vi', 'ug', 'uz', 'tr', 'uk', 'fil', 'iw', 'or', 'sd'
}

filtered_languages = {
    code: name for code, name in LANGUAGES.items() if code not in languages_to_remove
}
language_mapping = {name: code for code, name in filtered_languages.items()}

supported_tts_languages = gtts_langs.tts_langs()

# ----------------------------------
# Helper functions
# ----------------------------------
def get_language_code(language_name):
    return language_mapping.get(language_name, language_name)


def translate_text(text, src_lang, dest_lang):
    if src_lang == dest_lang:
        return text
    try:
        return translator.translate(text, src=src_lang, dest=dest_lang).text
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return None


def text_to_voice(text, lang_code):
    if not PYGAME_AVAILABLE:
        st.info("🔇 Audio playback disabled on cloud.")
        return

    if lang_code in supported_tts_languages:
        try:
            temp_path = os.path.join(tempfile.gettempdir(), "audio.mp3")
            tts = gTTS(text=text, lang=lang_code)
            tts.save(temp_path)
            sound = pygame.mixer.Sound(temp_path)
            sound.play()
        except Exception as e:
            st.error(f"TTS error: {e}")
    else:
        st.warning("TTS not supported for this language.")


# ----------------------------------
# UI Components
# ----------------------------------
from_lang_name = st.selectbox("Select Source Language", list(filtered_languages.values()))
to_lang_name = st.selectbox("Select Target Language", list(filtered_languages.values()))

from_lang = get_language_code(from_lang_name)
to_lang = get_language_code(to_lang_name)

st.markdown("---")

# ----------------------------------
# Text-based translation (Cloud-safe)
# ----------------------------------
input_text = st.text_area("Enter text to translate")

if st.button("Translate Text"):
    if input_text.strip():
        translated = translate_text(input_text, from_lang, to_lang)
        if translated:
            st.success(f"Translated Text ({to_lang_name}):")
            st.write(translated)
            text_to_voice(translated, to_lang)
    else:
        st.warning("Please enter text.")

st.markdown("---")

# ----------------------------------
# Voice translation (Local only)
# ----------------------------------
if st.button("🎤 Start Voice Translation (Local Only)"):
    if not PYGAME_AVAILABLE:
        st.error("Voice translation works only in local environment.")
    else:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening...")
            audio = recognizer.listen(source)

        try:
            spoken_text = recognizer.recognize_google(audio, language=from_lang)
            st.write(f"Recognized: {spoken_text}")

            translated = translate_text(spoken_text, from_lang, to_lang)
            if translated:
                st.success(f"Translated ({to_lang_name}):")
                st.write(translated)
                text_to_voice(translated, to_lang)

        except Exception as e:
            st.error(f"Speech recognition error: {e}")
