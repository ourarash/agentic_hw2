"""The HW 2 specification, written as tests.

Read this file, but do not edit it. Every test uses fixed local data. No test
calls a live model, website, job service, LangSmith, or other network service.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

import langgraph_workflow
import plain_workflow
from langgraph_workflow import (
    route_after_verification,
    run_langgraph_workflow,
    trace_langgraph_workflow,
)
from plain_workflow import merge_search_updates, run_plain_workflow
from radar_domain import (
    RadarData,
    SOURCE_A,
    SOURCE_B,
    canonicalize_jobs,
    initial_state,
    load_profile,
    score_matches,
    search_source_a,
    search_source_b,
)
from resume_model import (
    ResumeClaimOutput,
    generate_claim_with_openai,
    scripted_claim_generator,
)


EXPECTED_SUCCESS_NODES = {
    "load_profile",
    "search_source_a",
    "search_source_b",
    "canonicalize_jobs",
    "score_matches",
    "tailor_resume",
    "verify_claims",
    "build_preview",
}


def run(coroutine):
    """Run one coroutine from a synchronous pytest test."""

    return asyncio.run(coroutine)


def node_names(trace: list[dict[str, object]]) -> list[str]:
    """Return node names from either workflow's structured trace."""

    return [str(event["node"]) for event in trace]


def assert_success(outcome: dict[str, object]) -> None:
    """Check the shared success contract."""

    assert outcome["status"] == "preview_ready"
    assert outcome["source_record_count"] == 4
    assert outcome["canonical_job_count"] == 3
    assert outcome["selected_job_id"] == "rain-city-ai-platform-intern"

    preview = outcome["notification_preview"]
    assert preview["role"] == "Rain City Robotics: AI Platform Intern"
    assert preview["match_tier"] == "strong"
    assert preview["application_sent"] is False


def assert_failure(outcome: dict[str, object]) -> None:
    """Check the shared failure contract."""

    assert outcome == {
        "status": "failed",
        "failed_check": "resume_claims_supported",
        "details": ["Deployed and operated Kubernetes clusters."],
    }


def model_ready_state() -> RadarData:
    """Return the fixed state supplied to either live model backend."""

    state = initial_state("supported")
    state.update(load_profile(state))
    state["source_jobs"] = SOURCE_A + SOURCE_B
    state.update(canonicalize_jobs(state))
    state.update(score_matches(state))
    return state


def test_01_searches_are_fixed_local_fakes() -> None:
    async def collect():
        return await asyncio.gather(
            search_source_a({}),
            search_source_b({}),
        )

    source_a_update, source_b_update = run(collect())

    assert source_a_update == {"source_jobs": SOURCE_A}
    assert source_b_update == {"source_jobs": SOURCE_B}


def test_02_plain_merge_preserves_all_four_source_records() -> None:
    merged = merge_search_updates(
        {"source_jobs": SOURCE_A},
        {"source_jobs": SOURCE_B},
    )

    assert len(merged) == 4
    rain_city_records = [
        job for job in merged if job["company"] == "Rain City Robotics"
    ]
    assert len(rain_city_records) == 2, (
        "TODO 1 combines updates. It does not perform job deduplication."
    )


def test_03_openai_call_requests_one_structured_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LM_STUDIO_BASE_URL", raising=False)

    class FakeResponses:
        def __init__(self):
            self.arguments = None

        async def parse(self, **arguments):
            self.arguments = arguments
            return SimpleNamespace(
                output_parsed=ResumeClaimOutput(
                    text="Built a FastAPI service backed by PostgreSQL.",
                    claimed_skills=["FastAPI", "PostgreSQL"],
                    evidence_ids=["ev-python-api", "ev-postgres"],
                )
            )

    fake_responses = FakeResponses()
    fake_client = SimpleNamespace(responses=fake_responses)

    claim = run(
        generate_claim_with_openai(
            model_ready_state(),
            client=fake_client,
            model="test-model",
        )
    )

    assert claim["claimed_skills"] == ["FastAPI", "PostgreSQL"]
    assert fake_responses.arguments["model"] == "test-model"
    assert fake_responses.arguments["text_format"] is ResumeClaimOutput
    assert fake_responses.arguments["store"] is False
    assert "ev-python-api" in fake_responses.arguments["input"]


