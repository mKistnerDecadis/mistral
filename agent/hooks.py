"""Hooks that run inside the agent loop.

A hook sees every tool call before and after it runs. This one only observes: it writes an audit line per call, so a
workshop participant can watch what the model does, and the evals can count calls per investigation.
"""

import logging

import mistralai.agents as agents

log = logging.getLogger("investigation.audit")


class AuditTrail(agents.Hook):
    """Log every tool call with its stable ID and argument names. Never logs argument values: they can hold customer data."""

    async def pre_tool_call(self, ctx: agents.HookCallbackContext, call: agents.hook.PreToolCall) -> None:
        log.info("tool call %s(%s) in session %s", call.tool_id, ", ".join(sorted(call.arguments)), ctx.session.id)
        return None
