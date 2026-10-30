from app.utils.config import LLM_PROVIDER, LLM_MODEL


# Answers are short (the prompt asks for concise replies); a smaller cap also keeps
# each call's reservation low against Groq's free-tier tokens-per-minute limit.
def get_llm(temperature: float = 0.3, max_tokens: int = 1024):
    """Build the chat model for the configured provider (groq or mistral)."""
    if LLM_PROVIDER == "mistral":
        from langchain_mistralai import ChatMistralAI
        return ChatMistralAI(
            model=LLM_MODEL or "mistral-small-latest",
            temperature=temperature,
            max_tokens=max_tokens,
        )

    from langchain_groq import ChatGroq
    return ChatGroq(
        model=LLM_MODEL or "openai/gpt-oss-120b",
        temperature=temperature,
        max_tokens=max_tokens,
        # gpt-oss is a reasoning model; reasoning tokens count against max_tokens
        reasoning_effort="low",
    )
