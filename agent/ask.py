"""Ask the agent one question from the terminal and print its report.

uv run --env-file ../.env python ask.py "What's causing the KeyError in checkout?"   # in-process
uv run --env-file ../.env python ask.py --served "..."                               # the agent `agents serve` runs
uv run --env-file ../.env python ask.py --json "..."                                 # the report as JSON
"""

import argparse
import asyncio
import logging
import sys

from investigate import Investigation, investigate, served_agent

DEFAULT_QUESTION = "What's causing the latest ValueError in Sentry, and which code is responsible?"


def render(outcome: Investigation) -> str:
    """The report as readable text, or the reason there is none."""
    lines = [f"Tool calls ({len(outcome.tool_calls)}): " + ", ".join(call.name for call in outcome.tool_calls)]
    if outcome.report is None:
        lines += ["", f"No report: {outcome.error}", "", outcome.text]
        return "\n".join(lines)
    report = outcome.report
    lines += ["", report.summary, ""]
    lines += [f"Exception:  {report.exception}", f"Where:      {report.file} :: {report.symbol}", f"Confidence: {report.confidence}", ""]
    lines += ["Root cause", "  " + report.root_cause, ""]
    if report.evidence:
        lines.append("Evidence")
        lines += [f"  [{e.source}] {e.reference}: {e.proves}" for e in report.evidence]
    if report.next_check:
        lines += ["", f"Next check: {report.next_check}"]
    return "\n".join(lines)


async def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question", nargs="*", help=f"The question to ask. Default: {DEFAULT_QUESTION!r}")
    parser.add_argument("--served", action="store_true", help="Ask the agent `agents serve` or `agents deploy` runs (INVESTIGATION_AGENT_NAME)")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)

    if args.served:
        agent = served_agent()
    else:
        from main import agent
    outcome = await investigate(" ".join(args.question) or DEFAULT_QUESTION, agent=agent)
    if args.json and outcome.report is not None:
        print(outcome.report.model_dump_json(indent=2))
    else:
        print(render(outcome))
    return 0 if outcome.ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main(sys.argv[1:])))
