import os
import time
from pypdf import PdfReader
import google.generativeai as genai
import streamlit as st
from gtts import gTTS
from io import BytesIO

# =================== CONFIG ===================
os.environ["GOOGLE_API_KEY"] = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
generation_model = genai.GenerativeModel("gemini-1.5-flash")

# =================== FUNCTIONS ===================

def list_pdfs(folder_path):
    return [f for f in os.listdir(folder_path) if f.endswith('.pdf')]

def extract_pdf_pages(pdf_path):
    reader = PdfReader(pdf_path)
    return [page.extract_text() or "" for page in reader.pages]

def speak_text(text):
    tts = gTTS(text)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp

def use_llm(prompt):
    response = generation_model.generate_content(prompt)
    return response.text

def translate_text(text, target_lang="French"):
    return use_llm(f"Translate this to {target_lang} language:\n\n{text}")

def summarize_text(text):
    return use_llm(f"Summarize this page:\n\n{text}")

def simplify_text(text):
    return use_llm(f"Explain this like I'm 10:\n\n{text}")

def chat_about_text(text, question):
    prompt = f"Context:\n{text}\n\nQuestion: {question}"
    return use_llm(prompt)

# =================== STREAMLIT UI ===================

st.set_page_config(page_title="📚 Smart Book Reader", layout="wide")

# Custom dark theme with animations
custom_css = f"""
    <style>
    html, body, [class*="css"]  {{
        background-color: #000000 !important;
        color: #cce4ff !important;
        transition: background-color 0.6s ease, color 0.6s ease;
    }}
    .stTextInput > div > div > input, .stTextArea textarea {{
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #004c99 !important;
        transition: background-color 0.6s ease, color 0.6s ease;
    }}
    .stButton button {{
        background-color: #003366 !important;
        color: #ffffff !important;
        border: 1px solid #004c99 !important;
        animation: pulse 1.5s infinite;
    }}
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1); }}
    }}
    .stSelectbox > div {{
        background-color: #111111 !important;
        color: #ffffff !important;
        transition: background-color 0.6s ease, color 0.6s ease;
    }}
    .block-container {{
        transition: all 0.5s ease-in-out;
    }}
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.title("📖 AI Smart Book Reader")

# PDF Library
folder_path = r"C:\\Users\\ayush\\Downloads\\Pdf Folder"  # Make sure this folder exists with some PDFs
os.makedirs(folder_path, exist_ok=True)

pdf_files = list_pdfs(folder_path)
selected_pdf = st.selectbox("📚 Select a book", pdf_files)

if selected_pdf:
    pages = extract_pdf_pages(os.path.join(folder_path, selected_pdf))
    page_num = st.number_input("📄 Page", 0, len(pages)-1, 0)
    current_page = pages[page_num]

    st.markdown("### 📖 Page Content")
    st.text_area("", value=current_page, height=300)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔊 Read Aloud"):
            st.audio(speak_text(current_page), format="audio/mp3")

    with col2:
        translate_clicked = st.button("🌐 Translate")
        lang_display = st.selectbox(
            "Select Language",
            ["French", "Spanish", "Hindi", "German", "Malayalam", "Tamil"],
            key="translate_lang"
        )
        lang_codes = {
            "French": "fr",
            "Spanish": "es",
            "Hindi": "hi",
            "German": "de",
            "Malayalam": "ml",
            "Tamil": "ta"
        }
        lang = lang_codes.get(lang_display, "fr")

    with col3:
        summarize_clicked = st.button("📝 Summarize")

    with col4:
        simplify_clicked = st.button("🧠 Simplify")

    output_text = ""
    output_title = ""

    if translate_clicked:
        output_title = "🌐 Translated Output"
        output_text = translate_text(current_page, lang_display)

    elif summarize_clicked:
        output_title = "📝 Summary Output"
        output_text = summarize_text(current_page)

    elif simplify_clicked:
        output_title = "🧠 Simplified Output"
        output_text = simplify_text(current_page)

    if output_text:
        st.markdown(f"### {output_title}")
        st.markdown(f"<div style='padding: 1rem; background-color: #111111; border: 1px solid #004c99; border-radius: 8px; transition: all 0.6s ease;'>{output_text}</div>", unsafe_allow_html=True)

    user_query = st.text_input("🤔 Ask about this page")
    if st.button("💬 Chat with Page") and user_query.strip():
        st.markdown("### 💬 AI Response")
        answer = chat_about_text(current_page, user_query)
        st.markdown(f"<div style='padding: 1rem; background-color: #111111; border: 1px solid #004c99; border-radius: 8px; transition: all 0.6s ease;'>{answer}</div>", unsafe_allow_html=True)

# Optional: Upload more PDFs
with st.expander("📤 Upload New Book"):
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
    if uploaded_pdf:
        with open(os.path.join(folder_path, uploaded_pdf.name), "wb") as f:
            f.write(uploaded_pdf.read())
        st.success(f"Uploaded {uploaded_pdf.name} successfully!")
