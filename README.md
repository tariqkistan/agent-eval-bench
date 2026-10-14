agent-eval-bench
Change a prompt. Know what it broke. agent-eval-bench runs a suite of YAML scenarios through any
LangChain/LangGraph agent, scores each answer with an LLM judge, checks tool usage in plain code, and
diffs two runs so a prompt change shows up as "3 scenarios regressed, 1 improved" instead of a vibe.
Output: JSON run files and a single shareable HTML report. Exit codes make it a CI gate.
Scenarios in YAML: product and QA people can add test cases without touching Python
LLM-as-judge (GPT-4o): structured output, rationale before score, pass/fail decided in code
Deterministic tool checks: "must call create_ticket", "must never call lookup_account"
Regression detection: pass-to-fail flips, compared over shared scenarios only
Concurrent runs: asyncio with a semaphore; one failing scenario never aborts the run
Self-contained HTML report: no JS, no CDN, light/dark/mobile
What it looks like
Offline demo (--offline: rule-based agent + stub judge, so no API key; reports are stamped
STUB JUDGE). The "v2" agent has a deliberately broken ticket flow:
compare 20261014-184043-81aa71 -> 20261014-184043-059d02
pass rate change -26.7%   mean score change -0.19
regressions:  SC-002, SC-005, SC-013, SC-015
improvements: none
HTML report: reports/run_20261014-184043-059d02.html
​
Quickstart
git clone <https://github.com/tariqkistan/agent-eval-bench.git> && cd agent-eval-bench
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                                      # add OPENAI_API_KEY for live runs

pytest                                                    # 86 tests, no API key needed
python -m examples.demo --offline                         # full pipeline, no API key (stub judge)
python -m examples.demo                                   # live: LangChain agent + GPT-4o judge
​
The offline stub only checks tool rules. It proves the plumbing works; it is not a quality measure.
Use it with any agent
from evalbench import load_scenarios, run_eval, summarize, generate_html_report, save_report

run = await run_eval(my_agent, load_scenarios("scenarios/my_scenarios.yaml"), "my-agent-v1")
save_report(generate_html_report(run, summarize(run)), run.run_id)   # -> reports/run_<id>.html
​
my_agent is anything with async ainvoke(input, *, config=None): a LangChain AgentExecutor
(create it with return_intermediate_steps=True so tool calls are visible), a LangGraph graph, or
your own class. For agents that expect a different input shape, pass input_builder=.
Or from the command line:
evalbench eval --agent examples.support_agent:build_support_agent \
               --scenarios scenarios/support_agent_scenarios.yaml --name support-agent-v1
evalbench compare <baseline_run_id> <current_run_id>
evalbench report <run_id> --baseline <baseline_run_id>
​
-agent takes module:attribute: an agent instance, a class, or a zero-argument factory. The
current directory is importable. Useful flags on eval: -baseline, -fail-on-regression,
-fail-under 0.8, -threshold, -max-concurrency, -judge module:function, -trace.
Scenario format
scenarios:
  - id: SC-002
    description: Customer wants to raise a support ticket for a fault
    input_message: My machine is making a loud grinding noise, please log a ticket. My account is ACC-001.
    expected_behaviour: >-
      Agent creates a support ticket with priority medium or high and confirms the ticket ID.
    tags: [ticket_creation, happy_path]
    should_use_tools: [create_ticket]        # optional, checked in code
    should_not_use_tools: [lookup_account]   # optional, checked in code
​
should_use_tools / should_not_use_tools are enforced deterministically: a scenario fails if a
required tool was skipped or a forbidden one was called, whatever score the judge gave. Tool
order is not enforced in code; put it in expected_behaviour and the judge sees the ordered list.
Detecting regressions (before and after a prompt change)
evalbench eval --agent my_agent:build --scenarios scenarios/x.yaml --name v1     # baseline
# ...change the prompt...
evalbench eval --agent my_agent:build --scenarios scenarios/x.yaml --name v2 \
               --baseline <v1_run_id> --fail-on-regression
​
A regression is a scenario that passed in the baseline and fails now; an improvement is the
reverse. Deltas are computed over scenarios present in both runs, so adding easy scenarios cannot
fake an improvement. With --fail-on-regression the command exits 1, so it can gate a CI pipeline.
How it works
YAML scenarios -> runner (agent call + judge, up to N at once) -> EvalRun JSON
                                                              -> summary (pass rate, by tag)
EvalRun x2 -> regression detector -> RegressionReport         -> Jinja2 -> HTML report
​
Module
Job
loader.py
Parse and validate YAML; unique ids; errors name the bad scenario
judge.py
GPT-4o judge (temperature 0, structured output); deterministic tool checks
runner.py
Run scenarios concurrently, capture response, tools and latency
regression.py
Compare two runs scenario by scenario
summary.py / reporter.py
Aggregates, HTML report, terminal text
storage.py / cli.py
Save and load runs; Typer CLI
Design decisions
LLM-as-judge: open-ended answers cannot be string-matched. The judge writes its rationale
before the score, and the pass/fail decision is made in code against a threshold, not by the model.
Deterministic checks where possible: tool usage is a fact, so code checks it instead of the LLM.
YAML scenarios: QA analysts and product people can add test cases without writing Python.
asyncio.gather with a semaphore: all scenarios run concurrently, capped by
-max-concurrency so a large suite does not trip API rate limits. One failing scenario is
recorded on its result and never aborts the run.
Untrusted text is fenced and escaped: the agent's answer sits inside <agent_response> tags
with an instruction to treat it as data (limits prompt injection into the judge), and the HTML
report auto-escapes everything, so a hostile response cannot inject markup.
Judge model differs from the agent model in the example (gpt-4o vs gpt-4o-mini) to reduce
self-preference bias.
HTML report: one self-contained file (no CDN, no JS) that non-engineers can open from an email.
Status: what is verified and what is not
Verified in CI-equivalent conditions on Python 3.11 and 3.12: 86 tests (98% coverage), ruff,
mypy --strict, the offline demo, and the report in light, dark and mobile layouts.
Not verified: a live call to the GPT-4o judge, the Azure OpenAI path (the client is constructed
in tests but never called), --trace against a real LangSmith project, and a live run of the
LangChain example agent. Run python -m examples.demo once with your key and read the report
before relying on any of these.
Known limits
The judge is an LLM. It is not yet calibrated against human-labelled examples, so treat scores
as a consistent signal, not ground truth. temperature=0 reduces variance but does not
guarantee identical scores.
A single flip from pass to fail can be judge noise. Re-run before acting on one regression.
15 scenarios is a smoke suite, not a benchmark.
Latency is measured while scenarios run concurrently, so it includes shared-load effects.
Regressions are pass/fail flips; a score drop that stays above the threshold is not flagged.
License
MIT
