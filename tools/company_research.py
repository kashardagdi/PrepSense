
import os

from dotenv import load_dotenv
from tavily import TavilyClient
from llm import ask_ai

# Load variables from the project's .env file
load_dotenv()

# Read the API key securely
api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError(
        "TAVILY_API_KEY not found. Check your .env file."
    )

# Create the Tavily client
tavily = TavilyClient(api_key=api_key)


def search_company(company_name: str) -> dict:
    """Search the web for useful information about a company."""

    if not company_name.strip():
        raise ValueError("Company name cannot be empty.")

    response = tavily.search(
        query=f"{company_name} company overview products technology",
        search_depth="basic",
        max_results=5,
    )

    return response

def summarize_company_research(search_results: dict) -> str:
    """Summarize Tavily results into a company research profile."""

    results = search_results.get("results", [])

    if not results:
        return "No company research results were found."

    research_text = ""

    for result in results:
        research_text += (
            f"\nTitle: {result.get('title', '')}\n"
            f"URL: {result.get('url', '')}\n"
            f"Content: {result.get('content', '')}\n"
        )

    prompt = f"""
    You are a company research assistant for PrepSense,
    an interview preparation system.

    Summarize the supplied web search results into these sections:
    1. Company overview
    2. Main products and services
    3. Important technology areas
    4. Potential interview preparation topics

    Use only information supported by the supplied results.
    Label potential interview topics as suggestions, not facts.
    Do not invent company information.
    Keep the summary concise and include relevant source URLs.

    Research results:
    {research_text}
    """

    return ask_ai(prompt)



if __name__ == "__main__":
    results = search_company("Microsoft")
    summary = summarize_company_research(results)

    print("\nCOMPANY RESEARCH PROFILE")
    print("=" * 50)
    print(summary)
