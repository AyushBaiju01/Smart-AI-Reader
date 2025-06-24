import os
import time
from tqdm import tqdm
from pypdf import PdfReader
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO

# MUST be first Streamlit command
st.set_page_config(page_title="🎤 Intern RAG App (Voice + Gemini + Pinecone)", layout="centered")

# ==================== CONFIG ====================
os.environ["GOOGLE_API_KEY"] = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"
PINECONE_API_KEY = "pcsk_3VgeYZ_6qwTLfLxXTZZTYqCX8Ea5XhDP4GrFfk7RuPbest7eUTaqKu1W6D38rVFAQW5B3i"
PINECONE_ENV = "us-east-1"
PINECONE_INDEX = "audio"

pdf_path = r"C:\Users\ayush\Downloads\freefromschool.pdf"

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
generation_model = genai.GenerativeModel("gemini-1.5-flash")

pc = Pinecone(api_key=PINECONE_API_KEY)

# Create Pinecone index if needed
if PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )
    time.sleep(2)

index = pc.Index(PINECONE_INDEX)

# ==================== FUNCTIONS ====================

def extract_pdf_text(pdf_path):
    pdf = PdfReader(pdf_path)
    text = ""
    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def chunk_text(text, chunk_size=500, overlap=50):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def embed_text(text):
    response = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"
    )
    return response['embedding']

def upload_to_pinecone(chunks, batch_size=20):
    vectors = []
    for i, chunk in enumerate(tqdm(chunks, desc="Uploading chunks")):
        try:
            embedding = embed_text(chunk)
            vectors.append({'id': f"chunk-{i}", 'values': embedding, 'metadata': {"text": chunk}})
            if len(vectors) >= batch_size:
                index.upsert(vectors=vectors)
                vectors = []
        except Exception as e:
            print(f"Error embedding chunk {i}: {e}")
    if vectors:
        index.upsert(vectors=vectors)
    print("Upload complete.")

def search_pinecone(query, top_k=3):
    query_embedding = embed_text(query)
    response = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    contexts = [match['metadata']['text'] for match in response['matches']]
    return "\n".join(contexts)

def answer_question(user_question):
    context = search_pinecone(user_question)
    if not context:
        return "No relevant context found."

    prompt = f"Use the following context to answer the question:\n\n{context}\n\nQuestion: {user_question}"
    response = generation_model.generate_content(prompt)
    return response.text

def listen_to_voice():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening... Speak now!")
        audio = recognizer.listen(source, timeout=5)
        st.success("🧠 Processing voice...")
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, I couldn't understand your voice input."
    except sr.RequestError:
        return "Speech Recognition API unavailable."

def speak_text(text):
    tts = gTTS(text)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp

# ==================== STREAMLIT UI ====================

st.title("🎤 Intern RAG App (Gemini + Pinecone + Voice)")

# Train once
if "trained" not in st.session_state:
    st.write("📄 Extracting PDF...")
    pdf_text = extract_pdf_text(pdf_path)
    st.write("🔖 Chunking PDF...")
    chunks = chunk_text(pdf_text)

    try:
        index.delete(delete_all=True)
        st.write("Old vectors cleared from Pinecone.")
    except Exception as e:
        st.warning(f"Couldn't clear Pinecone index: {e}")
    st.success("🧹 Old Pinecone vectors cleared.")

    st.write("📤 Uploading chunks to Pinecone...")
    upload_to_pinecone(chunks)

    st.session_state.trained = True
    st.success("✅ PDF Ready! Start asking your questions!")

# Input options
st.subheader("💬 Ask a question (Text or Voice)")

col1, col2 = st.columns([2, 1])
with col1:
    user_input = st.text_input("Type your question here:")
with col2:
    use_voice = st.button("🎙️ Voice Input")

if use_voice:
    voice_input = listen_to_voice()
    st.session_state["user_input"] = voice_input  # Save voice input to session
    st.write(f"🗣️ You said: **{voice_input}**")

# Recover input value from session if exists
user_input = st.session_state.get("user_input", "")

# Generate and speak response
if st.button("Submit") and user_input.strip():
    with st.spinner("✨ Thinking..."):
        answer = answer_question(user_input)
        st.write("🧠 **Gemini says:**")
        st.success(answer)

        st.audio(speak_text(answer), format="audio/mp3")

    # Clear the input to prevent repeat on rerun
    st.session_state["user_input"] = ""

