# HW 2 — Job Radar: One Workflow, Two Runtimes

## EE 599: Designing and Building Autonomous AI Agents

**Expected time: about two hours. Tests and required demonstrations run
offline. A live model call is optional.**

## What you will build

Job Radar reviews internship matches. It loads a verified student profile,
searches two fixed local job sources at the same time, removes duplicate jobs,
ranks the results, drafts a résumé claim, checks that claim against profile
evidence, and creates a notification preview only when the check passes.

You will implement the same workflow twice:

1. Plain Python, where your code applies updates and controls every step.
2. LangGraph, where nodes return updates and the graph controls execution.

The searches use fixed local data. Running two searches at once does not make
this a multi-agent system.

## Setup

Use Python 3.11 or newer.

```bash
cd files
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

The initial test failures are expected. Each failure points to unfinished work.

## Your work

Edit only these files:

| File | Work |
|---|---|
| `plain_workflow.py` | TODO 1–2: combine search results and control the workflow |
| `langgraph_workflow.py` | TODO 3–6: state, routing, graph connections, and trace |
| `ANSWERS.md` | Four short explanations |

### Part 1: Plain Python

Complete TODO 1 and TODO 2. Use `asyncio.gather` to start both searches before
waiting for them. Combining the two lists is separate from removing duplicate
jobs.

```bash
pytest -q
python run_part1.py
```

`run_part1.py` shows accepted and rejected claims using fixed model responses.

### Part 2: LangGraph

Complete TODO 3 through TODO 6:

- Add the reducer that combines both search updates.
- Route accepted claims to `build_preview` and rejected claims to the end.
- Connect the parallel searches, join, remaining nodes, and final routes.
- Collect a local trace from graph updates.

Run `pytest -q` as you work.

### Part 3: Compare the results

After all tests pass, run:

```bash
python run_demo.py
```

Both implementations should produce the same final result. The offline demo
uses fixed model responses and requires no account, server, key, or network.

## Optional live model

The live run makes one model request and reuses the claim in both workflows.
It is not required for grading. Set variables in the same terminal where you
run the command. Never put an API key in source code or commit it to Git.

### OpenAI

Create an [API key](https://platform.openai.com/api-keys) in your OpenAI
account, then run:

```bash
unset LM_STUDIO_BASE_URL
export OPENAI_API_KEY="your-key"
python run_demo.py --live
```

The default model is `gpt-6-luna`. You may set `OPENAI_MODEL` to another model
available to your account.

### LM Studio

In [LM Studio](https://lmstudio.ai/docs/developer/core/server), load a chat
model and start the local server from the Developer tab. Copy the model
identifier shown there, then run:

```bash
export LM_STUDIO_BASE_URL="http://localhost:1234/v1"
export OPENAI_MODEL="your-loaded-model-id"
python run_demo.py --live
```

LM Studio runs locally and does not need an OpenAI API key. Local model output
varies, so the verifier may reject its claim; that is a valid workflow result.

On Windows PowerShell, set a variable with `$env:NAME="value"` instead of
`export NAME="value"`.

## Submit

Complete `ANSWERS.md`, run `pytest -q`, and submit your `files/` folder.
