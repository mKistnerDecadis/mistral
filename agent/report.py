"""The structured answer every investigation turn must produce.

`InvestigationReport` is the agent's `output_type`: the model fills it in, the SDK validates it, and the evals and
the workflow read it as data instead of parsing prose. Keep the field descriptions precise: the model reads them.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """One piece of evidence the conclusion rests on."""

    source: Literal["sentry", "github", "other"] = Field(description="Which system the evidence came from.")
    reference: str = Field(description="A link or stable identifier: a Sentry issue URL or ID, a GitHub file or commit URL.")
    proves: str = Field(description="What this evidence establishes, in one sentence.")


class InvestigationReport(BaseModel):
    """The agent's answer to an investigation question."""

    summary: str = Field(description="One to three sentences: what is broken and why. No narration of the investigation.")
    exception: str | None = Field(default=None, description="The exception type and message as seen in Sentry, such as 'KeyError: UK'.")
    file: str | None = Field(default=None, description="Repository path of the responsible code, such as 'sample-app/shop/shipping.py'.")
    symbol: str | None = Field(default=None, description="The responsible function or class, such as 'rate_for'.")
    root_cause: str = Field(description="The defect in the code, stated as a fact about the code, with the offending line quoted when known.")
    confidence: Literal["low", "medium", "high"] = Field(description="How well the evidence supports the root cause.")
    evidence: list[Evidence] = Field(default_factory=list, description="The Sentry and GitHub references the conclusion rests on.")
    next_check: str | None = Field(default=None, description="The next concrete check when the evidence is incomplete, else null.")
