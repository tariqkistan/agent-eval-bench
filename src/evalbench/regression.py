from evalbench.models import EvalRun, EvalSummary, RegressionReport


def detect_regressions(
    baseline: tuple[EvalRun, EvalSummary],
    current: tuple[EvalRun, EvalSummary],
) -> RegressionReport:
    """Compare two runs. Find scenarios that got worse or better."""
    baseline_run, baseline_summary = baseline
    current_run, current_summary = current

    # Lookup dicts: scenario_id -> passed
    baseline_pass = {r.scenario_id: r.passed for r in baseline_run.results}
    current_pass = {r.scenario_id: r.passed for r in current_run.results}

    regressions: list[str] = []
    improvements: list[str] = []

    for scenario_id, now_passing in current_pass.items():
        was_passing = baseline_pass.get(scenario_id)
        if was_passing is None:
            continue  # new scenario, not in baseline

        if was_passing and not now_passing:
            regressions.append(scenario_id)   # got worse
        elif not was_passing and now_passing:
            improvements.append(scenario_id)  # got better

    return RegressionReport(
        baseline_run_id=baseline_run.run_id,
        current_run_id=current_run.run_id,
        regressions=sorted(regressions),
        improvements=sorted(improvements),
        pass_rate_delta=round(
            current_summary.pass_rate - baseline_summary.pass_rate, 4
        ),
    )
