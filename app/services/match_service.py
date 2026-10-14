import logging
import re

from app.core.exceptions import InvalidMatchInputError
from app.prompts.match import MATCH_SYSTEM_PROMPT, build_match_prompt
from app.schemas.match import MatchAnalysis, MatchLevel, MatchResult, Requirement
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

REQUIRED_WEIGHT = 2
NICE_TO_HAVE_WEIGHT = 1
STRONG_SCORE = 75
PARTIAL_SCORE = 50


class MatchService:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def match(self, cv_text: str, job_text: str) -> MatchResult:
        analysis = await self._llm_client.extract(
            prompt=build_match_prompt(cv_text, job_text),
            schema=MatchAnalysis,
            system=MATCH_SYSTEM_PROMPT,
        )
        if not analysis.inputs_valid:
            raise InvalidMatchInputError(
                "The texts do not look like a CV and a job description"
            )
        if not analysis.requirements:
            raise InvalidMatchInputError("The job description lists no requirements")

        matched = verified_matches(analysis.requirements, cv_text)
        matched_skills = {requirement.skill for requirement in matched}
        missing = [r for r in analysis.requirements if r.skill not in matched_skills]
        missing_required = [r.skill for r in missing if r.required]
        score = compute_score(analysis.requirements, matched_skills)
        level = match_level(
            score, missing_required, analysis.required_years, analysis.candidate_years
        )
        logger.info(
            "Matched CV: requirements=%s matched=%s score=%s level=%s",
            len(analysis.requirements),
            len(matched),
            score,
            level,
        )
        return MatchResult(
            job_title=analysis.job_title,
            score=score,
            level=level,
            matched=matched,
            missing_required=missing_required,
            missing_nice_to_have=[r.skill for r in missing if not r.required],
            required_years=analysis.required_years,
            candidate_years=analysis.candidate_years,
            summary=analysis.summary,
        )


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).casefold().strip(" .,;:'\"")


def verified_matches(
    requirements: list[Requirement], cv_text: str
) -> list[Requirement]:
    cv = normalize(cv_text)
    matched = []
    for requirement in requirements:
        if requirement.evidence is None:
            continue
        if normalize(requirement.evidence) in cv:
            matched.append(requirement)
        else:
            logger.warning("Dropped unverified evidence: skill=%s", requirement.skill)
    return matched


def weight(requirement: Requirement) -> int:
    return REQUIRED_WEIGHT if requirement.required else NICE_TO_HAVE_WEIGHT


def compute_score(requirements: list[Requirement], matched_skills: set[str]) -> int:
    total = sum(weight(r) for r in requirements)
    earned = sum(weight(r) for r in requirements if r.skill in matched_skills)
    return round(100 * earned / total)


def match_level(
    score: int,
    missing_required: list[str],
    required_years: float | None,
    candidate_years: float | None,
) -> MatchLevel:
    short_on_experience = (
        required_years is not None
        and candidate_years is not None
        and candidate_years < required_years
    )
    if score >= STRONG_SCORE and not missing_required and not short_on_experience:
        return MatchLevel.STRONG
    if score >= PARTIAL_SCORE:
        return MatchLevel.PARTIAL
    return MatchLevel.WEAK
