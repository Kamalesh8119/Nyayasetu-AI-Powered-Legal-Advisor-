import asyncio
from cachetools import TTLCache
from app.services.retriever import retrieve
from app.services.llm import get_llm



llm = get_llm()

semaphore = asyncio.Semaphore(5)
cache = TTLCache(maxsize=100, ttl=300)


ACT_NAMES = {
    "constitution": "Constitution of India",
    "bns":          "Bharatiya Nyaya Sanhita (BNS), 2023",
    "bnss":         "Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023",
    "crpc":         "Code of Criminal Procedure (CrPC)",
    "cpc":          "Code of Civil Procedure (CPC)",
    "ida":          "Indian Divorce Act, 1869",
    "mva":          "Motor Vehicles Act (MVA)",
    "iea":          "Indian Evidence Act (IEA)",
    "nia":          "Negotiable Instruments Act (NIA)",
}


def build_prompt(query, context_chunks):
    context_text = ""

    for chunk in context_chunks:
        act = ACT_NAMES.get(chunk["type"], chunk["type"])
        title = f" - {chunk['title']}" if chunk["title"] else ""
        context_text += f"[{act}] {chunk['id']}{title}\n{chunk['text']}\n\n"

    return f"""
You are a legal assistant AI for Indian law (BNS = Bharatiya Nyaya Sanhita, 2023).

Use the following legal context to answer the question clearly and accurately.

Context:
{context_text}

Question:
{query}

Instructions:
- Answer based only on the context
- If the context does not contain the relevant provision, say the knowledge base does not cover it; never invent section numbers
- Mention article/section numbers exactly as given in the context, with the act name
- The BNS replaced the IPC with new section numbers; if the question cites an IPC section, give the BNS section from the context and note the old IPC number
- Keep answer short (max 4-5 lines)
- Avoid unnecessary explanation
"""



async def generate_answer(query):
    key = query.lower().strip()

    
    if key in cache:
        print("[CACHE HIT]")
        return cache[key]

    async with semaphore:  
        retries = 3

        for attempt in range(retries):
            try:
             
                context_chunks = await asyncio.to_thread(retrieve, key)
                context_chunks = context_chunks[:3]

                if not context_chunks:
                    return "No relevant legal information found."

                
                prompt = build_prompt(key, context_chunks)

             
                response = await llm.ainvoke(prompt)
                answer = response.content

           
                cache[key] = answer

                return answer

            except Exception as e:
           
                if "429" in str(e):
                    wait = 2
                    print(f"[RETRY] Rate limited. Waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    import traceback
                    print("ERROR:", traceback.format_exc())
                    return f"Error: {str(e)}"

        return "Rate limit exceeded. Please try again later."