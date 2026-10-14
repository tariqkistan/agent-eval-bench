# agent-eval-bench

Reusable evaluation framework for LangChain agents using LLM-as-judge scoring
and regression detection.

## Usage

```bash
pip install -e '.[dev]'
pytest tests/ -v                 # unit tests (no real API key needed)
python scripts/demo.py           # full demo (needs a real OPENAI_API_KEY in .env)
```

```python
scenarios = load_scenarios("scenarios/support_agent_scenarios.yaml")
run, summary = await run_eval(agent, scenarios, "my-agent")
generate_html_report(run, summary)
```

## Regression workflow

1. Run the suite, save the run as a baseline (`evalbench eval ... --save baseline.json`).
2. Change your prompt, run again (`--save current.json`).
3. `evalbench compare baseline.json current.json`
4. Fix any regressions before merging.
