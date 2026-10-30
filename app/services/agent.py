from langchain_core.tools import Tool
from langgraph.prebuilt import create_react_agent
from app.services.llm import get_llm
from app.services.tools import search_legal_docs_async, simplify_legal_text_async

tools = [
    Tool(
        name="Legal_Search",
        coroutine=search_legal_docs_async,
        description="Search Indian law (Constitution, BNS/IPC, BNSS/CrPC, CPC, Indian Divorce Act, MVA, Evidence Act, Negotiable Instruments Act). Returns the text of the most relevant sections, each labelled with its act. Input: a focused legal search query.",
        func=lambda x: x,
    ),
    Tool(
        name="Simplify_Legal_Text",
        coroutine=simplify_legal_text_async,
        description="Simplify legal language",
        func=lambda x: x,
    )
]

llm = get_llm()

system_prompt = """You are a legal assistant AI for Indian law. Help users understand legal concepts,
search Indian legal documents, and simplify complex legal language.
The knowledge base covers: the Constitution of India, the Bharatiya Nyaya Sanhita (BNS, which replaced the IPC),
the Bharatiya Nagarik Suraksha Sanhita (BNSS, which replaced the CrPC), the Code of Criminal Procedure (CrPC), the Code of Civil Procedure (CPC), the Indian Divorce Act, 1869 (IDA),
the Motor Vehicles Act (MVA), the Indian Evidence Act (IEA) and the Negotiable Instruments Act (NIA).
"BNS" always means the Bharatiya Nyaya Sanhita, 2023 (India).
The BNS replaced the Indian Penal Code (IPC) with NEW section numbers (e.g. IPC 302 murder = BNS 103).
If the user cites an IPC section, answer with the BNS section from the search results and mention the old IPC number;
never label a BNS provision with an IPC section number.
"BNSS" always means the Bharatiya Nagarik Suraksha Sanhita, 2023, the current criminal procedure law; it renumbered the CrPC.
Never label a BNSS provision with a CrPC section number (or vice versa); cite each with the act shown in the search results.
Always use Legal_Search for legal questions. Answer from the section text it returns and cite those sections/articles with their act.
Labour/employment law (e.g. the Industrial Disputes Act) is NOT in the knowledge base.
Only cite section numbers that appear in the search results. If the results do not cover the question,
say so clearly, and give only general guidance without section numbers.
The knowledge base contains statutes only, not judgments: do not cite court cases or case names.
Keep answers concise."""


agent = create_react_agent(
    model=llm,
    tools=tools,
)

HISTORY_CHARS = 1500  # cap each earlier answer to keep prompts small


OUT_OF_STEPS = "Sorry, need more steps"  # LangGraph's placeholder when the step budget runs out
RECURSION_LIMIT = 12


def build_messages(query: str, history: list | None = None) -> list:
    """history: earlier (question, answer) pairs from this conversation, oldest first."""
    messages = [("system", system_prompt)]
    for past_query, past_response in history or []:
        messages.append(("user", past_query))
        messages.append(("assistant", past_response[:HISTORY_CHARS]))
    messages.append(("user", query))
    return messages


async def ask_agent(query: str, history: list | None = None):
    try:
        result = await agent.ainvoke(
            {"messages": build_messages(query, history)},
            config={"recursion_limit": RECURSION_LIMIT},
        )
        answer = result["messages"][-1].content
        if answer.startswith(OUT_OF_STEPS):
            raise RuntimeError("Agent ran out of reasoning steps; please rephrase the question.")
        return answer
    except Exception:
        import traceback
        print("AGENT ERROR:", traceback.format_exc())
        raise


async def stream_agent(query: str, history: list | None = None):
    """Yield the final answer's text as the LLM generates it.

    Only chunks from the "agent" node are the user-facing answer; the "tools" node
    also streams tokens (the RAG tool's own LLM call), which are internal.
    """
    try:
        async for chunk, meta in agent.astream(
            {"messages": build_messages(query, history)},
            config={"recursion_limit": RECURSION_LIMIT},
            stream_mode="messages",
        ):
            if meta.get("langgraph_node") != "agent" or not isinstance(chunk.content, str):
                continue
            if chunk.content.startswith(OUT_OF_STEPS):
                raise RuntimeError("Agent ran out of reasoning steps; please rephrase the question.")
            if chunk.content:
                yield chunk.content
    except Exception:
        import traceback
        print("AGENT ERROR:", traceback.format_exc())
        raise
