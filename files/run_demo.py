"""Run both Job Radar implementations and print their outcomes and traces."""

from __future__ import annotations

import argparse
import asyncio
import json
import os

from langgraph_workflow import run_langgraph_workflow, trace_langgraph_workflow
from plain_workflow import run_plain_workflow
from radar_domain import RadarData, ResumeClaim
from resume_model import (
    ClaimGenerator,
    generate_claim_with_openai,
    scripted_claim_generator,
)


class ReuseOneClaim:
    """Get one claim, then reuse its value for a fair comparison."""

    def __init__(self, source: ClaimGenerator) -> None:
        self.source = source
        self.claim: ResumeClaim | None = None

    async def __call__(self, state: RadarData) -> ResumeClaim:
        if self.claim is None:
            self.claim = await self.source(state)
        return {
            "text": self.claim["text"],
            "claimed_skills": list(self.claim["claimed_skills"]),
            "evidence_ids": list(self.claim["evidence_ids"]),
        }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--live",
        action="store_true",
        help="Call a live model once and reuse its claim in both workflows.",
    )
    args = parser.parse_args()

    if args.live:
        lm_studio_base_url = os.getenv("LM_STUDIO_BASE_URL")
        if lm_studio_base_url and not os.getenv("OPENAI_MODEL"):
            parser.error(
                "Set OPENAI_MODEL to the model identifier loaded in LM Studio."
            )
        if not lm_studio_base_url and not os.getenv("OPENAI_API_KEY"):
            parser.error("Set OPENAI_API_KEY before using --live.")
        claim_modes = ("supported",)
        claim_source = generate_claim_with_openai
        model_mode = (
            "live LM Studio call"
            if lm_studio_base_url
            else "live OpenAI call"
        )
    else:
        claim_modes = ("supported", "unsupported")
        claim_source = scripted_claim_generator
        model_mode = "fixed offline response"

    for claim_mode in claim_modes:
        claim_generator = ReuseOneClaim(claim_source)
        plain_result = await run_plain_workflow(
            claim_mode,
            claim_generator=claim_generator,
        )
        graph_outcome = await run_langgraph_workflow(
            claim_mode,
            claim_generator=claim_generator,
        )
        graph_trace = await trace_langgraph_workflow(
            claim_mode,
            claim_generator=claim_generator,
        )
        print(
            json.dumps(
                {
                    "model_mode": model_mode,
                    "claim_mode": claim_mode,
                    "model_claim": claim_generator.claim,
                    "plain_python": plain_result,
                    "langgraph": {
                        "outcome": graph_outcome,
                        "trace": graph_trace,
                    },
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
