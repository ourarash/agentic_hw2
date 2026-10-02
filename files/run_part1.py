"""Run only the plain Python workflow with fixed, offline model responses."""

import asyncio
import json

from plain_workflow import run_plain_workflow
from resume_model import scripted_claim_generator


async def main() -> None:
    """Show the accepted and rejected paths without using an API key."""

    print("--- Running Plain Python Workflow (Supported Claim) ---")
    result = await run_plain_workflow(
        "supported",
        claim_generator=scripted_claim_generator,
    )
    print(json.dumps(result, indent=2))

    print("\n--- Running Plain Python Workflow (Unsupported Claim) ---")
    result_unsupported = await run_plain_workflow(
        "unsupported",
        claim_generator=scripted_claim_generator,
    )
    print(json.dumps(result_unsupported, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
