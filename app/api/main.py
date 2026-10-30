import asyncio
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.db.models import create_tables
from app.db.crud import (
    get_cached_response, set_cached_response, save_chat,
    list_sessions, get_session_messages,
)
from app.services.agent import ask_agent, stream_agent

create_tables()
AGENT_TIMEOUT = 90
HISTORY_TURNS = 3  # earlier Q&A pairs sent to the agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"   # ← optional, defaults to anonymous
    session_id: str | None = None  # conversation this message belongs to


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/sessions")
def sessions(user_id: str = "anonymous", limit: int = 50):
    return {"sessions": list_sessions(user_id, limit)}


@app.get("/sessions/{session_id}")
def session_messages(session_id: str, user_id: str = "anonymous"):
    messages = get_session_messages(user_id, session_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"session_id": session_id, "messages": messages}


RATE_LIMIT_MESSAGE = (
    "NyayaSetu is handling too many questions right now (the AI provider's per-minute "
    "limit was reached). Please try again in a few seconds."
)


def user_facing_error(e: Exception) -> str:
    text = str(e)
    if "rate_limit" in text or "429" in text:
        return RATE_LIMIT_MESSAGE
    return text


def load_history(req: ChatRequest) -> list:
    """Earlier (question, answer) pairs of this conversation, for follow-up questions."""
    if not req.session_id:
        return []
    try:
        rows = get_session_messages(req.user_id, req.session_id)[-HISTORY_TURNS:]
        return [(r["query"], r["response"]) for r in rows]
    except Exception as e:
        print(f"[chat] history unavailable: {e}")
        return []


def cached_answer(req: ChatRequest, history: list) -> str | None:
    """Only standalone questions are cached: a follow-up like "what about it?"
    depends on the conversation."""
    if history:
        return None
    try:
        return get_cached_response(req.message)
    except Exception as e:
        print(f"[chat] cache unavailable: {e}")
        return None


def persist(req: ChatRequest, response: str, history: list, cache: bool = True):
    try:
        if cache and not history:
            set_cached_response(req.message, response)
        save_chat(req.user_id, req.message, response, req.session_id)
    except Exception as e:
        print(f"[chat] persist failed: {e}")


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        print(f"[chat] incoming: {req.message[:60]!r}")
        history = load_history(req)

        cached = cached_answer(req, history)
        if cached:
            print("[chat] cache HIT")
            persist(req, cached, history, cache=False)
            return {"response": cached, "cached": True}

        response = await asyncio.wait_for(
            ask_agent(req.message, history),
            timeout=AGENT_TIMEOUT,
        )
        print(f"[chat] response length: {len(response)}")
        persist(req, response, history)
        return {"response": response, "cached": False}

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail=f"Agent timed out after {AGENT_TIMEOUT}s")
    except Exception as e:
        print(f"[chat] ERROR: {e}")
        raise HTTPException(status_code=500, detail=user_facing_error(e))


CACHED_CHUNK_CHARS = 12  # cached answers are replayed in small pieces so they still "type out"


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Stream the answer as newline-delimited JSON events:
    {"type": "token", "text": ...} … then {"type": "done", "cached": bool}
    or {"type": "error", "detail": ...}."""

    def event(**payload) -> str:
        return json.dumps(payload) + "\n"

    async def generate():
        print(f"[chat/stream] incoming: {req.message[:60]!r}")
        history = load_history(req)

        cached = cached_answer(req, history)
        if cached:
            print("[chat/stream] cache HIT")
            for i in range(0, len(cached), CACHED_CHUNK_CHARS):
                yield event(type="token", text=cached[i:i + CACHED_CHUNK_CHARS])
                await asyncio.sleep(0.01)
            persist(req, cached, history, cache=False)
            yield event(type="done", cached=True)
            return

        parts = []
        try:
            async with asyncio.timeout(AGENT_TIMEOUT):
                async for text in stream_agent(req.message, history):
                    parts.append(text)
                    yield event(type="token", text=text)
        except TimeoutError:
            yield event(type="error", detail=f"Agent timed out after {AGENT_TIMEOUT}s")
            return
        except Exception as e:
            print(f"[chat/stream] ERROR: {e}")
            yield event(type="error", detail=user_facing_error(e))
            return

        response = "".join(parts)
        if not response.strip():
            yield event(type="error", detail="The model returned an empty answer; please try again.")
            return
        print(f"[chat/stream] response length: {len(response)}")
        persist(req, response, history)
        yield event(type="done", cached=False)

    return StreamingResponse(generate(), media_type="application/x-ndjson")
