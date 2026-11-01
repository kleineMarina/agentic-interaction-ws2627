# agentic-interaction-ws2627

Exercise for the course Agentic Human-AI Interaction (Ulm University, WS 2026/27).

## What it does

A command-line agent that answers questions about a mock calendar.
The language model decides to call a tool that fetches the appointments
of one day from the course data repository, then answers based on the result
(model → tool → model). Every run writes a JSONL log to `logs/`.

## Setup

Requires Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the repository root:

```
OPENAI_BASE_URL=https://api.groq.com/openai/v1
MODEL=openai/gpt-oss-20b
OPENAI_API_KEY=your-key
DATA_BASE_URL=https://jhbelz.github.io/agentic-interaction-data/v1
```

Environment variables override values in `.env`.

## Run

From the repository root:

```bash
python -m agent "Was steht am 29.10.2026 im Kalender?"
```

The answer is printed to standard output. The log for the run is in `logs/`.
