from enum import StrEnum

from pydantic import BaseModel, Field


class MatchLevel(StrEnum):
    STRONG = "strong"
    PARTIAL = "partial"
    WEAK = "weak"


class Requirement(BaseModel):
    skill: str = Field(
        description="One skill, tool or qualification from the job description, "
        "named as the job description names it"
    )
    required: bool = Field(
        description="True if the job description says it is required, "
        "false if it is a nice-to-have"
    )
    evidence: str | None = Field(
        description="A short phrase copied word for word from the CV that shows "
        "the candidate has this skill, null if the CV does not show it"
    )


class MatchAnalysis(BaseModel):
    inputs_valid: bool = Field(
        description="False if the first text is not a CV or the second text "
        "is not a job description"
    )
    job_title: str | None = Field(
        description="Job title from the job description, null if not stated"
    )
    requirements: list[Requirement] = Field(
        description="Every distinct skill, tool or qualification the job "
        "description asks for, including nice-to-have items, in the order it lists them"
    )
    required_years: float | None = Field(
        description="Minimum years of experience the job asks for, null if not stated"
    )
    candidate_years: float | None = Field(
        description="Years of relevant professional experience shown in the CV, "
        "null if it cannot be worked out"
    )
    summary: str = Field(
        description="Two sentences on how well the CV fits the job, "
        "based only on skills and experience"
    )


class MatchResult(BaseModel):
    job_title: str | None
    score: int = Field(ge=0, le=100)
    level: MatchLevel
    matched: list[Requirement]
    missing_required: list[str]
    missing_nice_to_have: list[str]
    required_years: float | None
    candidate_years: float | None
    summary: str
