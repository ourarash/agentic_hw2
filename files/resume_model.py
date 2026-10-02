"""The shared model call used by both Job Radar workflows.

The live function asks an OpenAI model for one structured résumé claim. The
application then checks the returned claim against the supplied profile
evidence. The model does not decide whether the claim is accepted.

Tests use ``scripted_claim_generator`` so grading is repeatable and does not
need an API key or network connection.
"""

from __future__ import annotations

import json
import os
from collections.abc import Awaitable, Callable
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict

from radar_domain import RadarData, ResumeClaim


class ResumeClaimOutput(BaseModel):
    """The exact fields the model must return."""

    model_config = ConfigDict(extra="forbid")

    text: str
    claimed_skills: list[str]
    evidence_ids: list[str]


ClaimGenerator = Callable[[RadarData], Awaitable[ResumeClaim]]


MODEL_INSTRUCTIONS = """You draft one short résumé sentence for a student.
Use only facts and skills supported by the supplied profile evidence. Tailor
the sentence to the selected job without claiming an unsupported skill. Cite
the evidence IDs that support the sentence. Return the requested fields only.
"""


def model_input(state: RadarData) -> str:
    """Build the data sent to the model for one claim proposal."""

    return json.dumps(
        {
            "selected_job": state["selected_job"],
            "verified_profile_evidence": state["profile"]["evidence"],
        },
        indent=2,
    )


async def generate_claim_with_openai(
    state: RadarData,
    *,
    client: Any | None = None,
    model: str | None = None,
) -> ResumeClaim:
    """Request one typed claim from the OpenAI Responses API.

    ``client`` and ``model`` are optional so tests can supply a local test
    client. A normal run reads ``OPENAI_API_KEY`` through ``AsyncOpenAI`` and
    uses ``OPENAI_MODEL`` when it is set.
    """

    openai_client = client or AsyncOpenAI()
    model_name = model or os.getenv("OPENAI_MODEL", "gpt-6-luna")
    response = await openai_client.responses.parse(
        model=model_name,
        instructions=MODEL_INSTRUCTIONS,
        input=model_input(state),
        text_format=ResumeClaimOutput,
        max_output_tokens=300,
        store=False,
    )
    proposal = response.output_parsed
    if proposal is None:
        raise RuntimeError("The model did not return a résumé claim.")

    return {
        "text": proposal.text,
        "claimed_skills": proposal.claimed_skills,
        "evidence_ids": proposal.evidence_ids,
    }


async def scripted_claim_generator(state: RadarData) -> ResumeClaim:
    """Return fixed claims for tests and the offline demonstration."""

    if state["claim_mode"] == "unsupported":
        return {
            "text": "Deployed and operated Kubernetes clusters.",
            "claimed_skills": ["Kubernetes"],
            "evidence_ids": ["ev-docker"],
        }
    return {
        "text": (
            "Built a FastAPI service backed by PostgreSQL and packaged "
            "it with Docker."
        ),
        "claimed_skills": ["FastAPI", "PostgreSQL", "Docker"],
        "evidence_ids": ["ev-python-api", "ev-postgres", "ev-docker"],
    }


def make_tailor_resume_node(
    claim_generator: ClaimGenerator,
):
    """Wrap a claim generator as one async workflow step."""

    async def tailor_resume(state: RadarData) -> dict[str, object]:
        claim = await claim_generator(state)
        return {"resume_claims": [claim], "status": "verifying"}

    tailor_resume.__name__ = "tailor_resume"
    return tailor_resume
