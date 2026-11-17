"""Run one investigation turn and return its outcome as data.

`ask.py` and `evals/run_evals.py` both go through `investigate()`, so a change to how a turn is run or read lives here.
It works on the in-process agent (`main.agent`) and on a served or deployed one (`agents.Agent.load_from(...)`).
"""

import os
from dataclasses import dataclass, field

import mistralai.agents as agents

from report import InvestigationReport

DEFAULT_TIMEOUT_SECONDS = 600


@dataclass
class Investigation:
    """What one turn produced. `report` is None when the turn did not end with a valid InvestigationReport; `error` says why."""

    question: str
    session_id: str | None = None
    report: InvestigationReport | None = None
    text: str = ""
    tool_calls: tuple[agents.ToolCall, ...] = field(default_factory=tuple)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.report is not None


def served_agent(name: str | None = None) -> agents.Agent:
    """A handle on the agent that `agents serve` or `agents deploy` runs under `name` (default: INVESTIGATION_AGENT_NAME)."""
    agent_name = name or os.environ.get("INVESTIGATION_AGENT_NAME", "").strip() or "investigation-agent"
    return agents.Agent.load_from(agent_name=agent_name)


async def investigate(question: str, *, agent: agents.Agent, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> Investigation:
    """Start a session on `agent`, run `question` as one turn, and read the turn's record into an Investigation."""
    outcome = Investigation(question=question)
    session = await agent.start_session()
    outcome.session_id = session.id
    try:
        # A served or deployed agent keeps the report format it was started with; parsing here types the output either way.
        state = await session.run(question, output_type=InvestigationReport, timeout=timeout)
        read_state(outcome, state)
    finally:
        # One investigation per session: cancelling ends the session and frees its sandbox.
        await session.cancel()
    return outcome


def read_state(outcome: Investigation, state: object) -> None:
    """Fill `outcome` from the turn's record. Every record but Busy carries the latest assistant text."""
    outcome.text = getattr(state, "text", "") or ""
    outcome.tool_calls = tuple(getattr(state, "tool_calls", ()) or ())
    match state:
        case agents.Completed(output=InvestigationReport() as report):
            outcome.report = report
        case agents.Completed(output=agents.InvalidOutput(error=error)):
            outcome.error = f"The answer is not a valid InvestigationReport: {error}"
        case agents.Completed(stop_reason=reason):
            outcome.error = f"The turn ended without a final answer ({reason})"
        case agents.Failed(error=error):
            outcome.error = f"The turn failed ({error.code}): {error.message}"
        case agents.Blocked():
            outcome.error = "The turn is waiting on an approval or a client tool, which nothing answers here"
        case agents.Busy():
            outcome.error = "The session is busy with another turn"
        case _:
            outcome.error = f"The turn did not complete in time: {type(state).__name__}"
