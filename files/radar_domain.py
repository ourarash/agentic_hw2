"""Fixed data and workflow steps for HW 2.

The assignment compares two ways to control the same workflow. This file holds
the shared work so students do not have to implement job matching twice.

All data is fictional. The search functions read in-memory lists and use short,
controlled delays. They do not call a website, model, or external service.
"""

from __future__ import annotations

import asyncio
from typing import Literal, TypedDict


ClaimMode = Literal["supported", "unsupported"]


class ProfileEvidence(TypedDict):
    evidence_id: str
    description: str
    skills: list[str]


class Profile(TypedDict):
    profile_id: str
    profile_version: int
    evidence: list[ProfileEvidence]


class SourceJob(TypedDict):
    source: str
    source_job_id: str
    company: str
    title: str
    location: str
    required_skills: list[str]
    preferred_skills: list[str]


class CanonicalJob(TypedDict):
    canonical_job_id: str
    company: str
    title: str
    location: str
    source_job_ids: list[str]
    required_skills: list[str]
    preferred_skills: list[str]


class MatchResult(TypedDict):
    canonical_job_id: str
    tier: Literal["strong", "partial", "weak"]
    matched_skills: list[str]
    unmet_skills: list[str]


class ResumeClaim(TypedDict):
    text: str
    claimed_skills: list[str]
    evidence_ids: list[str]


class ClaimReport(TypedDict):
    accepted: bool
    unsupported_claims: list[str]


class NotificationPreview(TypedDict):
    notification_id: str
    role: str
    match_tier: Literal["strong", "partial", "weak"]
    application_sent: Literal[False]


class RadarData(TypedDict, total=False):
    radar_run_id: str
    claim_mode: ClaimMode
    profile: Profile
    source_jobs: list[SourceJob]
    canonical_jobs: list[CanonicalJob]
    matches: list[MatchResult]
    selected_job: CanonicalJob
    resume_claims: list[ResumeClaim]
    claim_report: ClaimReport
    notification_preview: NotificationPreview
    status: str


class PreviewReady(TypedDict):
    status: Literal["preview_ready"]
    selected_job_id: str
    source_record_count: int
    canonical_job_count: int
    notification_preview: NotificationPreview


class ExplicitFailure(TypedDict):
    status: Literal["failed"]
    failed_check: str
    details: list[str]


RadarOutcome = PreviewReady | ExplicitFailure


class TraceEvent(TypedDict):
    node: str
    updated_keys: list[str]


class WorkflowRun(TypedDict):
    outcome: RadarOutcome
    trace: list[TraceEvent]


PROFILE: Profile = {
    "profile_id": "profile-lee-001",
    "profile_version": 3,
    "evidence": [
        {
            "evidence_id": "ev-python-api",
            "description": "Built a FastAPI service for a campus shuttle project.",
            "skills": ["Python", "FastAPI"],
        },
        {
            "evidence_id": "ev-postgres",
            "description": "Designed and queried the project's PostgreSQL database.",
            "skills": ["PostgreSQL"],
        },
        {
            "evidence_id": "ev-docker",
            "description": "Packaged the service in Docker.",
            "skills": ["Docker"],
        },
    ],
}


SOURCE_A: list[SourceJob] = [
    {
        "source": "source_a",
        "source_job_id": "job-a-101",
        "company": "Rain City Robotics",
        "title": "AI Platform Intern",
        "location": "Seattle, WA",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "preferred_skills": ["Docker", "Kubernetes"],
    },
    {
        "source": "source_a",
        "source_job_id": "job-a-102",
        "company": "Northstar Studio",
        "title": "Product Design Intern",
        "location": "Los Angeles, CA",
        "required_skills": ["Figma", "UX research"],
        "preferred_skills": ["Design systems"],
    },
]


SOURCE_B: list[SourceJob] = [
    {
        "source": "source_b",
        "source_job_id": "job-b-201",
        "company": "Rain City Robotics",
        "title": "AI Platform Intern",
        "location": "Seattle, WA",
        "required_skills": ["Python", "FastAPI", "PostgreSQL"],
        "preferred_skills": ["Docker", "Kubernetes"],
    },
    {
        "source": "source_b",
        "source_job_id": "job-b-202",
        "company": "Harbor Labs",
        "title": "Data Systems Intern",
        "location": "Seattle, WA",
        "required_skills": ["Python", "PostgreSQL", "Airflow"],
        "preferred_skills": ["Spark"],
    },
]


def initial_state(claim_mode: ClaimMode = "supported") -> RadarData:
    """Return fresh state for one workflow run."""

    return {
        "radar_run_id": f"radar-{claim_mode}-001",
        "claim_mode": claim_mode,
        "source_jobs": [],
        "status": "created",
    }


def load_profile(_: RadarData) -> dict[str, object]:
    """Load the verified profile used by this fictional example."""

    return {"profile": PROFILE, "status": "searching"}


async def search_source_a(_: RadarData) -> dict[str, object]:
    """Return Source A records after a short simulated wait."""

    await asyncio.sleep(0.03)
    return {"source_jobs": list(SOURCE_A)}


async def search_source_b(_: RadarData) -> dict[str, object]:
    """Return Source B records after a short simulated wait."""

    await asyncio.sleep(0.05)
    return {"source_jobs": list(SOURCE_B)}


