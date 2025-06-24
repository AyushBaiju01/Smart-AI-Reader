import os
import time
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import streamlit as st
import speech_recognition as sr
from gtts import gTTS
from io import BytesIO

st.set_page_config(page_title="📺 YouTube Q&A (Voice + Gemini + Pinecone)", layout="centered")

# ============ CONFIG ============
os.environ["GOOGLE_API_KEY"] = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"
PINECONE_API_KEY = "pcsk_3VgeYZ_6qwTLfLxXTZZTYqCX8Ea5XhDP4GrFfk7RuPbest7eUTaqKu1W6D38rVFAQW5B3i"
PINECONE_ENV = "us-east-1"
PINECONE_INDEX = "youtube"

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
generation_model = genai.GenerativeModel("gemini-1.5-flash")
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create Pinecone index if not exists
if PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=PINECONE_INDEX,
        dimension=768,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region=PINECONE_ENV)
    )
    time.sleep(2)

index = pc.Index(PINECONE_INDEX)

# ============ FUNCTIONS ============

def get_video_id(youtube_url):
    import re
    match = re.search(r"(?:v=|youtu\.be/)([\w-]+)", youtube_url)
    return match.group(1) if match else None

def fetch_transcript(video_id):
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    text = " ".join([t['text'] for t in transcript])
    return text

def chunk_text(text, chunk_size=500, overlap=50):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size - overlap)]

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

def search_pinecone(query, top_k=3):
    query_embedding = embed_text(query)
    response = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    contexts = [match['metadata']['text'] for match in response['matches']]
    return "\n".join(contexts)

def answer_question(user_question):
    context = search_pinecone(user_question)
    if not context:
        return "No relevant context found."
    prompt = f"Use the following transcript context to answer the question:\n\n{context}\n\nQuestion: {user_question}"
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

# ============ STREAMLIT UI ============

st.title("📺 YouTube Q&A Chatbot (Gemini + Pinecone + Voice)")

# YouTube URL input
youtube_url = st.text_input("Paste YouTube Video URL:")

if youtube_url and st.button("🚀 Process Video"):
    with st.spinner("📥 Fetching transcript..."):
        video_id = get_video_id(youtube_url)
        if not video_id:
            st.error("Invalid YouTube URL.")
        else:
            try:
                transcript = fetch_transcript(video_id)
                st.success("Transcript fetched successfully!")

                st.write("🔖 Chunking...")
                chunks = chunk_text(transcript)

                try:
                    index.delete(delete_all=True)
                    st.success("🧹 Pinecone index cleared.")
                except Exception as e:
                    st.warning(f"Couldn't clear index: {e}")

                with st.spinner("📤 Uploading to Pinecone..."):
                    upload_to_pinecone(chunks)
                    st.session_state["video_ready"] = True
            except Exception as e:
                st.error(f"Failed to fetch transcript: {e}")

# Input area
if st.session_state.get("video_ready"):
    st.subheader("💬 Ask a question (Text or Voice)")

    col1, col2 = st.columns([2, 1])
    with col1:
        typed_input = st.text_input("Type your question here:")
    with col2:
        use_voice = st.button("🎙️ Voice Input")

    if use_voice:
        voice_input = listen_to_voice()
        st.session_state["user_input"] = voice_input
        st.write(f"🗣️ You said: **{voice_input}**")

    user_input = st.session_state.get("user_input", typed_input)

    if st.button("Submit") and user_input.strip():
        with st.spinner("✨ Thinking..."):
            answer = answer_question(user_input)
            st.write("🧠 **Gemini says:**")
            st.success(answer)
            st.audio(speak_text(answer), format="audio/mp3")

        st.session_state["user_input"] = ""
