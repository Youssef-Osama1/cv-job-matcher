import logging
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import InvalidMatchInputError
from app.prompts.match import MATCH_SYSTEM_PROMPT, build_match_prompt
from app.schemas.match import MatchAnalysis, MatchLevel, Requirement
from app.services.llm_client import LLMClient
from app.services.match_service import (
    MatchService,
    compute_score,
    match_level,
    verified_matches,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def llm_client(analysis):
    client = AsyncMock(spec=LLMClient)
    client.extract.return_value = analysis
    return client


@pytest.fixture
def service(llm_client):
    return MatchService(llm_client)


async def test_match_sends_both_texts_and_schema(service, llm_client, cv_text):
    await service.match(cv_text, "the job")

    llm_client.extract.assert_awaited_once_with(
        prompt=build_match_prompt(cv_text, "the job"),
        schema=MatchAnalysis,
        system=MATCH_SYSTEM_PROMPT,
    )


async def test_match_scores_and_splits_requirements(service, cv_text):
    result = await service.match(cv_text, "the job")

    assert result.score == 80
    assert result.level == MatchLevel.STRONG
    assert [r.skill for r in result.matched] == ["Python", "FastAPI"]
    assert result.missing_required == []
    assert result.missing_nice_to_have == ["Redis"]


async def test_invalid_inputs_raise(service, llm_client, analysis):
    llm_client.extract.return_value = analysis.model_copy(
        update={"inputs_valid": False}
    )

    with pytest.raises(InvalidMatchInputError):
        await service.match("a recipe", "the job")


async def test_job_without_requirements_raises(service, llm_client, analysis):
    llm_client.extract.return_value = analysis.model_copy(update={"requirements": []})

    with pytest.raises(InvalidMatchInputError):
        await service.match("my cv", "the job")


async def test_invented_evidence_counts_as_missing(service, llm_client, analysis):
    invented = Requirement(skill="Docker", required=True, evidence="Docker expert")
    llm_client.extract.return_value = analysis.model_copy(
        update={"requirements": [*analysis.requirements, invented]}
    )

    result = await service.match("Built APIs in Python with FastAPI", "the job")

    assert result.missing_required == ["Docker"]
    assert result.level == MatchLevel.PARTIAL


def test_evidence_check_ignores_case_spacing_and_edge_punctuation(cv_text):
    requirement = Requirement(
        skill="FastAPI", required=True, evidence='"python WITH fastapi."'
    )

    assert verified_matches([requirement], cv_text) == [requirement]


def test_unverified_evidence_logs_warning(caplog):
    requirement = Requirement(skill="Go", required=True, evidence="Go services")

    with caplog.at_level(logging.WARNING):
        assert verified_matches([requirement], "Python only") == []

    assert "skill=Go" in caplog.text


@pytest.mark.parametrize(
    ("matched", "expected"),
    [(set(), 0), ({"Redis"}, 20), ({"Python"}, 40), ({"Python", "FastAPI"}, 80)],
)
def test_required_skills_weigh_double(analysis, matched, expected):
    assert compute_score(analysis.requirements, matched) == expected


@pytest.mark.parametrize(
    ("score", "missing", "required_years", "candidate_years", "expected"),
    [
        (80, [], 3, 4, MatchLevel.STRONG),
        (80, [], None, None, MatchLevel.STRONG),
        (90, ["Docker"], None, None, MatchLevel.PARTIAL),
        (90, [], 5, 2, MatchLevel.PARTIAL),
        (60, [], None, None, MatchLevel.PARTIAL),
        (49, [], None, None, MatchLevel.WEAK),
    ],
)
def test_match_level(score, missing, required_years, candidate_years, expected):
    assert match_level(score, missing, required_years, candidate_years) == expected
