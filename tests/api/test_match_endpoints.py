from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_match_service
from app.core.exceptions import InvalidMatchInputError, LLMOutputError
from app.main import app
from app.schemas.match import MatchLevel, MatchResult
from app.services.match_service import MatchService

VALID_BODY = {"cv": "my cv", "job_description": "the job"}


@pytest.fixture
def match_result(analysis):
    return MatchResult(
        job_title=analysis.job_title,
        score=80,
        level=MatchLevel.STRONG,
        matched=analysis.requirements[:2],
        missing_required=[],
        missing_nice_to_have=["Redis"],
        required_years=analysis.required_years,
        candidate_years=analysis.candidate_years,
        summary=analysis.summary,
    )


@pytest.fixture
def service(match_result):
    fake = AsyncMock(spec=MatchService)
    fake.match.return_value = match_result
    app.dependency_overrides[get_match_service] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_match_returns_result(client, service, match_result):
    response = client.post("/match", json=VALID_BODY)

    assert response.status_code == 200
    assert response.json() == match_result.model_dump(mode="json")
    service.match.assert_awaited_once_with("my cv", "the job")


@pytest.mark.parametrize(
    "body",
    [
        {"cv": "my cv"},
        {"cv": "   ", "job_description": "the job"},
        {"cv": "x" * 15_001, "job_description": "the job"},
        {"cv": "my cv", "job_description": "x" * 8_001},
    ],
)
def test_invalid_body_is_rejected_before_the_service(client, service, body):
    response = client.post("/match", json=body)

    assert response.status_code == 422
    service.match.assert_not_awaited()


def test_texts_that_are_not_a_cv_and_job_return_422(client, service):
    service.match.side_effect = InvalidMatchInputError("not a CV")

    response = client.post("/match", json=VALID_BODY)

    assert response.status_code == 422
    assert response.json() == {"detail": "not a CV"}


def test_bad_model_output_returns_502(client, service):
    service.match.side_effect = LLMOutputError("did not match MatchAnalysis")

    response = client.post("/match", json=VALID_BODY)

    assert response.status_code == 502
    assert response.json() == {"detail": "did not match MatchAnalysis"}
