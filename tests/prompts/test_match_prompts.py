from app.prompts.match import build_match_prompt


def test_match_prompt_wraps_cv_and_job_in_tags():
    prompt = build_match_prompt("  my cv  ", "  the job  ")

    assert prompt == "<cv>\nmy cv\n</cv>\n\n<job>\nthe job\n</job>"
