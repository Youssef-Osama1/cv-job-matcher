import pytest

from app.config.settings import Settings
from app.schemas.match import MatchAnalysis, Requirement


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def settings():
    return Settings(_env_file=None, llm_api_key="test-key", llm_model="test-model")


@pytest.fixture
def cv_text():
    return "Backend developer.\nBuilt APIs in Python with  FastAPI for 4 years."


@pytest.fixture
def analysis():
    return MatchAnalysis(
        inputs_valid=True,
        job_title="Backend Engineer",
        requirements=[
            Requirement(skill="Python", required=True, evidence="APIs in Python"),
            Requirement(skill="FastAPI", required=True, evidence="with FastAPI"),
            Requirement(skill="Redis", required=False, evidence=None),
        ],
        required_years=3,
        candidate_years=4,
        summary="Good fit on the core backend stack.",
    )
