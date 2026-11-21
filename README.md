# Research Learning Agent

A read-only Python agent built with Google ADK, Vertex AI, Gemini, and Google Search grounding. It researches a topic, maps prerequisites and an ordered curriculum, then teaches one module at a time in at most 300 words with source links and a practice task.

## Example interaction

**Illustrative example, not a recorded agent run.** The response below is manually written to show the intended learning format. Its Docker reference link is not a captured Google Search grounding result. No live agent calls, tests, or evaluations were run during this repository cleanup because credentials are unavailable.

**You:** Teach me Docker from scratch.

> **Prerequisites:** Be comfortable opening a terminal and recognizing files and folders.
>
> **Roadmap:** 1. Containers and images. 2. Running containers. 3. Building images. 4. Persistent data. 5. Networking. 6. Docker Compose.
>
> **Module 1 — Containers and images**
>
> A container runs an application as an isolated process with its own filesystem and view of the system. An image supplies the files and settings used to start that container. Think of the image as the packaged starting point and the container as a running instance.
>
> Containers on the same host share an operating-system kernel; they are different from virtual machines that boot their own operating systems. Docker Desktop uses a Linux virtual machine for Linux containers on macOS and Windows.
>
> **Practice:** Sketch an image with two running containers created from it. Label which item is the package and which items are running processes.
>
> **Reference:** [Docker: What is a container?](https://docs.docker.com/learn/content/what-is-a-container/) — the official Docker guide explains container isolation, images, and virtual machines.
>
> Ask **“Continue to the next module”** when ready.

The actual agent is configured to search on each substantive turn and append links from returned grounding metadata. If metadata is missing, its callback adds a source-verification warning. A live screenshot or transcript can replace this illustration after credentials are restored.

## Project layout

```text
research-learning-agent/       repository root
  README.md                   setup and illustrative example
  pyproject.toml              package metadata and dependencies
  .env.example                placeholder configuration
  .gitignore                  local state and secret exclusions

research_agent/                Python package (inside the repository)
  __init__.py                 ADK package entrypoint
  agent.py                    root agent definition
  callbacks.py                word-limit and source-link enforcement
  config.py                   environment-backed settings
  logging_config.py           JSON structured logging
  policy.py                   learning and read-only policies
  tools.py                    Google Search tool boundary
  requirements.txt            Agent Runtime dependencies
  .agent_engine_config.json   deployment configuration
evals/                        live ADK evaluation cases and rubrics
tests/                        deterministic unit tests
```

The agent has exactly one capability: Google Search grounding. It has no filesystem, shell, browser-control, cloud-administration, or write tool.

## Prerequisites

Each user supplies their own Google Cloud project and credentials. The repository does not include credentials or a hosted demo. The documented setup uses Application Default Credentials for Vertex AI.

- Python 3.10 or newer
- A Google Cloud project with billing configured
- `gcloud` CLI
- Vertex AI API (`aiplatform.googleapis.com`) enabled

Google recommends Application Default Credentials for local development. No key file belongs in this repository.

## Local setup

From this project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example research_agent/.env
```

Edit `research_agent/.env` and replace `your-google-cloud-project-id`. Keep `GOOGLE_CLOUD_LOCATION=global` unless the selected model requires another supported location. Authenticate locally:

```bash
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
```

`.env`, local ADK sessions, caches, private keys, and common service-account filenames are ignored by Git.

## Run in the browser when credentials are available

Complete local setup first. From the `research-learning-agent` repository root, run:

```bash
adk web
```

Open the URL printed by ADK (normally `http://localhost:8000`), select `research_agent`, and enter:

```text
Teach me Docker from scratch.
```

The web interface is a local development UI. It still needs the configured Vertex AI credentials to generate responses. To capture a real demo later, include the module text and grounded source links, and omit account details or credentials. See the [official ADK web interface guide](https://adk.dev/runtime/web-interface/).

## Run in the terminal

Use ADK's interactive CLI from the project directory:

```bash
adk run research_agent
```

Example prompt:

```text
Teach me Kubernetes from scratch.
```

Ask `Continue to the next module` to advance. ADK keeps conversation context in the active session. This project does not configure cross-session long-term memory.

For a one-shot smoke query:

```bash
adk run --in_memory research_agent "Teach me DNS from scratch."
```

The CLI reports authentication, quota, model-access, and search failures from ADK. Invalid `RESEARCH_AGENT_MODEL` or `RESEARCH_AGENT_LOG_LEVEL` values fail during startup with a focused configuration error. Agent-owned logs are JSON and do not contain prompts or credentials.

## Checks

These commands are provided for contributors; they were not run during this cleanup. No current pass/fail result is claimed.

Deterministic checks do not call Vertex AI:

```bash
pytest
ruff check .
```

The tool test guards the read-only security boundary: the registered tool set must contain only ADK's `GoogleSearchTool`.

## Live agent evaluation

The repository includes two evaluation cases and judge rubrics. Their presence does not imply the live evaluation has passed; it was not run during this cleanup.

Live evaluations call Gemini, Google Search, and an LLM judge, so they require credentials and can incur Google Cloud charges. Install the evaluation extra, then run:

```bash
python -m pip install -e ".[eval]"
adk eval research_agent evals/research_agent.evalset.json \
  --config_file_path=evals/test_config.json \
  --print_detailed_results
```

The cases cover a from-scratch learning plan and next-module continuation. Rubrics check source links, prerequisites, ordered modules, one-module scope, a practice task, plain English, and the 300-word limit.

## Deploy to Agent Runtime

Deployment is intentionally not automatic. It creates paid Google Cloud resources.

1. Authenticate and select the intended project.
2. Enable the required APIs.
3. Run the ADK deployment command only after reviewing the target project and region.

```bash
gcloud auth login
gcloud auth application-default login
gcloud services enable \
  aiplatform.googleapis.com \
  cloudresourcemanager.googleapis.com

adk deploy agent_engine \
  --project="YOUR_PROJECT_ID" \
  --region="us-central1" \
  --display_name="Personal Research Learning Agent" \
  --otel_to_cloud \
  research_agent
```

ADK automatically reads `research_agent/.agent_engine_config.json` and `research_agent/requirements.txt`. The config contains only non-secret runtime defaults. Hosted credentials should come from the Agent Runtime service identity; never upload a service-account key.

Google Search grounding can return `groundingMetadata.searchEntryPoint.renderedContent`. Any production UI that consumes Agent Runtime responses must display those Google Search Suggestions as required by Google's grounding terms. The development CLI is the initial interface; it is not a production web UI.

## Common failures

- `DefaultCredentialsError`: run `gcloud auth application-default login`.
- `403 PERMISSION_DENIED`: verify the project, API enablement, model access, and IAM roles.
- `404` or unsupported model: select a Gemini model available in `GOOGLE_CLOUD_LOCATION` through `RESEARCH_AGENT_MODEL`.
- `429 RESOURCE_EXHAUSTED`: the project quota is exhausted; retry later or review Vertex AI quotas.
- No grounded links: treat the answer as a failed research response and retry; the policy requires current-turn search and source links.

## Official references

- [ADK Python quickstart](https://adk.dev/get-started/python/)
- [Google Cloud authentication for ADK](https://adk.dev/get-started/google-cloud/)
- [Google Search tool](https://adk.dev/integrations/google-search/)
- [Google Search grounding](https://adk.dev/grounding/google_search_grounding/)
- [ADK command-line runtime](https://adk.dev/runtime/command-line/)
- [ADK evaluation](https://adk.dev/evaluate/)
- [Agent Runtime deployment](https://adk.dev/deploy/agent-runtime/deploy/)
