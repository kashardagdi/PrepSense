
from langchain_ollama import ChatOllama

# Create our local language model
llm = ChatOllama(
    model="qwen3:8b",
    temperature=0.2,
)

def ask_ai(prompt: str) -> str:
    """Send a prompt to the local model and return its answer."""
    response = llm.invoke(prompt)
    return response.content
