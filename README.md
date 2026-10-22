# CV Job Matcher

[![CI](https://github.com/Youssef-Osama1/cv-job-matcher/actions/workflows/ci.yml/badge.svg)](https://github.com/Youssef-Osama1/cv-job-matcher/actions/workflows/ci.yml)

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

## Docker

```bash
docker build -f docker/Dockerfile -t cv-job-matcher .
docker run --rm -p 8000:8000 --env-file .env cv-job-matcher
```

The image installs runtime dependencies only, runs as a non-root user and
listens on `$PORT` (default 8000). `.env` is never copied into the image, so
secrets are passed at run time. Values in `.env` must not be quoted for
`--env-file`.

## CI and Deployment

Every push to `main` and every pull request runs
`.github/workflows/ci.yml`: ruff lint, ruff format check, pytest and a
Docker build.

The app runs on Render as a Docker web service:

| Setting | Value |
|---|---|
| Dockerfile path | `./docker/Dockerfile` |
| Build context | `.` |
| Health check path | `/health` |
| Auto-deploy | After CI checks pass |
| Environment | `LLM_API_KEY` (other settings have defaults) |

## Project Structure

```text
├── .github/          # CI workflow
├── app/
│   ├── api/          # Routes, dependencies and request/response models
│   ├── config/       # Settings loaded from .env
│   ├── core/         # Logging and exceptions
│   ├── prompts/      # Match prompt
│   ├── schemas/      # Pydantic models the LLM fills in and the match result
│   ├── services/     # LLM client, match service and scoring
│   └── main.py       # FastAPI app entry point
├── docker/           # Dockerfile
├── docs/             # Documentation files
├── evals/            # Eval cases and runner for output quality
├── playground/       # Experimental code, never imported by app/
├── tests/            # Tests that run without network access
├── .env.example      # Environment variables template
├── pyproject.toml    # Project dependencies and metadata
└── uv.lock           # Locked dependencies
```
