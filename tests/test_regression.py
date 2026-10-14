from copy import deepcopy

from evalbench.regression import detect_regressions
from evalbench.runner import _compute_summary


def test_detects_regression(sample_run):
    # baseline: SC-001 passes, SC-002 fails
    baseline = (sample_run, _compute_summary(sample_run))

    # current: SC-001 NOW FAILS (regression), SC-002 now passes (improvement)
    current_run = deepcopy(sample_run)
    current_run.run_id = "r2"
    current_run.results[0].passed = False
    current_run.results[0].judge_score = 0.4
    current_run.results[1].passed = True
    current_run.results[1].judge_score = 0.8
    current = (current_run, _compute_summary(current_run))

    report = detect_regressions(baseline, current)

    assert "SC-001" in report.regressions
    assert "SC-002" in report.improvements


def test_no_regressions_when_identical(sample_run):
    baseline = (sample_run, _compute_summary(sample_run))
    current = (sample_run, _compute_summary(sample_run))

    report = detect_regressions(baseline, current)

    assert len(report.regressions) == 0
