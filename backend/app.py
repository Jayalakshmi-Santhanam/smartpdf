from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from gradio_client import Client, handle_file
import tempfile
import shutil

# =========================
# FASTAPI APP
# =========================
app = FastAPI(title="Smart PDF Contract Analyzer Backend")

# =========================
# CORS CONFIG
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # change to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# GRADIO CLIENT
# =========================
GRADIO_SPACE = "Jayalakshmi31/smartpdf"
gradio_client = Client(GRADIO_SPACE)

# =========================
# INDEX DOCUMENT API
# =========================
@app.post("/index")
async def index_document(pdf: UploadFile = File(...)):
    """
    Upload PDF → Index in Gradio Space
    """
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        shutil.copyfileobj(pdf.file, temp_file)
        temp_path = temp_file.name

    # Call Gradio Space
    result = gradio_client.predict(
        pdf_file=handle_file(temp_path),
        api_name="/index_document"
    )

    return {
        "status": "success",
        "message": result
    }

# =========================
# CHAT API
# =========================
@app.post("/chat")
async def chat_contract(question: str):
    """
    Ask question → Get clause analysis
    """
    result = gradio_client.predict(
        question=question,
        api_name="/chat_with_contract"
    )

    return {
        "status": "success",
        "answer": result
    }
