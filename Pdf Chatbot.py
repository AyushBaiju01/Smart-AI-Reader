import os
import time
from tqdm import tqdm
from pypdf import PdfReader
import google.generativeai as genai
from pinecone import Pinecone, ServerlessSpec
import streamlit as st

# ==================== CONFIG ====================
# Set your API Keys
os.environ["GOOGLE_API_KEY"] = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"
PINECONE_API_KEY = "pcsk_3VgeYZ_6qwTLfLxXTZZTYqCX8Ea5XhDP4GrFfk7RuPbest7eUTaqKu1W6D38rVFAQW5B3i"
PINECONE_ENV = "us-east-1"
PINECONE_INDEX = "gen-ai"

# Hardcoded PDF path (change this to your actual file location)
pdf_path = r"C:\Users\ayush\Downloads\freefromschool.pdf"

# Initialize Gemini
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
generation_model = genai.GenerativeModel("gemini-1.5-flash")

# Initialize Pinecone 3.x
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if not exists
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

# ==================== STREAMLIT UI ====================

st.title("Intern RAG App (Gemini + Pinecone)")

# Train only once
if "trained" not in st.session_state:
    st.write("Extracting PDF...")
    pdf_text = extract_pdf_text(pdf_path)
    st.write("Chunking PDF...")
    chunks = chunk_text(pdf_text)

    # Clear Pinecone index before uploading new PDF
    index.delete(delete_all=True)
    st.write("Old vectors cleared from Pinecone.")

    st.write("Uploading embeddings to Pinecone...")
    upload_to_pinecone(chunks)

    st.session_state.trained = True
    st.success("PDF successfully embedded & ready!")

# Once trained, allow user to query
user_input = st.text_input("Ask your question:")
if st.button("Submit") and user_input:
    with st.spinner("Generating answer..."):
        result = answer_question(user_input)
        st.write(result)