def test_03b_lm_studio_uses_structured_chat_completions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCompletions:
        def __init__(self):
            self.arguments = None

        async def parse(self, **arguments):
            self.arguments = arguments
            proposal = ResumeClaimOutput(
                text="Built a FastAPI service backed by PostgreSQL.",
                claimed_skills=["FastAPI", "PostgreSQL"],
                evidence_ids=["ev-python-api", "ev-postgres"],
            )
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(parsed=proposal))]
            )

    fake_completions = FakeCompletions()
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=fake_completions)
    )
    monkeypatch.setenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")

    claim = run(
        generate_claim_with_openai(
            model_ready_state(),
            client=fake_client,
            model="local-test-model",
        )
    )

    arguments = fake_completions.arguments
    assert claim["claimed_skills"] == ["FastAPI", "PostgreSQL"]
    assert arguments["model"] == "local-test-model"
    assert arguments["response_format"] is ResumeClaimOutput
    assert "ev-python-api" in arguments["messages"][1]["content"]


def test_04_plain_workflow_returns_a_checked_preview() -> None:
    result = run(
        run_plain_workflow(
            "supported",
            claim_generator=scripted_claim_generator,
        )
    )

    assert_success(result["outcome"])
    assert node_names(result["trace"]) == [
        "load_profile",
        "search_source_a",
        "search_source_b",
        "canonicalize_jobs",
        "score_matches",
        "tailor_resume",
        "verify_claims",
        "build_preview",
    ]


def test_05_plain_workflow_blocks_an_unsupported_claim() -> None:
    result = run(
        run_plain_workflow(
            "unsupported",
            claim_generator=scripted_claim_generator,
        )
    )

    assert_failure(result["outcome"])
    assert node_names(result["trace"])[-1] == "verify_claims"
    assert "build_preview" not in node_names(result["trace"])


def test_06_plain_workflow_starts_both_searches_before_waiting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started: set[str] = set()
    both_started = asyncio.Event()

    async def controlled_search(name: str, jobs: list[dict]):
        started.add(name)
        if len(started) == 2:
            both_started.set()
        await both_started.wait()
        return {"source_jobs": jobs}

    async def source_a(_):
        return await controlled_search("a", SOURCE_A)

    async def source_b(_):
        return await controlled_search("b", SOURCE_B)

    monkeypatch.setattr(plain_workflow, "search_source_a", source_a)
    monkeypatch.setattr(plain_workflow, "search_source_b", source_b)

    async def scenario():
        return await asyncio.wait_for(
            run_plain_workflow(
                "supported",
                claim_generator=scripted_claim_generator,
            ),
            timeout=0.5,
        )

    result = run(scenario())
    assert started == {"a", "b"}
    assert_success(result["outcome"])


@pytest.mark.parametrize(
    ("accepted", "expected_route"),
    [(True, "build_preview"), (False, "end")],
)
def test_07_graph_route_has_two_explicit_outcomes(
    accepted: bool,
    expected_route: str,
) -> None:
    state = {
        "claim_report": {
            "accepted": accepted,
            "unsupported_claims": [],
        }
    }

    assert route_after_verification(state) == expected_route


def test_08_langgraph_combines_parallel_updates_and_returns_a_preview() -> None:
    outcome = run(
        run_langgraph_workflow(
            "supported",
            claim_generator=scripted_claim_generator,
        )
    )

    assert_success(outcome)


def test_09_langgraph_blocks_an_unsupported_claim() -> None:
    outcome = run(
        run_langgraph_workflow(
            "unsupported",
            claim_generator=scripted_claim_generator,
        )
    )
    trace = run(
        trace_langgraph_workflow(
            "unsupported",
            claim_generator=scripted_claim_generator,
        )
    )

    assert_failure(outcome)
    assert node_names(trace)[-1] == "verify_claims"
    assert "build_preview" not in node_names(trace)


def test_10_langgraph_trace_exposes_the_fork_and_join() -> None:
    trace = run(
        trace_langgraph_workflow(
            "supported",
            claim_generator=scripted_claim_generator,
        )
    )
    names = node_names(trace)

    assert set(names) == EXPECTED_SUCCESS_NODES
    assert names[0] == "load_profile"
    assert names[-1] == "build_preview"
    assert names.index("canonicalize_jobs") > names.index("search_source_a")
    assert names.index("canonicalize_jobs") > names.index("search_source_b")

    search_events = {
        event["node"]: event for event in trace if "search_source" in event["node"]
    }
    assert search_events["search_source_a"]["updated_keys"] == ["source_jobs"]
    assert search_events["search_source_b"]["updated_keys"] == ["source_jobs"]


@pytest.mark.parametrize("claim_mode", ["supported", "unsupported"])
def test_11_both_runtimes_return_the_same_terminal_record(
    claim_mode: str,
) -> None:
    plain_result = run(
        run_plain_workflow(
            claim_mode,
            claim_generator=scripted_claim_generator,
        )
    )
    graph_outcome = run(
        run_langgraph_workflow(
            claim_mode,
            claim_generator=scripted_claim_generator,
        )
    )

    assert plain_result["outcome"] == graph_outcome
