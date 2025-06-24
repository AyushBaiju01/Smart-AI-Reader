import os
import streamlit as st
from pinecone import Pinecone
import google.generativeai as genai
from pypdf import PdfReader
from tqdm import tqdm
import time

# ========== API KEYS & ENV VARIABLES ==========
os.environ["GOOGLE_API_KEY"] = "AIzaSyC7xNMObXQ16LlnorwnYhxxm8NfbA8txl8"
PINECONE_API_KEY = "pcsk_3VgeYZ_6qwTLfLxXTZZTYqCX8Ea5XhDP4GrFfk7RuPbest7eUTaqKu1W6D38rVFAQW5B3i"
PINECONE_ENV = "us-east-1"
PINECONE_INDEX = "gen-ai"

# ========== INITIALIZE GEMINI MODEL ==========
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
generation_model = genai.GenerativeModel("gemini-1.5-flash")

# ========== INITIALIZE PINECONE ==========
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

# ========== EXTRACT PDF ==========
def extract_pdf_text(pdf_path):
    try:
        pdf = PdfReader(pdf_path)
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text
    except Exception as e:
        st.error(f"Error extracting PDF: {e}")
        return None

# ========== CHUNKING ==========
def chunk_text(text, chunk_size=500):
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

# ========== EMBEDDING WITH GEMINI 1.5 FLASH ==========
def embed_text(text):
    try:
        response = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return response['embedding']
    except Exception as e:
        st.error(f"Error embedding text: {e}")
        return None

# ========== UPLOAD EMBEDDINGS TO PINECONE ==========
def upload_to_pinecone(chunks, batch_size=20, progress_bar=None, status_text=None):
    vectors = []
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        try:
            embedding = embed_text(chunk)
            vectors.append((f"chunk-{i}", embedding, {"text": chunk}))
            if len(vectors) >= batch_size:
                index.upsert(vectors=vectors)
                vectors = []
            # Update Streamlit progress
            if progress_bar:
                progress_bar.progress((i + 1) / total)
            if status_text:
                status_text.text(f"Uploading chunk {i + 1} of {total}")
        except Exception as e:
            print(f"Error embedding chunk {i}: {e}")
    if vectors:
        index.upsert(vectors=vectors)
    if status_text:
        status_text.text("Upload complete.")

# ========== SEARCH PINECONE ==========
def search_pinecone(query, top_k=3):
    try:
        query_embedding = embed_text(query)
        if not query_embedding:
            return None
        response = index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        matches = response.get('matches', [])
        contexts = [match['metadata']['text'] for match in matches]
        return "\n".join(contexts)
    except Exception as e:
        st.error(f"Error searching Pinecone: {e}")
        return None

# ========== RAG PIPELINE ==========
def answer_question(user_question):
    context = search_pinecone(user_question)
    if not context:
        return "No relevant context found."
    prompt = (
        f"Use the following context to answer the question:\n\n"
        f"{context}\n\n"
        f"Question: {user_question}"
    )
    try:
        response = generation_model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating answer: {e}")
        return "Error generating response."

# ========== PREPROCESS PDF ==========
pdf_path = r"C:\Users\ayush\Downloads\Sell My Dreams.pdf"  # Hardcoded PDF path

if 'pdf_processed' not in st.session_state:
    with st.spinner("Processing PDF..."):
        pdf_text = extract_pdf_text(pdf_path)
        if pdf_text:
            st.session_state['pdf_text'] = pdf_text
            with st.spinner("Chunking and uploading to Pinecone..."):
                chunks = chunk_text(pdf_text)

                # Clear Pinecone index before uploading new PDF
                index.delete(delete_all=True)
                st.write("Old vectors cleared from Pinecone.")

                # Add progress bar and status text
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                st.write("Uploading embeddings to Pinecone...")
                upload_to_pinecone(chunks, batch_size=20, progress_bar=progress_bar, status_text=status_text)
            st.session_state['pdf_processed'] = True

# ========== STREAMLIT UI ==========
st.set_page_config(page_title="PDF Q&A with Pinecone", layout="wide")
st.title("PDF Question Answering System")
st.markdown("Ask questions based on the content of the preloaded PDF using Pinecone and Gemini.")

# Query Section
st.header("Ask a Question")
if 'pdf_processed' in st.session_state:
    query = st.text_input("Enter your question:")
    if st.button("Submit"):
        if query:
            with st.spinner("Generating answer..."):
                answer = answer_question(query)
                st.markdown("### Answer")
                st.write(answer)
        else:
            st.warning("Please enter a question.")
else:
    st.info("Processing PDF, please wait...")