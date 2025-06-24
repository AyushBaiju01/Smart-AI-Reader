import requests
import json
import fitz  # PyMuPDF

# PDF to Markdown Converter
def convert_pdf_to_markdown(pdf_path, md_path):
    doc = fitz.open(pdf_path)
    with open(md_path, 'w', encoding='utf-8') as md_file:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            md_file.write(f"# Page {page_num + 1}\n\n")
            md_file.write(text)
            md_file.write("\n\n---\n\n")
    print(f"✅ PDF converted to Markdown and saved at: {md_path}")

# Markdown File Loader
def load_markdown_file(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        return f.read()

# Augmented Prompt Generator
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

# Gemini 2.0 Flash API Caller (Raw REST API)
def call_gemini_flash_raw(augmented_prompt, api_key, model="gemini-1.5-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {"parts": [{"text": augmented_prompt}]}
        ]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        response_json = response.json()
        return response_json['candidates'][0]['content']['parts'][0]['text']
    else:
        print(f"❌ API call failed: {response.status_code} {response.text}")
        return None

# ============================ MAIN BOT EXECUTION ============================

# Replace with your actual Gemini API key
api_key = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"

# Use your uploaded file path
pdf_path = r"C:\Users\ayush\Downloads\Pride&Prejudice.pdf"
md_path = r"C:\Users\ayush\Downloads\Pride&Prejudice.md"

# Convert PDF to Markdown (only once)
convert_pdf_to_markdown(pdf_path, md_path)

# Load converted Markdown
md_text = load_markdown_file(md_path)

# Chat loop
while True:
    user_prompt = input("\n💬 Ask your question (or type 'exit' to quit): ")
    if user_prompt.lower() in ['exit', 'quit', 'bye']:
        print("👋 Exiting AI Assistant. Have a nice day!")
        break

    augmented_prompt = generate_augmented_prompt(user_prompt, md_text)
    response_text = call_gemini_flash_raw(augmented_prompt, api_key)

    if response_text:
        print("\n🤖 Gemini says:\n")
        print(response_text)
    else:
        print("❌ No response from Gemini!")
