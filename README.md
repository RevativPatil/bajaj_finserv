# bajaj_finserv
                ┌───────────────────────────┐
                │   1️⃣ User Uploads File   │
                │ (PDF, DOCX, TXT)          │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ 2️⃣ Extract Text          │
                │ - PDF → PyPDF2 / pdfplumber│
                │ - DOCX → python-docx      │
                │ - TXT → direct read        │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ 3️⃣ Chunking              │
                │ Text is split into small  │
                │ overlapping segments      │
                │ (e.g., 500 tokens)        │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ 4️⃣ Embedding Generation  │
                │ SentenceTransformer model │
                │ converts chunks → vectors │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ 5️⃣ Store in Vector DB    │
                │ ChromaDB saves:           │
                │ - chunk text              │
                │ - embeddings              │
                │ - unique IDs              │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ 6️⃣ User Asks Question    │
                │ via chat interface        │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ 7️⃣ Retrieve Relevant Data │
                │ Vector search compares    │
                │ embeddings → returns top  │
                │ matching chunks           │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ 8️⃣ LLM (Gemini) Response │
                │ Gemini generates answer   │
                │ STRICTLY based on found   │
                │ document context          │
                │ (No guessing / No external│
                │ knowledge allowed)        │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │     🔟 Final Output       │
                │ Answer is displayed with  │
                │ formatting + stored in    │
                │ chat history              │
                └───────────────────────────┘
