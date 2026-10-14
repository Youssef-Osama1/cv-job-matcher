from typing import Annotated

from fastapi import Depends, Request

from app.services.llm_client import LLMClient
from app.services.match_service import MatchService


def get_llm_client(request: Request) -> LLMClient:
    return request.app.state.llm_client


LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]


def get_match_service(llm_client: LLMClientDep) -> MatchService:
    return MatchService(llm_client)


MatchServiceDep = Annotated[MatchService, Depends(get_match_service)]
