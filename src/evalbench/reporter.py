from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from evalbench.models import EvalRun, EvalSummary, RegressionReport

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def generate_html_report(
    run: EvalRun,
    summary: EvalSummary,
    regression: RegressionReport | None = None,
    output_dir: str = "reports",
) -> str:
    """Generate an HTML report using the Jinja2 template. Saves to output_dir."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    template = env.get_template("report.html.j2")

    # Score distribution buckets (0-0.2, 0.2-0.4 ... 0.8-1.0)
    buckets = [0] * 5
    for r in run.results:
        idx = min(int(r.judge_score * 5), 4)
        buckets[idx] += 1

    html = template.render(
        run=run,
        summary=summary,
        regression=regression,
        buckets=buckets,
        bucket_labels=["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"],
    )

    Path(output_dir).mkdir(exist_ok=True)
    out_path = Path(output_dir) / f"run_{run.run_id}.html"
    out_path.write_text(html)
    return str(out_path)
