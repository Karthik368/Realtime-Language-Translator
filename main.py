import os
import time
import pygame
import streamlit as st
import speech_recognition as sr
from gtts import gTTS, lang as gtts_langs
from googletrans import LANGUAGES, Translator
import tempfile

# Initialize the translator and mixer modules
translator = Translator()
pygame.mixer.init()

# List of languages to remove (including 'iw' for Hebrew, 'sd' for Sindhi, 'or' for Odia)
languages_to_remove = {
    'hy', 'az', 'eu', 'zh-tw', 'ny', 'nl', 'co', 'da', 'hr', 'cs', 'eo', 'et', 'am', 'sq', 'af', 'ca', 'be', 'bs', 'bg', 'ceb',
    'fi', 'fy', 'gl', 'ka', 'el', 'ht', 'ha', 'haw', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'kk', 'km', 'ko', 'ku', 'ky', 'lo',
    'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms', 'mt', 'mi', 'mn', 'my', 'no', 'ps', 'fa', 'pl', 'ro', 'sm', 'gd', 'sr', 'st', 'sn',
    'si', 'sk', 'sl', 'so', 'su', 'sw', 'sv', 'tg', 'zu', 'yo', 'yi', 'xh', 'cy', 'vi', 'ug', 'uz', 'tr', 'uk', 'fil', 'iw', 'or', 'sd'
}

# Filter out the specified languages
filtered_languages = {code: name for code, name in LANGUAGES.items() if code not in languages_to_remove}

# Create a mapping between language names and language codes
language_mapping = {name: code for code, name in filtered_languages.items()}

# Fetch supported TTS languages dynamically from gTTS
supported_tts_languages = gtts_langs.tts_langs()

def get_language_code(language_name):
    """ Get the language code from the language name. """
    return language_mapping.get(language_name, language_name)

def translator_function(spoken_text, from_language, to_language):
    """ Translate text from one language to another. """
    if from_language == to_language:
        return spoken_text  # Skip translation if languages are the same
    try:
        return translator.translate(spoken_text, src=from_language, dest=to_language).text
    except Exception as e:
        st.error(f"Translation failed: {e}")
        return None

def text_to_voice(text_data, to_language):
    """ Convert text to speech if the language is supported, otherwise provide a warning. """
    if to_language in supported_tts_languages:
        try:
            temp_dir = tempfile.gettempdir()
            temp_audio_path = os.path.join(temp_dir, "temp_audio.mp3")

            myobj = gTTS(text=text_data, lang=to_language, slow=False)
            myobj.save(temp_audio_path)

            audio = pygame.mixer.Sound(temp_audio_path)
            audio.play()
            os.remove(temp_audio_path)
        except Exception as e:
            st.error(f"Text-to-speech error: {e}")
    else:
        st.warning(f"TTS is not supported for {LANGUAGES.get(to_language, to_language)}. Text will be displayed instead.")

def main_process(output_placeholder, from_language, to_language, from_language_name, to_language_name):
    """ Main function to handle speech recognition, translation, and TTS. """
    rec = sr.Recognizer()
    with sr.Microphone() as source:
        output_placeholder.text("Adjusting for ambient noise...")
        rec.adjust_for_ambient_noise(source, duration=1)  # Increased duration for better calibration
        output_placeholder.text("Listening... Speak now.")
        rec.energy_threshold = 200  # Lowered threshold for better sensitivity
        rec.pause_threshold = 1.5  # Increased pause threshold to allow longer sentences

        try:
            # Capture audio from the microphone
            audio = rec.listen(source)
            st.write("Audio captured successfully.")  # Debug statement
        except sr.WaitTimeoutError:
            output_placeholder.text("No speech detected. Please try again.")
            st.write("No speech detected: WaitTimeoutError")  # Debug statement
            return
        except Exception as e:
            st.error(f"Error capturing audio: {e}")
            return
    
    if not st.session_state.is_translate_on:
        output_placeholder.text("Translation stopped.")
        st.write("Translation stopped.")  # Debug statement
        return
    
    try:
        # Step 1: Recognize the speech
        output_placeholder.text("Processing speech...")
        spoken_text = rec.recognize_google(audio, language=from_language)
        st.write(f"Recognized speech: {spoken_text}")  # Debug statement

        # Display the recognized speech in the source language
        output_placeholder.text(f"Source Language ({from_language_name}): {spoken_text}")

        # Step 2: Start the translation process
        output_placeholder.text("Translating...")
        translated_text = translator_function(spoken_text, from_language, to_language)
        
        if translated_text:
            # Display the translated text
            output_placeholder.text(f"Translated Text ({to_language_name}): {translated_text}")
            # Convert the translated text to speech
            text_to_voice(translated_text, to_language)
    except sr.UnknownValueError:
        st.error("Google Speech Recognition could not understand the audio.")
        st.write("Google Speech Recognition could not understand the audio.")  # Debug statement
    except sr.RequestError as e:
        st.error(f"Could not request results from Google Speech Recognition service; {e}")
        st.write(f"RequestError: {e}")  # Debug statement
    except Exception as e:
        st.error(f"Error occurred: {e}")
        st.write(f"Unexpected error: {e}")  # Debug statement

# Streamlit UI
st.title("Language Translator")

if 'is_translate_on' not in st.session_state:
    st.session_state.is_translate_on = False

from_language_name = st.selectbox("Select Source Language:", list(filtered_languages.values()))
to_language_name = st.selectbox("Select Target Language:", list(filtered_languages.values()))

from_language = get_language_code(from_language_name)
to_language = get_language_code(to_language_name)

col1, col2 = st.columns(2)

with col1:
    start_button = st.button("Start Translation", help="Click to start translation", type="primary")

with col2:
    stop_button = st.button("Stop Translation", help="Click to stop translation", type="secondary")

if start_button:
    st.session_state.is_translate_on = True
    output_placeholder = st.empty()
    with st.spinner("Listening..."):
        main_process(output_placeholder, from_language, to_language, from_language_name, to_language_name)
    st.session_state.is_translate_on = False

if stop_button:
    st.session_state.is_translate_on = False
    st.success("Translation stopped.")

if st.session_state.is_translate_on:
    st.info("Translation is currently running. Speak into your microphone.")
else:
    st.info("Translation is stopped. Click 'Start Translation' to begin.")