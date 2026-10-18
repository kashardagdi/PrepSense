# PrepSense

### An Agentic AI System for Company-Aware Interview Preparation and Feedback

PrepSense is an AI-powered interview preparation project designed to help candidates prepare for company-specific interviews using job descriptions, resume information, company research, tailored interview questions, and structured feedback on practice answers.

The project uses local large language models and agent-based orchestration to build an interview preparation workflow that can be tested, evaluated, and extended.

## Project Goals

- Research a target company using web search.
- Extract important skills, responsibilities, and seniority from a job description.
- Generate relevant technical and behavioral interview questions.
- Evaluate candidate answers and provide actionable feedback.
- Orchestrate the workflow using LangGraph.
- Provide an easy-to-use interface using Streamlit.
- Evaluate the quality and usefulness of generated questions and feedback.

*Note: These are the project's goals. Individual features are still under development.*

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| LangChain | LLM integration and application components |
| LangGraph | Workflow and agent orchestration |
| Ollama | Running the language model locally |
| Qwen3:8b | Initial local language model |
| Tavily | Planned web-based company research |
| Streamlit | Planned user interface |
| pypdf | Resume PDF text extraction |
| python-dotenv | Loading environment variables |

## Project Structure

```text
PrepSense/
├── agents/             # Agent logic
├── evaluation/         # Evaluation datasets and results
├── tests/              # Tests for project modules
├── tools/              # Reusable project functions
├── .env.example        # Example environment configuration
├── .gitignore          # Files Git should ignore
├── README.md           # Project documentation
├── requirements.txt    # Python dependencies
├── llm.py               # Shared local LLM connection
├── job_parser.py        # Job parsing code
├── test_llm.py          # LLM connection test
└── test_ollama.py       # Initial Ollama test
```

## Prerequisites

Before running PrepSense, install:

- Python 3.10 or a compatible version supported by the project's dependencies.
- Git.
- [Ollama](https://ollama.com/).
- The `qwen3:8b` model through Ollama.

Check your installations:

```powershell
python --version
git --version
ollama --version
```

## Local Setup

### 1. Clone the repository

```powershell
git clone https://github.com/kashardagdi/PrepSense.git
cd PrepSense
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set up Ollama

Install and start Ollama, then download the model if it is not already installed:

```powershell
ollama pull qwen3:8b
```

Check that the model is available:

```powershell
ollama list
```

### 5. Configure environment variables

Copy `.env.example` to `.env` and add your own Tavily API key when required.

Never commit `.env` or publish API keys.

### 6. Test the current LLM connection

```powershell
python test_llm.py
```

This test requires Ollama to be running and the configured model to be available locally.

The complete Streamlit application and multi-agent workflow will be documented here once implemented.

## Team Collaboration

PrepSense is being developed by a team of five.

- Work on a separate feature branch.
- Keep changes focused on your assigned module.
- Test your changes before submitting them.
- Push your branch and open a pull request.
- Review changes before merging into `main`.

Example:

```powershell
git switch -c feature/your-feature
git add .
git commit -m "Describe your changes"
git push -u origin feature/your-feature
```

Then open a pull request on GitHub.

## Security

- Never commit `.env`, passwords, tokens, or API keys.
- Keep `.env.example` limited to placeholder values.
- Do not commit your `.venv/` directory.
- If a secret is accidentally committed, revoke or rotate it; deleting the file alone does not remove it from Git history.

## Project Status

**Current stage:** Initial setup and local LLM integration.

Upcoming milestones include company research, job description parsing, question generation, answer evaluation, LangGraph orchestration, Streamlit integration, and systematic evaluation.

## Contributors

This project is being developed collaboratively by five team members. Contributor names and GitHub profiles will be added as the team is finalized.

## License

No open-source license has been selected yet. Until a license is added, the project remains subject to the default copyright rules.
