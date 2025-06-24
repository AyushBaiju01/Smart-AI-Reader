import os
from gtts import gTTS
from io import BytesIO
import streamlit as st
import speech_recognition as sr
import google.generativeai as genai

# ========== CONFIG ==========

st.set_page_config(page_title="🌍 Voice Translator PWA", layout="centered")
os.environ["GOOGLE_API_KEY"] = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-flash")

supported_languages = {
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Hindi": "hi",
    "Malayalam": "ml",
    "Arabic": "ar",
    "Chinese": "zh-CN",
    "Japanese": "ja",
    "Tamil": "ta",
}

# ========== FUNCTIONS ==========

def listen_to_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening... Speak now.")
        audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
        st.success("✅ Voice captured!")
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand audio."
    except sr.RequestError:
        return "Speech Recognition service is down."

def translate_text(text, source_lang, target_lang):
    prompt = f"Translate the following from {source_lang} to {target_lang}:\n\n'{text}'"
    response = model.generate_content(prompt)
    return response.text.strip()

def speak_text(text, lang_code):
    tts = gTTS(text=text, lang=lang_code)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp

# ========== UI ==========

st.title("🌍 Real-Time Voice Translator")
st.caption("Translate spoken sentences from one language to another with voice output!")

col1, col2 = st.columns(2)
with col1:
    source_lang = st.selectbox("🎙️ Speak in", list(supported_languages.keys()), index=0)
with col2:
    target_lang = st.selectbox("🗣️ Translate to", list(supported_languages.keys()), index=1)

if st.button("🎧 Listen and Translate"):
    with st.spinner("Listening..."):
        original_text = listen_to_voice()
        st.write(f"🔊 You said: **{original_text}**")

    with st.spinner("Translating..."):
        translated = translate_text(original_text, source_lang, target_lang)
        st.success(f"🌐 Translation: {translated}")
        st.audio(speak_text(translated, supported_languages[target_lang]), format="audio/mp3")
