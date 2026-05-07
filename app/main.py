import os
import base64
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


APP_NAME = os.getenv("APP_NAME", "Cloud Notes")
DATABASE_URL = os.getenv("DATABASE_URL")
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title=APP_NAME, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Note(BaseModel):
    id: int
    name: str
    message: str
    created_at: datetime


class CreateNote(BaseModel):
    name: str
    message: str


class UploadRequest(BaseModel):
    filename: str
    content_type: Optional[str] = "application/octet-stream"
    content_base64: str


def get_db_connection():
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="DATABASE_URL is not configured")
    import psycopg

    return psycopg.connect(DATABASE_URL)


def init_db() -> None:
    if not DATABASE_URL:
        return
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        conn.commit()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.get("/ready")
def ready() -> dict[str, str]:
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ready"}


@app.get("/api/notes", response_model=list[Note])
def list_notes() -> list[Note]:
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT id, name, message, created_at FROM notes ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
    return [
        Note(id=row[0], name=row[1], message=row[2], created_at=row[3])
        for row in rows
    ]


@app.post("/api/notes", response_model=Note)
def create_note(payload: CreateNote) -> Note:
    with get_db_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO notes (name, message)
            VALUES (%s, %s)
            RETURNING id, name, message, created_at
            """,
            (payload.name, payload.message),
        ).fetchone()
        conn.commit()
    return Note(id=row[0], name=row[1], message=row[2], created_at=row[3])


@app.post("/api/upload")
async def upload_file(payload: UploadRequest) -> dict[str, Optional[str]]:
    if not S3_BUCKET:
        raise HTTPException(status_code=500, detail="S3_BUCKET is not configured")

    key = f"uploads/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{payload.filename}"
    body = base64.b64decode(payload.content_base64)
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    s3 = boto3.client("s3", region_name=AWS_REGION)

    try:
        s3.put_object(Bucket=S3_BUCKET, Key=key, Body=body, ContentType=payload.content_type)
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(status_code=500, detail="upload failed") from exc

    return {"bucket": S3_BUCKET, "key": key}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Cloud Notes</title>
      <style>
        :root { color-scheme: light; font-family: Inter, system-ui, Arial, sans-serif; }
        body { margin: 0; background: #f7f8fb; color: #18212f; }
        header { background: #17324d; color: white; padding: 32px 20px; }
        main { max-width: 980px; margin: 0 auto; padding: 24px 20px 48px; }
        h1 { margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }
        .lead { margin: 0; max-width: 720px; color: #dce8f4; line-height: 1.55; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }
        section, article { background: white; border: 1px solid #dce3ea; border-radius: 8px; padding: 18px; }
        label { display: block; margin: 12px 0 6px; font-weight: 700; }
        input, textarea { box-sizing: border-box; width: 100%; border: 1px solid #b9c4d0; border-radius: 6px; padding: 11px; font: inherit; }
        textarea { min-height: 110px; resize: vertical; }
        button { margin-top: 12px; border: 0; border-radius: 6px; background: #0f766e; color: white; padding: 11px 14px; font-weight: 800; cursor: pointer; }
        button:hover { background: #0b5f59; }
        .note { margin-top: 12px; border-top: 1px solid #edf1f5; padding-top: 12px; }
        .muted { color: #5d6b7a; font-size: 14px; }
        .status { display: inline-block; border-radius: 999px; background: #d7f7eb; color: #075846; padding: 4px 10px; font-weight: 800; }
      </style>
    </head>
    <body>
      <header>
        <main>
          <span class="status">AWS production-like demo</span>
          <h1>Cloud Notes</h1>
          <p class="lead">A small FastAPI web app for storing team notes and testing file uploads. It is intentionally simple, so the DevOps infrastructure is the focus.</p>
        </main>
      </header>
      <main class="grid">
        <section>
          <h2>Add a note</h2>
          <form id="note-form">
            <label for="name">Name</label>
            <input id="name" name="name" required maxlength="120" />
            <label for="message">Message</label>
            <textarea id="message" name="message" required></textarea>
            <button type="submit">Save note</button>
          </form>
        </section>
        <section>
          <h2>Upload a file</h2>
          <form id="upload-form">
            <label for="file">File</label>
            <input id="file" name="file" type="file" required />
            <button type="submit">Upload to S3</button>
          </form>
          <p id="upload-result" class="muted"></p>
        </section>
        <article style="grid-column: 1 / -1;">
          <h2>Recent notes</h2>
          <div id="notes" class="muted">Loading notes...</div>
        </article>
      </main>
      <script>
        async function loadNotes() {
          const target = document.getElementById('notes');
          const response = await fetch('/api/notes');
          const notes = await response.json();
          target.innerHTML = notes.length ? notes.map(note => `
            <div class="note"><strong>${note.name}</strong><p>${note.message}</p><p class="muted">${new Date(note.created_at).toLocaleString()}</p></div>
          `).join('') : 'No notes yet.';
        }

        document.getElementById('note-form').addEventListener('submit', async event => {
          event.preventDefault();
          const data = Object.fromEntries(new FormData(event.target).entries());
          await fetch('/api/notes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
          });
          event.target.reset();
          loadNotes();
        });

        document.getElementById('upload-form').addEventListener('submit', async event => {
          event.preventDefault();
          const file = document.getElementById('file').files[0];
          const reader = new FileReader();
          reader.onload = async () => {
            const response = await fetch('/api/upload', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                filename: file.name,
                content_type: file.type || 'application/octet-stream',
                content_base64: reader.result.split(',')[1]
              })
            });
            const result = await response.json();
            document.getElementById('upload-result').textContent = result.key ? `Uploaded as ${result.key}` : result.detail;
          };
          reader.readAsDataURL(file);
        });

        loadNotes();
      </script>
    </body>
    </html>
    """
