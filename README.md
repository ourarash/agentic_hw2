# HW 2 — Job Radar: One Workflow, Two Runtimes

## EE 599: Designing and Building Autonomous AI Agents

**Expected time: ~2 hours. The assignment includes one optional OpenAI model call. The automated tests do not use the network or consume API credits.**

---

## The Situation

Job Radar helps a student review internship matches. The workflow performs the following steps:

1. Loads a verified student profile (from local test data)
2. Searches two [mock job sources](files/radar_domain.py) concurrently
3. Combines and deduplicates the search results
4. Ranks jobs against the student's skills
5. Drafts a structured résumé claim using an LLM
6. Verifies the claim against the student's profile evidence
7. Creates a notification preview (only if verification passes)

You will build this workflow twice:
1. **Plain Python**: Using standard `asyncio` for parallel execution.
2. **LangGraph**: Using nodes, edges, and a state reducer.

This side-by-side comparison reveals exactly what LangGraph does for you (state management, parallel joins, routing) versus what you must handle yourself.

---

## Learning Goals

- Run independent asynchronous tasks concurrently
- Define LangGraph state, nodes, edges, and a state reducer
- Implement parallel branches, joins, and conditional routing
- Distinguish between a state reducer (combining lists) and domain logic (deduplication)
- Request a structured model response and verify it locally

### Key Terms
- **State:** The shared data dictionary for one workflow run.
- **Node:** One step in the LangGraph workflow (a Python function).
- **Reducer:** A rule specifying how to combine parallel updates to the same state field.
- **Canonical job:** A single, deduplicated job record.

---

## Setup

Use Python 3.11+.

```bash
cd files
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

The fresh handout contains unfinished functions, so tests will fail and point you to the `TODO`s. All mock data is stored locally in `radar_domain.py`.

---

## Files to Edit

You will edit exactly three files in the `files/` directory:

| File | Purpose |
|---|---|
| `plain_workflow.py` | Ordinary Python controller (TODO 1, 2) |
| `langgraph_workflow.py` | LangGraph state, routes, and graph (TODO 3, 4, 5, 6) |
| `ANSWERS.md` | Four short conceptual questions |

*(The other files contain fixed domain logic, mock data, and tests. You do not need to edit them.)*

---

## Part 1 — Plain Python control

Open `plain_workflow.py` and complete the `TODO`s.

You will use `asyncio.gather` to run both searches concurrently. Remember that combining state updates (TODO 1) is separate from deduplicating job postings (`canonicalize_jobs`).

Run tests to check your progress:
```bash
pytest -q
```

After TODO 1 and TODO 2 pass, run the plain Python workflow by itself:

```bash
python run_part1.py
```

This script shows both the accepted and rejected claim paths. It uses fixed
model responses, so it runs without an API key or network connection.

---

## Part 2 — LangGraph control

Open `langgraph_workflow.py` and complete the `TODO`s.

You will implement the exact same workflow, but expressed as a graph:
1. **Reducer (TODO 3)**: Tell LangGraph how to combine parallel `source_jobs` updates.
2. **Routing (TODO 4)**: Define the logic to skip `build_preview` if verification fails.
3. **Graph (TODO 5)**: Connect the nodes, including a parallel branch for the two searches.
4. **Trace (TODO 6)**: Collect a structured trace of the execution without needing LangSmith.

---

## Part 3 — Run the demonstrations

When all tests pass, run the offline demonstration. This uses hardcoded mock LLM responses.

```bash
python run_demo.py
```

Observe that both implementations produce the **exact same final outcomes and traces** for both a supported and an unsupported claim scenario.

### Optional: Live Model Call

To run the workflow with a real OpenAI call (requires an API key):
```bash
export OPENAI_API_KEY="your-key"
python run_demo.py --live
```

---

## Part 4 — Short explanations

Complete `ANSWERS.md`. Write two to four clear sentences for each question based on your observations.

---

## Note on Scope

This assignment focuses purely on workflow control. It does **not** include external API scraping, multi-agent delegation, or LangSmith setup.

*Reminder: Just because two searches run concurrently does **not** make this a multi-agent system!*

---

## Submission

Run the complete test suite:

```bash
pytest -q
```

Submit your `files/` folder with your completed:
- `plain_workflow.py`
- `langgraph_workflow.py`
- `ANSWERS.md`
