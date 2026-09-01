import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from answer import ask_gemini, retrieve_and_rerank
from chunk import create_overlapping_chunks, create_text_chunks
from config import CORS_ORIGINS, MAX_UPLOAD_BYTES
from index import index_documents
from transcribe import transcribe_meeting

app = FastAPI(title="Civic Watchdog API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    query: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Civic Watchdog API",
        "routes": ["/api/health", "/api/ask", "/api/ingest"],
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask(request: AskRequest, x_session_id: str = Header(...)):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Please enter a question.")
    try:
        chunks = retrieve_and_rerank(query, session_id=x_session_id)
        answer = ask_gemini(query, chunks)
    except Exception as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    citations = [
        {
            "source": chunk[2].get("source", "Unknown source"),
            "start": chunk[2].get("start", 0),
            "end": chunk[2].get("end"),
            "text": chunk[1],
        }
        for chunk in chunks
    ]
    return {"answer": answer, "citations": citations}


def process_upload(file_bytes, filename, suffix, session_id):
    if suffix in {".txt", ".md"}:
        text = file_bytes.decode("utf-8", errors="replace").strip()
        if not text:
            raise ValueError("The transcript is empty.")
        chunks = create_text_chunks(text)
    else:
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(file_bytes)
                temp_path = temp_file.name
            segments = transcribe_meeting(temp_path)
            chunks = create_overlapping_chunks(segments)
            if not chunks:
                raise ValueError("No speech was found in the file.")
        finally:
            if temp_path:
                os.unlink(temp_path)

    index_documents(chunks, source_name=filename, session_id=session_id)
    return chunks


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...), x_session_id: str = Header(...)):
    filename = Path(file.filename or "upload").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".mp3", ".mp4", ".wav", ".m4a", ".webm", ".mov"}:
        raise HTTPException(status_code=400, detail="Upload a transcript or supported audio/video file.")

    upload_id = str(uuid.uuid4())
    try:
        file_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(file_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="The uploaded file is too large.")
        chunks = await run_in_threadpool(process_upload, file_bytes, filename, suffix, x_session_id)
    except HTTPException:
        raise
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Could not index {filename}: {error}") from error

    return {"id": upload_id, "source": filename, "chunks": len(chunks), "status": "indexed"}