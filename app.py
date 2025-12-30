import gradio as gr
import pdfplumber
import chromadb
from chromadb.utils import embedding_functions
import requests
import uuid
import os
from dotenv import load_dotenv

load_dotenv()
# =========================
# CONFIGURATION
# =========================
OPENROUTER_API_KEY = os.getenv("API_KEY")   # 🔴 keep secret
MODEL_NAME = "nvidia/nemotron-3-nano-30b-a3b:free"

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "contracts"

# =========================
# INITIALIZE CHROMADB
# =========================
client = chromadb.Client(
    settings=chromadb.Settings(
        persist_directory=CHROMA_PATH
    )
)

embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_function
)

DOCUMENT_INDEXED = False

# =========================
# PDF TEXT EXTRACTION
# =========================
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# =========================
# TEXT CHUNKING
# =========================
def chunk_text(text, chunk_size=800, overlap=100):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

# =========================
# INDEX DOCUMENT (CLEAN RESET)
# =========================
def index_document(pdf_file):
    global DOCUMENT_INDEXED, collection

    if pdf_file is None:
        return "❌ Please upload a PDF file."

    # ✅ Proper way to reset data (ChromaDB safe)
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )

    text = extract_text_from_pdf(pdf_file.name)
    chunks = chunk_text(text)

    ids = [str(uuid.uuid4()) for _ in chunks]
    collection.add(documents=chunks, ids=ids)

    DOCUMENT_INDEXED = True

    return f"✅ Document indexed successfully.\nTotal chunks stored: {len(chunks)}"

# =========================
# RETRIEVE RELEVANT CHUNKS
# =========================
def retrieve_relevant_chunks(query, n_results=3):
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0]

# =========================
# OPENROUTER CALL (SAFE)
# =========================
def query_openrouter(context, question):
    prompt = f"""
You are an AI legal contract analysis assistant.

Using ONLY the contract content below, identify and explain the relevant clause.

Contract Content:
{context}

User Question:
{question}

Respond with:
• Clause Name
• Clause Explanation
• Risk Level (Low / Medium / High)
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=60
    )

    data = response.json()

    if "choices" not in data:
        return f"❌ OpenRouter Error:\n{data}"

    return data["choices"][0]["message"]["content"]

# =========================
# CHAT PIPELINE
# =========================
def chat_with_contract(question):
    if not DOCUMENT_INDEXED:
        return "❌ Please upload and index a contract first."

    if question.strip() == "":
        return "❌ Please enter a valid question."

    relevant_chunks = retrieve_relevant_chunks(question)
    return query_openrouter("\n".join(relevant_chunks), question)

# =========================
# GRADIO BLOCKS UI
# =========================
with gr.Blocks(title="Smart PDF Contract Analyzer") as app:

    gr.Markdown("## 📄 Smart PDF Contract Analyzer")
    gr.Markdown("### RAG-Based Enterprise Contract Intelligence System")

    with gr.Tab("📂 Upload & Index Contract"):
        pdf_input = gr.File(
            label="Upload Contract PDF",
            file_types=[".pdf"]
        )
        index_btn = gr.Button("📌 Index Document", variant="primary")
        index_status = gr.Textbox(
            label="Indexing Status",
            interactive=False
        )

        index_btn.click(
            fn=index_document,
            inputs=pdf_input,
            outputs=index_status
        )

    with gr.Tab("💬 Clause Query & Analysis"):
        query_input = gr.Textbox(
            label="Ask a Question",
            placeholder="e.g. Explain termination clause",
            lines=2
        )
        query_btn = gr.Button("🔍 Analyze Clause", variant="primary")
        answer_output = gr.Textbox(
            label="Clause Analysis",
            lines=12
        )

        query_btn.click(
            fn=chat_with_contract,
            inputs=query_input,
            outputs=answer_output
        )

if __name__ == "__main__":
    app.launch()