def canonical_key(job: SourceJob) -> tuple[str, str, str]:
    """Return the fields that identify the same posting across sources."""

    return (
        job["company"].lower(),
        job["title"].lower(),
        job["location"].lower(),
    )


def canonicalize_jobs(state: RadarData) -> dict[str, object]:
    """Combine duplicate source records into one canonical job."""

    groups: dict[tuple[str, str, str], list[SourceJob]] = {}
    for job in state["source_jobs"]:
        groups.setdefault(canonical_key(job), []).append(job)

    canonical_jobs: list[CanonicalJob] = []
    company_slugs = {
        "Rain City Robotics": "rain-city",
        "Harbor Labs": "harbor",
        "Northstar Studio": "northstar",
    }
    for group in groups.values():
        first = group[0]
        title_slug = first["title"].lower().replace(" ", "-")
        canonical_jobs.append(
            {
                "canonical_job_id": f"{company_slugs[first['company']]}-{title_slug}",
                "company": first["company"],
                "title": first["title"],
                "location": first["location"],
                "source_job_ids": sorted(job["source_job_id"] for job in group),
                "required_skills": first["required_skills"],
                "preferred_skills": first["preferred_skills"],
            }
        )
    canonical_jobs.sort(key=lambda job: job["canonical_job_id"])
    return {"canonical_jobs": canonical_jobs, "status": "matching"}


def verified_skills(profile: Profile) -> set[str]:
    """Return every skill supported by the profile's evidence records."""

    return {
        skill
        for evidence_item in profile["evidence"]
        for skill in evidence_item["skills"]
    }


def score_matches(state: RadarData) -> dict[str, object]:
    """Rank jobs by the share of required skills found in the profile."""

    skills = verified_skills(state["profile"])
    matches: list[MatchResult] = []
    for job in state["canonical_jobs"]:
        required = set(job["required_skills"])
        preferred = set(job["preferred_skills"])
        ratio = len(required & skills) / max(1, len(required))
        tier: Literal["strong", "partial", "weak"]
        if ratio >= 0.8:
            tier = "strong"
        elif ratio >= 0.4:
            tier = "partial"
        else:
            tier = "weak"
        matches.append(
            {
                "canonical_job_id": job["canonical_job_id"],
                "tier": tier,
                "matched_skills": sorted((required | preferred) & skills),
                "unmet_skills": sorted(required - skills),
            }
        )

    tier_order = {"strong": 0, "partial": 1, "weak": 2}
    matches.sort(
        key=lambda match: (
            tier_order[match["tier"]],
            match["canonical_job_id"],
        )
    )
    selected_id = matches[0]["canonical_job_id"]
    selected_job = next(
        job
        for job in state["canonical_jobs"]
        if job["canonical_job_id"] == selected_id
    )
    return {"matches": matches, "selected_job": selected_job}


def verify_claims(state: RadarData) -> dict[str, object]:
    """Accept claims only when the cited evidence supports every skill."""

    evidence_by_id = {
        item["evidence_id"]: item for item in state["profile"]["evidence"]
    }
    unsupported: list[str] = []

    for claim in state["resume_claims"]:
        cited_ids = claim["evidence_ids"]
        if not cited_ids or not set(cited_ids) <= evidence_by_id.keys():
            unsupported.append(claim["text"])
            continue

        supported_skills = {
            skill
            for evidence_id in cited_ids
            for skill in evidence_by_id[evidence_id]["skills"]
        }
        if not set(claim["claimed_skills"]) <= supported_skills:
            unsupported.append(claim["text"])

    return {
        "claim_report": {
            "accepted": not unsupported,
            "unsupported_claims": unsupported,
        },
        "status": "verified" if not unsupported else "failed",
    }


def build_preview(state: RadarData) -> dict[str, object]:
    """Create a reviewable notification without sending or applying."""

    job = state["selected_job"]
    preview: NotificationPreview = {
        "notification_id": (
            f"{state['profile']['profile_id']}:"
            f"v{state['profile']['profile_version']}:"
            f"{job['canonical_job_id']}:resume-v1"
        ),
        "role": f"{job['company']}: {job['title']}",
        "match_tier": state["matches"][0]["tier"],
        "application_sent": False,
    }
    return {"notification_preview": preview, "status": "preview_ready"}


def terminal_outcome(state: RadarData) -> RadarOutcome:
    """Return one checked success or failure record for the caller."""

    report = state["claim_report"]
    if not report["accepted"]:
        return {
            "status": "failed",
            "failed_check": "resume_claims_supported",
            "details": report["unsupported_claims"],
        }

    if "notification_preview" not in state:
        return {
            "status": "failed",
            "failed_check": "notification_preview_created",
            "details": ["Verification passed, but no preview was created."],
        }

    return {
        "status": "preview_ready",
        "selected_job_id": state["selected_job"]["canonical_job_id"],
        "source_record_count": len(state["source_jobs"]),
        "canonical_job_count": len(state["canonical_jobs"]),
        "notification_preview": state["notification_preview"],
    }


def trace_event(node: str, update: dict[str, object]) -> TraceEvent:
    """Record which state fields one workflow step returned."""

    return {"node": node, "updated_keys": sorted(update)}
