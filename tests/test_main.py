import json

import pytest

from app.core.exceptions import InvalidMatchInputError, LLMOutputError
from app.main import handle_invalid_match_input, handle_llm_output_error

pytestmark = pytest.mark.anyio


async def test_llm_output_error_becomes_502():
    response = await handle_llm_output_error(None, LLMOutputError("refused"))

    assert response.status_code == 502
    assert json.loads(response.body) == {"detail": "refused"}


async def test_invalid_match_input_becomes_422():
    response = await handle_invalid_match_input(
        None, InvalidMatchInputError("not a CV")
    )

    assert response.status_code == 422
    assert json.loads(response.body) == {"detail": "not a CV"}
