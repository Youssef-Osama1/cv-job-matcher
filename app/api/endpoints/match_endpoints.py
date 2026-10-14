from fastapi import APIRouter

from app.api.dependencies import MatchServiceDep
from app.api.schemas.match import MatchRequest
from app.schemas.match import MatchResult

router = APIRouter()


@router.post("")
async def match_cv(payload: MatchRequest, service: MatchServiceDep) -> MatchResult:
    return await service.match(payload.cv, payload.job_description)
