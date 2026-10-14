# CV Job Matcher

Match a CV against a job description with an LLM and a transparent score.

## Quick Start

```bash
uv sync
cp .env.example .env    # add your LLM_API_KEY
uv run uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs.

## Development

```bash
uv run pytest                                        # tests, no network access
uv run ruff check                                    # lint
uv run --env-file .env python playground/first_call.py
```

## Project Structure

```text
├── app/
│   ├── api/          # Routes, dependencies and request/response models
│   ├── config/       # Settings loaded from .env
│   ├── core/         # Logging and exceptions
│   ├── prompts/      # System prompts
│   ├── schemas/      # Pydantic models the LLM fills in
│   ├── services/     # LLM client and business logic
│   └── main.py       # FastAPI app entry point
├── docker/           # Docker configurations
├── docs/             # Documentation files
├── evals/            # Datasets for measuring output quality
├── playground/       # Experimental code, never imported by app/
├── tests/            # Tests that run without network access
├── .env.example      # Environment variables template
├── pyproject.toml    # Project dependencies and metadata
└── uv.lock           # Locked dependencies
```
