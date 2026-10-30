from app.services.retriever import retrieve
import asyncio
from app.services.rag_pipeline import ACT_NAMES

def search_legal_docs(query: str):
    """Return the most relevant statute sections, labelled with their act, for the
    agent to answer from directly (no intermediate LLM call)."""
    results = retrieve(query)

    if not results:
        return "No relevant legal information found."

    formatted = ""
    for r in results:
        act = ACT_NAMES.get(r["type"], r["type"])
        # stored chunks read "passage: <id>: <title>. <text>"; BNS titles were missing ("None")
        text = r["text"].removeprefix("passage: ").replace(f"{r['id']}: None. ", "")
        formatted += f"[{act}] {r['id']}\n{text}\n\n"

    return formatted

def simplify_legal_text(text: str):
    return f"Explain this legal text in simple words:\n{text}"

async def search_legal_docs_async(query: str):
    return await asyncio.to_thread(search_legal_docs, query)


async def simplify_legal_text_async(text: str):
    return await asyncio.to_thread(simplify_legal_text, text)