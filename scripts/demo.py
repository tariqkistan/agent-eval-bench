"""Demo: runs eval-bench against the support-agent from Project 03."""
import asyncio
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from langchain.agents import AgentExecutor, create_openai_tools_agent  # noqa: E402
from langchain.tools import tool  # noqa: E402
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402

from evalbench.reporter import generate_html_report  # noqa: E402
from evalbench.runner import run_eval  # noqa: E402
from evalbench.scenarios.loader import load_scenarios  # noqa: E402


# -- MOCK TOOLS (replace with real support-agent tools if available) --
@tool
def lookup_account(account_id: str) -> str:
    """Look up a customer account by ID."""
    mock_accounts = {
        "ACC-001": (
            "Company: Acme Laser Co. Machine: LZ-3000. "
            "Warranty: expires 2026-03-15. Last service: 2024-11-01."
        ),
        "ACC-002": (
            "Company: SA Engravers. Machine: LZ-5000. "
            "Warranty: expired 2024-01-01. Last service: 2023-08-15."
        ),
    }
    return mock_accounts.get(account_id, f"Account {account_id} not found.")


@tool
def search_faq(query: str) -> str:
    """Search the FAQ for answers to common questions."""
    faqs = {
        "acrylic": "For 3mm acrylic: power 65%, speed 15mm/s, 2 passes.",
        "warranty": "All machines have a 2-year warranty from purchase date.",
    }
    for key, answer in faqs.items():
        if key in query.lower():
            return answer
    return "No FAQ entry found for this query."


@tool
def create_ticket(account_id: str, issue: str, priority: str = "medium") -> str:
    """Create a support ticket for a customer issue."""
    ticket_id = f"TKT-{str(uuid.uuid4())[:6].upper()}"
    return f"Ticket {ticket_id} created. Priority: {priority}. Issue: {issue[:50]}"


def build_demo_agent() -> AgentExecutor:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
    tools = [lookup_account, search_faq, create_ticket]

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a professional support agent for Perfect Laser. "
            "You help clients with questions about their laser machines. "
            "Always look up account before discussing machine details. "
            "Be concise and professional. "
            "Only answer laser machine support questions.",
        ),
        MessagesPlaceholder("chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=5,
        return_intermediate_steps=True,  # required so the runner can see tool calls
    )


async def main() -> None:
    agent = build_demo_agent()
    scenarios = load_scenarios("scenarios/support_agent_scenarios.yaml")

    print(f"Running {len(scenarios)} scenarios...")
    run, summary = await run_eval(
        agent, scenarios, "support-agent-v1", "support_agent_scenarios"
    )

    print(f"Pass rate: {summary.pass_rate:.0%} ({summary.passed}/{summary.total})")
    print(f"Mean score: {summary.mean_score:.2f}")
    print(f"Failed scenarios: {[r.scenario_id for r in run.results if not r.passed]}")

    report_path = generate_html_report(run, summary)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    asyncio.run(main())
