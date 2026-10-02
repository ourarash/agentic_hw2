"""Part 1: control Job Radar with ordinary Python.

Read ``radar_domain.py`` before editing this file. Each supplied step reads the
current state and returns a dictionary containing only the fields it changed.
This controller must apply those updates itself.
"""

from __future__ import annotations

import asyncio

from radar_domain import (
    ClaimMode,
    RadarData,
    SourceJob,
    WorkflowRun,
    build_preview,
    canonicalize_jobs,
    initial_state,
    load_profile,
    score_matches,
    search_source_a,
    search_source_b,
    terminal_outcome,
    trace_event,
    verify_claims,
)
from resume_model import (
    ClaimGenerator,
    generate_claim_with_openai,
    make_tailor_resume_node,
)


# TODO 1: Combine the two search results.
#
# ``asyncio.gather`` returns one update from each search function. Each update
# contains a ``source_jobs`` list. Return one new list containing every record
# from Source A followed by every record from Source B.
#
# This operation only combines the two state updates. It must not remove the
# duplicate Rain City job. The later ``canonicalize_jobs`` step owns that rule.
def merge_search_updates(
    source_a_update: dict[str, object],
    source_b_update: dict[str, object],
) -> list[SourceJob]:
    raise NotImplementedError("TODO 1: follow the instructions above")


# TODO 2: Implement the application-controlled workflow.
#
# Run the supplied steps in this order:
#
#   1. Load the profile.
#   2. Start both searches together with ``asyncio.gather``.
#   3. Combine their ``source_jobs`` updates with TODO 1.
#   4. Canonicalize jobs and score matches.
#   5. Call the supplied claim generator through ``make_tailor_resume_node``.
#   6. Verify the model's claim with the deterministic verifier.
#   7. Build a preview only when ``claim_report["accepted"]`` is true.
#   8. Return one terminal outcome and the structured trace.
#
# After each step, apply its returned update with ``state.update(update)`` and
# append ``trace_event(step_name, update)``. Record one event for each search.
# The search event can be recorded after both searches finish. Use the order
# ``search_source_a`` followed by ``search_source_b`` so the trace is stable.
async def run_plain_workflow(
    claim_mode: ClaimMode = "supported",
    claim_generator: ClaimGenerator = generate_claim_with_openai,
) -> WorkflowRun:
    raise NotImplementedError("TODO 2: follow the instructions above")
