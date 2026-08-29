import os
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from answer import ask_gemini, retrieve_and_rerank
from chunk import create_overlapping_chunks
from index import index_documents
from transcribe import transcribe_meeting

app = FastAPI(title="Civic Watchdog API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    query: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ask")
def ask(request: AskRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Please enter a question.")
    try:
        chunks = retrieve_and_rerank(query)
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


@app.post("/api/ingest")
async def ingest(file: UploadFile = File(...)):
    filename = Path(file.filename or "upload").name
    suffix = Path(filename).suffix.lower()
    if suffix not in {".txt", ".md", ".mp3", ".mp4", ".wav", ".m4a", ".webm", ".mov"}:
        raise HTTPException(status_code=400, detail="Upload a transcript or supported audio/video file.")

    upload_id = str(uuid.uuid4())
    temp_path = None
    try:
        if suffix in {".txt", ".md"}:
            text = (await file.read()).decode("utf-8", errors="replace").strip()
            if not text:
                raise HTTPException(status_code=400, detail="The transcript is empty.")
            chunks = [
                {"text": text, "start_time": 0, "end_time": 0}
            ]
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(await file.read())
                temp_path = temp_file.name
            segments = transcribe_meeting(temp_path)
            chunks = create_overlapping_chunks(segments)
            if not chunks:
                raise HTTPException(status_code=400, detail="No speech was found in the file.")
        index_documents(chunks, source_name=filename)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Could not index {filename}: {error}") from error
    finally:
        if temp_path:
            os.unlink(temp_path)

    return {"id": upload_id, "source": filename, "chunks": len(chunks), "status": "indexed"}