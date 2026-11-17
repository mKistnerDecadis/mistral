"""The investigation agent: its model, its requirements (instructions.md), what it may use, and what it must answer with.

The `agents` CLI loads `agent` from here (`agents chat`, `agents serve`, `agents deploy`). The tests build the same agent
through `build_agent(connectors=False)`: same instructions, skills, policy, hooks and response format, but no connector
tools, so a scripted model can drive it offline.
"""

import os
from pathlib import Path

import mistralai.agents as agents

from config import GITHUB_CONNECTOR_ENV, SENTRY_CONNECTOR_ENV, connector_name, permission_policy
from hooks import AuditTrail
from report import InvestigationReport

ROOT = Path(__file__).resolve().parent
MODEL = "mistral-large-4"
# `agents serve --name` and `agents deploy --name` override it; the workflow opens sessions on this name.
DEFAULT_AGENT_NAME = "investigation-agent"


def build_agent(*, connectors: bool = True, name: str | None = None) -> agents.Agent:
    """Build the agent from its configuration. The connector names come from the environment (config.py)."""
    sentry, github = connector_name(SENTRY_CONNECTOR_ENV), connector_name(GITHUB_CONNECTOR_ENV)
    return agents.Agent(
        name=name or os.environ.get("INVESTIGATION_AGENT_NAME", "").strip() or DEFAULT_AGENT_NAME,
        model=MODEL,
        description="Investigates production errors with read-only Sentry and GitHub tools and answers with an InvestigationReport.",
        instructions=(ROOT / "instructions.md").read_text(encoding="utf-8"),
        # Every turn ends with a validated InvestigationReport: the evals and the workflow read it as data.
        output_type=InvestigationReport,
        max_iterations=32,
        temperature=0.1,
        # Bashkit holds the skill files that the `skill` tool loads. access="none" gives the model no shell or file tools.
        environment=agents.BashkitSandbox(access="none"),
        skills=[agents.LocalSkillBundle.from_directory(path) for path in sorted((ROOT / "skills").iterdir())],
        # The connectors are set up in the Studio workspace. auto_auth=False: a connector that is not connected fails the
        # session instead of letting the agent ask the user to connect it.
        connectors=[agents.connector(slot, run_as="auto", auto_auth=False) for slot in (sentry, github)] if connectors else [],
        # Deny by default; allow the reviewed read-only connector tools and the skill tool (config.py).
        permission_policy=permission_policy(sentry, github),
        hooks=[AuditTrail()],
        builtins=agents.Builtins(subagents=False),
    )


agent = build_agent()
