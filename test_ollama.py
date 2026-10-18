
from langchain_ollama import ChatOllama

# Connect Python to your local Ollama model
llm = ChatOllama(
    model="qwen3:8b",
    temperature=0.2,
)

# Send a prompt
response = llm.invoke(
    "Explain what an AI interview preparation system does in 3 sentences."
)

# Display the response
print(response.content)
