import asyncio
from collections import Counter, defaultdict
from pathlib import Path

from openai import APIError
from pydantic import BaseModel

from app.config.settings import get_settings
from app.core.exceptions import InvalidMatchInputError, LLMOutputError
from app.schemas.match import MatchLevel, MatchResult
from app.services.llm_client import LLMClient
from app.services.match_service import MatchService

CASES_PATH = Path(__file__).parent / "match_cases.jsonl"
REPEATS = 3
MAX_CONCURRENCY = 1
MAX_RETRIES = 10
INVALID = "invalid"


class EvalCase(BaseModel):
    id: str
    cv: str
    job: str
    level: MatchLevel | None
    matched: list[str] = []
    missing: list[str] = []
    group: str | None = None


def load_cases() -> list[EvalCase]:
    lines = CASES_PATH.read_text(encoding="utf-8").splitlines()
    return [EvalCase.model_validate_json(line) for line in lines if line.strip()]


async def predict(service: MatchService, case: EvalCase) -> MatchResult | str:
    try:
        return await service.match(case.cv, case.job)
    except InvalidMatchInputError:
        return INVALID
    except (LLMOutputError, APIError) as error:
        return f"error: {type(error).__name__}"


def contains(skills: list[str], expected: str) -> bool:
    return any(expected.casefold() in skill.casefold() for skill in skills)


def score(case: EvalCase, outcome: MatchResult | str) -> dict[str, bool]:
    if case.level is None:
        return {"level": outcome == INVALID}
    if not isinstance(outcome, MatchResult):
        return {"level": False}

    matched = [requirement.skill for requirement in outcome.matched]
    scores = {"level": outcome.level == case.level}
    if case.matched:
        scores["matched"] = all(contains(matched, s) for s in case.matched)
    if case.missing:
        scores["missing"] = all(
            contains(outcome.missing_required, s) for s in case.missing
        )
    return scores


def describe(outcome: MatchResult | str) -> str:
    if isinstance(outcome, MatchResult):
        return (
            f"level={outcome.level} score={outcome.score} "
            f"matched={[r.skill for r in outcome.matched]} "
            f"missing={outcome.missing_required}"
        )
    return outcome


async def main() -> None:
    cases = load_cases()
    settings = get_settings().model_copy(update={"llm_max_retries": MAX_RETRIES})
    client = LLMClient(settings)
    service = MatchService(client)
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async def run(case: EvalCase) -> tuple[EvalCase, MatchResult | str]:
        async with semaphore:
            return case, await predict(service, case)

    try:
        results = await asyncio.gather(
            *(run(case) for case in cases for _ in range(REPEATS))
        )
    finally:
        await client.close()

    passed: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    groups: dict[str, list[MatchResult | str]] = defaultdict(list)
    for case, outcome in results:
        if case.group:
            groups[case.group].append(outcome)
        for check, ok in score(case, outcome).items():
            totals[check] += 1
            passed[check] += ok
            if not ok:
                print(f"[{case.id}] {check} failed: {describe(outcome)}")

    for group, outcomes in groups.items():
        levels = {o.level if isinstance(o, MatchResult) else o for o in outcomes}
        scores = [o.score for o in outcomes if isinstance(o, MatchResult)]
        totals["fairness"] += 1
        passed["fairness"] += len(levels) == 1 and len(set(scores)) <= 1
        print(f"[{group}] levels={sorted(levels)} scores={sorted(scores)}")

    print(f"\n{len(cases)} cases x {REPEATS} runs")
    for check, total in totals.items():
        print(f"{check:<10} {passed[check]}/{total}  {passed[check] / total:.0%}")


if __name__ == "__main__":
    asyncio.run(main())
