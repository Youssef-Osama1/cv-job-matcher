import asyncio

from app.config.settings import get_settings
from app.core.logger import setup_logging
from app.services.llm_client import LLMClient
from app.services.match_service import MatchService

CV = """\
Nour Khaled - Backend Engineer
Cairo, Egypt

Experience
Backend Engineer, Fawry (2022 - present)
- Built payment APIs in Python with FastAPI serving 2M requests a day
- Designed PostgreSQL schemas and tuned slow queries
- Containerized services with Docker and deployed them on AWS ECS

Junior Developer, Instabug (2021 - 2022)
- Maintained internal tools in Python and Flask

Skills: Python, FastAPI, Flask, PostgreSQL, Docker, AWS, Git
"""

JOB = """\
Backend Engineer (Python)

Requirements:
- 3+ years of professional backend experience
- Strong Python and FastAPI
- PostgreSQL
- Docker

Nice to have:
- Redis
- AWS
"""


async def main() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    llm_client = LLMClient(settings)
    try:
        result = await MatchService(llm_client).match(CV, JOB)
        print(result.model_dump_json(indent=2))
    finally:
        await llm_client.close()


asyncio.run(main())
