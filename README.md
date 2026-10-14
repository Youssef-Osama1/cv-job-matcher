# CV Job Matcher

Match a CV against a job description with an LLM and a transparent score.

Send a CV and a job description and get back which requirements the CV meets, with evidence,
what is missing, a 0-100 score and a match level.

## How It Works

1. **Analyze**: the model fills `MatchAnalysis`: every requirement in the job description,
   whether it is required or nice to have, and a phrase copied from the CV as evidence.
2. **Verify**: evidence that does not appear in the CV is dropped, so the model cannot invent skills.
3. **Score**: Python computes the score. Required skills weigh 2, nice-to-haves weigh 1.
   The level is `strong` at 75+ with no missing required skill and enough years,
   `partial` at 50+, otherwise `weak`.

The model only judges skills, experience and qualifications. Personal details such as name,
age, gender and nationality are ignored, and the evals check that they do not change the result.

## Quick Start

```bash
uv sync
cp .env.example .env    # add your LLM_API_KEY
uv run uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs.

## Usage

```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"cv": "Backend Engineer, 2021 - present. Built APIs in Python with FastAPI and PostgreSQL.", "job_description": "Backend Engineer. Requirements: Python, FastAPI, PostgreSQL, Docker. Nice to have: Redis."}'
```

| Status | Meaning |
|--------|---------|
| 200 | Match result |
| 422 | Missing, empty or too long text, or the texts are not a CV and a job description |
| 502 | The model returned output that does not match the schema |

## Development

```bash
uv run pytest                                        # tests, no network access
uv run python -m evals.run_match                     # evals against the real model
uv run python -m playground.try_match                # one CV and job through the service
```

The evals run every case in `evals/match_cases.jsonl` three times and print the pass rate for
the match level, expected matched and missing skills, and fairness (the same CV with different
personal details must get the same level and score). Run them after changing the prompt,
the schema, the scoring or the model.

## Project Structure

```text
├── app/
│   ├── api/          # Routes, dependencies and request/response models
│   ├── config/       # Settings loaded from .env
│   ├── core/         # Logging and exceptions
│   ├── prompts/      # Match prompt
│   ├── schemas/      # Pydantic models the LLM fills in and the match result
│   ├── services/     # LLM client, match service and scoring
│   └── main.py       # FastAPI app entry point
├── docker/           # Docker configurations
├── docs/             # Documentation files
├── evals/            # Eval cases and runner for output quality
├── playground/       # Experimental code, never imported by app/
├── tests/            # Tests that run without network access
├── .env.example      # Environment variables template
├── pyproject.toml    # Project dependencies and metadata
└── uv.lock           # Locked dependencies
```
