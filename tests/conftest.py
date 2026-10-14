import os

os.environ.setdefault("OPENAI_API_KEY", "fake-key")
os.environ.setdefault("JUDGE_MODEL", "gpt-4o")
os.environ.setdefault("PASS_THRESHOLD", "0.7")

from datetime import datetime, timezone  # noqa: E402

import pytest  # noqa: E402

from evalbench.models import EvalRun, Scenario, ScenarioResult  # noqa: E402


@pytest.fixture
def sample_scenario():
    return Scenario(
        id="SC-001",
        description="Test warranty check",
        input_message="Is my machine under warranty?",
        expected_behaviour="Agent looks up account and gives warranty status.",
        tags=["happy_path"],
        should_use_tools=["lookup_account"],
    )


@pytest.fixture
def sample_run():
    results = [
        ScenarioResult(
            scenario_id="SC-001",
            agent_response="Your warranty is valid.",
            tools_called=["lookup_account"],
            judge_score=0.9,
            judge_rationale="Good",
            passed=True,
            latency_ms=500,
            run_id="r1",
        ),
        ScenarioResult(
            scenario_id="SC-002",
            agent_response="I cannot help.",
            tools_called=[],
            judge_score=0.3,
            judge_rationale="Poor",
            passed=False,
            latency_ms=300,
            run_id="r1",
        ),
    ]
    return EvalRun(
        run_id="r1",
        agent_name="test",
        scenario_set="test",
        timestamp=datetime.now(timezone.utc),
        results=results,
    )
