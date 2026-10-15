import asyncio
import json
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from evalbench.models import EvalRun
from evalbench.regression import detect_regressions
from evalbench.reporter import generate_html_report
from evalbench.runner import _compute_summary, run_eval
from evalbench.scenarios.loader import load_scenarios

load_dotenv()

app = typer.Typer(help="agent-eval-bench - LLM agent evaluation framework")
console = Console()


@app.command()
def eval(
    scenarios_file: str = typer.Option(..., "--scenarios", "-s"),
    agent_name: str = typer.Option("my-agent", "--agent", "-a"),
    output: str = typer.Option("reports", "--output", "-o"),
    save_run: str = typer.Option(None, "--save", help="Save run JSON to file"),
):
    """Run an eval against a LangChain agent using a scenario YAML file."""
    # NOTE: in real use, import your own agent here.
    # The CLI demo builds the mock support agent for illustration.
    from scripts.demo import build_demo_agent  # type: ignore[import-not-found]

    agent = build_demo_agent()
    scenarios = load_scenarios(scenarios_file)

    console.print(f"Running {len(scenarios)} scenarios against {agent_name}...")
    run, summary = asyncio.run(run_eval(agent, scenarios, agent_name))

    # Print summary table
    table = Table(title=f"Results - {agent_name}")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Pass rate", f"{summary.pass_rate:.0%}")
    table.add_row("Mean score", f"{summary.mean_score:.2f}")
    table.add_row("Passed", str(summary.passed))
    table.add_row("Failed", str(summary.failed))
    console.print(table)

    report_path = generate_html_report(run, summary, output_dir=output)
    console.print(f"Report saved: {report_path}")

    if save_run:
        Path(save_run).write_text(run.model_dump_json())
        console.print(f"Run saved: {save_run}")


@app.command()
def compare(
    baseline_file: str = typer.Argument(...),
    current_file: str = typer.Argument(...),
):
    """Compare two eval run JSON files for regressions."""
    baseline_run = EvalRun(**json.loads(Path(baseline_file).read_text()))
    current_run = EvalRun(**json.loads(Path(current_file).read_text()))

    baseline = (baseline_run, _compute_summary(baseline_run))
    current = (current_run, _compute_summary(current_run))
    report = detect_regressions(baseline, current)

    console.print(f"Pass rate delta: {report.pass_rate_delta:+.1%}")
    if report.regressions:
        console.print(f"[red]Regressions: {report.regressions}[/red]")
    if report.improvements:
        console.print(f"[green]Improvements: {report.improvements}[/green]")


if __name__ == "__main__":
    app()
