import json
from unittest.mock import AsyncMock, MagicMock

from evalbench.judge import judge_response


async def test_judge_returns_score_rationale_passed(mocker, sample_scenario):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {"score": 0.9, "rationale": "Good response", "passed": True}
    )
    mocker.patch(
        "evalbench.judge.client.chat.completions.create",
        AsyncMock(return_value=mock_response),
    )

    score, rationale, passed = await judge_response(
        sample_scenario, "Your warranty is valid until 2026.", ["lookup_account"]
    )

    assert score == 0.9
    assert rationale == "Good response"
    assert passed is True


async def test_judge_fails_below_threshold(mocker, sample_scenario):
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(
        {"score": 0.4, "rationale": "Incomplete", "passed": False}
    )
    mocker.patch(
        "evalbench.judge.client.chat.completions.create",
        AsyncMock(return_value=mock_response),
    )

    _, _, passed = await judge_response(sample_scenario, "I do not know.", [])

    assert passed is False
