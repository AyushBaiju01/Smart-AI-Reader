import streamlit as st
import requests
import json
import fitz  # PyMuPDF
import os

# ✅ PERMANENT GEMINI API KEY (PUT YOUR REAL KEY HERE)
API_KEY = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"  # 👈 Replace this with your actual Gemini key

# ========== PDF to Markdown Converter ==========
def convert_pdf_to_markdown(pdf_path, md_path):
    doc = fitz.open(pdf_path)
    with open(md_path, 'w', encoding='utf-8') as md_file:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            md_file.write(f"# Page {page_num + 1}\n\n")
            md_file.write(text)
            md_file.write("\n\n---\n\n")
    return md_path

# ========== Markdown Loader ==========
def load_markdown_file(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

# ========== Prompt Generator ==========
def generate_augmented_prompt(user_prompt, md_text):
    prompt = f"""
You are an AI assistant. Use the following context information to answer the user's question.

--- Start of Context ---

{md_text}

--- End of Context ---

User's Question: {user_prompt}
Answer:
"""
    return prompt

# ========== Gemini 2.0 Flash API ==========
def call_gemini_flash_raw(augmented_prompt, api_key=API_KEY, model="gemini-1.5-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": augmented_prompt}]}]}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        response_json = response.json()
        return response_json['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"❌ API call failed: {response.status_code} {response.text}"

# ========== Streamlit UI Starts ==========
st.set_page_config(page_title="PDF Gemini Bot", layout="centered")
st.title("📄🔮 Gemini PDF Chatbot")

# Upload PDF directly without entering API key
uploaded_pdf = st.file_uploader("Upload your PDF file", type=['pdf'])

if uploaded_pdf:

    # Save uploaded PDF to temp file
    pdf_path = "uploaded_file.pdf"
    with open(pdf_path, "wb") as f:
        f.write(uploaded_pdf.read())

    md_path = "converted_file.md"
    
    # Convert PDF to Markdown
    convert_pdf_to_markdown(pdf_path, md_path)
    
    # Load markdown
    md_text = load_markdown_file(md_path)

    # Chat interface
    user_prompt = st.text_area("Ask your question:")

    if st.button("Ask Gemini"):
        if user_prompt.strip() != "":
            augmented_prompt = generate_augmented_prompt(user_prompt, md_text)
            response_text = call_gemini_flash_raw(augmented_prompt)
            st.write("🤖 Gemini says:")
            st.write(response_text)
        else:
            st.warning("Please enter a question to ask.")
