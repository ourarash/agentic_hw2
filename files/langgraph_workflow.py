"""Part 2: express the Job Radar workflow as a LangGraph graph.

The functions imported from ``radar_domain.py`` are the same steps used by the
plain Python controller. LangGraph will apply their state updates, schedule the
two searches, wait for both searches, and follow the verification route.
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from radar_domain import (
    CanonicalJob,
    ClaimMode,
    ClaimReport,
    MatchResult,
    NotificationPreview,
    Profile,
    RadarOutcome,
    ResumeClaim,
    SourceJob,
    TraceEvent,
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


class RadarState(TypedDict, total=False):
    """Shared data for one graph run.

    ``total=False`` allows fields to appear as later nodes produce them.
    """

    radar_run_id: str
    claim_mode: ClaimMode
    profile: Profile

    # TODO 3: Define how parallel search updates combine.
    #
    # Both search nodes write a ``list[SourceJob]`` to ``source_jobs`` during
    # the same graph step. Use ``Annotated`` and ``operator.add`` so LangGraph
    # concatenates those two lists instead of rejecting the concurrent writes.
    ...  # Write your code here for TODO 3.

    canonical_jobs: list[CanonicalJob]
    matches: list[MatchResult]
    selected_job: CanonicalJob
    resume_claims: list[ResumeClaim]
    claim_report: ClaimReport
    notification_preview: NotificationPreview
    status: str


# TODO 4: Choose the route after claim verification.
#
# Return ``"build_preview"`` when the claim report is accepted. Return
# ``"end"`` when it is rejected. These names will be mapped to graph
# destinations in TODO 5.
def route_after_verification(
    state: RadarState,
) -> Literal["build_preview", "end"]:
    raise NotImplementedError("TODO 4: follow the instructions above")


# TODO 5: Build and compile the graph.
#
# Register the supplied functions as eight nodes. Create the ``tailor_resume``
# node with ``make_tailor_resume_node(claim_generator)`` so this graph can use
# either the live model or the fixed test generator. Then add these connections:
#
#   START -> load_profile
#   load_profile -> search_source_a
#   load_profile -> search_source_b
#   [search_source_a, search_source_b] -> canonicalize_jobs
#   canonicalize_jobs -> score_matches -> tailor_resume -> verify_claims
#   verify_claims -> build_preview or END, chosen by TODO 4
#   build_preview -> END
#
# The list form of ``add_edge`` creates the join: ``canonicalize_jobs`` waits
# until both search nodes finish.
def build_radar_graph(
    claim_generator: ClaimGenerator = generate_claim_with_openai,
):
    raise NotImplementedError("TODO 5: follow the instructions above")


async def run_langgraph_workflow(
    claim_mode: ClaimMode = "supported",
    claim_generator: ClaimGenerator = generate_claim_with_openai,
) -> RadarOutcome:
    """Run the graph and return the same terminal record as Part 1."""

    graph = build_radar_graph(claim_generator)
    final_state = await graph.ainvoke(initial_state(claim_mode))
    return terminal_outcome(final_state)


# TODO 6: Collect a local structured trace.
#
# Use ``graph.astream`` with ``stream_mode="updates"``. Each streamed item maps
# a node name to that node's partial state update. Convert every node update to
# ``trace_event(node_name, update)`` and return the completed list.
#
# This trace stays on the student's computer. It does not require LangSmith,
# an account, an API key, or a network connection.
async def trace_langgraph_workflow(
    claim_mode: ClaimMode = "supported",
    claim_generator: ClaimGenerator = generate_claim_with_openai,
) -> list[TraceEvent]:
    raise NotImplementedError("TODO 6: follow the instructions above")
