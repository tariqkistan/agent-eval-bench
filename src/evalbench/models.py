from datetime import datetime

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """One test case, loaded from YAML."""

    id: str
    description: str
    input_message: str
    expected_behaviour: str
    tags: list[str] = []
    should_use_tools: list[str] | None = None


class ScenarioResult(BaseModel):
    """Result of running one scenario through the agent."""

    scenario_id: str
    agent_response: str
    tools_called: list[str]
    judge_score: float = Field(ge=0.0, le=1.0)
    judge_rationale: str
    passed: bool
    latency_ms: float
    run_id: str


class EvalRun(BaseModel):
    """Complete eval run: all scenario results plus metadata."""

    run_id: str
    agent_name: str
    scenario_set: str
    timestamp: datetime
    results: list[ScenarioResult]


class EvalSummary(BaseModel):
    """Aggregated stats for an eval run."""

    run_id: str
    agent_name: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    mean_score: float
    by_tag: dict[str, dict]  # {tag: {total, passed, pass_rate}}


class RegressionReport(BaseModel):
    """Comparison between two eval runs."""

    baseline_run_id: str
    current_run_id: str
    regressions: list[str]    # scenario IDs that got worse
    improvements: list[str]   # scenario IDs that got better
    pass_rate_delta: float    # positive = improvement, negative = regression
