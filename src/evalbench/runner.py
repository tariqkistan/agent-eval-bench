import asyncio
import time
import uuid
from datetime import datetime, timezone

from evalbench.judge import judge_response
from evalbench.models import EvalRun, EvalSummary, Scenario, ScenarioResult


async def _run_one(agent, scenario: Scenario, run_id: str) -> ScenarioResult:
    """Run one scenario through the agent and judge the result."""
    start = time.monotonic()

    # 1. Run the agent
    try:
        result = await agent.ainvoke({"input": scenario.input_message})
        response = result.get("output", "")
        # Extract tool names from intermediate steps
        steps = result.get("intermediate_steps", [])
        tools_called = [step[0].tool for step in steps if hasattr(step[0], "tool")]
    except Exception as e:
        response = f"ERROR: {e}"
        tools_called = []

    latency_ms = (time.monotonic() - start) * 1000

    # 2. Judge the response
    score, rationale, passed = await judge_response(scenario, response, tools_called)

    return ScenarioResult(
        scenario_id=scenario.id,
        agent_response=response,
        tools_called=tools_called,
        judge_score=score,
        judge_rationale=rationale,
        passed=passed,
        latency_ms=round(latency_ms, 1),
        run_id=run_id,
    )


async def run_eval(
    agent,
    scenarios: list[Scenario],
    agent_name: str,
    scenario_set: str = "custom",
) -> tuple[EvalRun, EvalSummary]:
    """Run all scenarios concurrently. Returns EvalRun + EvalSummary."""
    run_id = str(uuid.uuid4())[:8]

    # Judge all scenarios CONCURRENTLY - much faster than sequential
    results = await asyncio.gather(*[_run_one(agent, s, run_id) for s in scenarios])

    run = EvalRun(
        run_id=run_id,
        agent_name=agent_name,
        scenario_set=scenario_set,
        timestamp=datetime.now(timezone.utc),
        results=list(results),
    )
    summary = _compute_summary(run, scenarios)
    return run, summary


def _compute_summary(
    run: EvalRun,
    scenarios: list[Scenario] | None = None,
) -> EvalSummary:
    total = len(run.results)
    passed = sum(1 for r in run.results if r.passed)
    scores = [r.judge_score for r in run.results]

    # Group by tag (needs the scenarios to know each scenario's tags)
    by_tag: dict[str, dict] = {}
    if scenarios:
        tags_by_id = {s.id: s.tags for s in scenarios}
        for result in run.results:
            for tag in tags_by_id.get(result.scenario_id, []):
                bucket = by_tag.setdefault(tag, {"total": 0, "passed": 0})
                bucket["total"] += 1
                bucket["passed"] += int(result.passed)
        for bucket in by_tag.values():
            bucket["pass_rate"] = bucket["passed"] / bucket["total"]

    return EvalSummary(
        run_id=run.run_id,
        agent_name=run.agent_name,
        total=total,
        passed=passed,
        failed=total - passed,
        pass_rate=passed / total if total else 0.0,
        mean_score=sum(scores) / len(scores) if scores else 0.0,
        by_tag=by_tag,
    )
