import streamlit as st
import os
from PyPDF2 import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv

# -----------------------------
# ⚙️ CONFIGURATION
# -----------------------------
st.set_page_config(
    page_title="AI Document Chatbot 🤖",
    page_icon="https://cdn-icons-png.flaticon.com/512/4712/4712102.png",
    layout="wide"
)

# 🔑 Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 🧩 Embedding model
embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# -----------------------------
# 🧠 CHROMADB SETUP
# -----------------------------
client_chroma = chromadb.PersistentClient(path="./chroma_db")
collection = client_chroma.get_or_create_collection(name="docs_embeddings")

# -----------------------------
# 💬 CHAT HISTORY
# -----------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# 🌈 STYLING
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top left, #0f0f0f 0%, #000000 80%);
    color: white;
}
.block-container {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 3rem;
    margin-top: 2rem;
    box-shadow: 0 0 30px rgba(255,255,255,0.1);
}
h1, h2, h3 { color: #ffffff !important; font-weight: 600; }
p, label { color: #b0b0b0 !important; }
.chat-bubble-user {
    background-color: #ffffff;
    color: #000000;
    padding: 10px;
    border-radius: 10px;
    margin-top: 5px;
}
.chat-bubble-bot {
    background: linear-gradient(90deg, #ff4ec4 0%, #9d00ff 100%);
    color: white;
    padding: 10px;
    border-radius: 10px;
    margin-top: 5px;
}
</style>
<header>
    <img src="https://cdn-icons-png.flaticon.com/512/4712/4712102.png" width="100">
    <h1>🤖 AI Document Chatbot</h1>
    <p>Upload • Summarize • Chat — with a human touch</p>
</header>
""", unsafe_allow_html=True)

# -----------------------------
# 📂 FILE UPLOAD
# -----------------------------
uploaded_files = st.file_uploader("📂 Upload one or more documents",
                                  type=["pdf", "docx", "txt"], accept_multiple_files=True)


# -----------------------------
# 📄 TEXT EXTRACTOR
# -----------------------------
def extract_text(file):
    text = ""
    try:
        if file.name.endswith(".pdf"):
            try:
                pdf_reader = PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            except:
                file.seek(0)
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
        elif file.name.endswith(".docx"):
            doc = Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
        else:
            text = file.read().decode("utf-8")
    except Exception as e:
        st.warning(f"⚠️ Couldn't read {file.name}. Reason: {e}")
    return text


# -----------------------------
# 🧠 PROCESS AND STORE FILES
# -----------------------------
if uploaded_files:
    model = genai.GenerativeModel("gemini-2.0-flash")
    for uploaded_file in uploaded_files:
        with st.spinner(f"🧩 Processing {uploaded_file.name}..."):
            text_data = extract_text(uploaded_file)

            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            chunks = splitter.split_text(text_data)
            embeddings = embed_model.encode(chunks, convert_to_numpy=True).tolist()

            for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                collection.add(
                    ids=[f"{uploaded_file.name}_{i}"],
                    documents=[chunk],
                    embeddings=[emb]
                )

            prompt = f"Summarize this document strictly using its content:\n\n{text_data[:4000]}"
            try:
                response = model.generate_content(prompt)
                summary = response.text.strip()
            except Exception as e:
                summary = f"⚠️ Error generating summary: {e}"

            st.subheader(f"📘 Summary for {uploaded_file.name}:")
            st.markdown(f"<div class='chat-bubble-bot'>{summary}</div>", unsafe_allow_html=True)

    st.success("✅ All files processed and stored!")


# -----------------------------
# 💬 CHAT FUNCTION
# -----------------------------
st.subheader("💬 Ask Anything About Your Documents")
query = st.text_input("Ask here...")


if query:
    results = collection.query(query_texts=[query], n_results=3)
    context = "\n\n".join(results["documents"][0]) if results["documents"] else ""

    if not context.strip():
        answer = "❌ The requested information is not available in the document."
    else:
        prompt = f"""
You are an AI assistant that must answer strictly based on the provided document content.

**Rules:**
- Use ONLY the information found directly in the "Context".
- Do NOT guess, assume, or invent information.
- If the context does not clearly contain the answer, respond EXACTLY with:
  "❌ The requested information is not available in the document."
- If the context includes partial information, respond with:
  "⚠️ Partial information found:" and then answer only using available content.
- Do not provide external knowledge beyond the document.

---

📄 **Context:**
\"\"\" 
{context}
\"\"\"

❓ **User Query:** "{query}"

Now generate the final grounded answer:
"""

        try:
            response = model.generate_content(prompt)
            answer = response.text.strip()
        except Exception as e:
            answer = f"⚠️ Gemini Error: {str(e)}"


    st.session_state.chat_history.append(("User", query))
    st.session_state.chat_history.append(("Bot", answer))

    st.markdown(f"<div class='chat-bubble-user'><b>You:</b> {query}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='chat-bubble-bot'><b>Bot:</b> {answer}</div>", unsafe_allow_html=True)

# -----------------------------
# 🕒 CHAT HISTORY
# -----------------------------
if st.session_state.chat_history:
    st.subheader("🕒 Chat History")
    for role, msg in st.session_state.chat_history:
        bubble = 'chat-bubble-user' if role == "User" else 'chat-bubble-bot'
        st.markdown(f"<div class='{bubble}'><b>{role}:</b> {msg}</div>", unsafe_allow_html=True)

