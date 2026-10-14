from typing import Annotated

from pydantic import BaseModel, StringConstraints

CVText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=15_000)
]
JobText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=8_000)
]


class MatchRequest(BaseModel):
    cv: CVText
    job_description: JobText
