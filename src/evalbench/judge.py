import json
import os

from openai import AsyncOpenAI

from evalbench.models import Scenario

client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = os.environ.get("JUDGE_MODEL", "gpt-4o")
THRESHOLD = float(os.environ.get("PASS_THRESHOLD", "0.7"))

SYSTEM_PROMPT = """
You are evaluating an AI agent response.
Score from 0.0 to 1.0 based on:
1. Does the response fulfil the expected behaviour? (most important - 40%)
2. Is it accurate and grounded - no hallucination? (30%)
3. Are the right tools called if expected? (20%)
4. Is the tone professional, helpful, and appropriate? (10%)

Be strict. A score >= 0.7 means PASSED. Be consistent.
Respond ONLY in JSON:
{"score": 0.0, "rationale": "...", "passed": false}
"""


async def judge_response(
    scenario: Scenario,
    agent_response: str,
    tools_called: list[str],
) -> tuple[float, str, bool]:
    """Judge one agent response. Returns (score, rationale, passed)."""
    tool_info = ""
    if scenario.should_use_tools is not None:
        expected = ", ".join(scenario.should_use_tools) or "none"
        actual = ", ".join(tools_called) or "none"
        tool_info = f"Expected tools: {expected}\nActual tools called: {actual}\n"

    user = f"""SCENARIO:
Description: {scenario.description}
Input: {scenario.input_message}
Expected behaviour: {scenario.expected_behaviour}
{tool_info}
AGENT RESPONSE:
{agent_response}
"""

    response = await client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.strip()},
            {"role": "user", "content": user.strip()},
        ],
        max_tokens=400,
    )

    raw = json.loads(response.choices[0].message.content or "{}")
    score = float(raw.get("score", 0.0))
    rationale = raw.get("rationale", "No rationale provided")
    passed = score >= THRESHOLD
    return score, rationale, passed
