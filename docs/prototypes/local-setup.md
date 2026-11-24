# WarWagon local lab setup (Windows PowerShell)

## Goal
Prove a **real locally hosted language model** can issue a structured tool call, receive an HTTP observation from the local lab, and provide evidence for a reported finding. The harmless preflight and ARC reviews have recorded live results. The full lab acceptance run is still pending. See the [implementation snapshot](../context/current-state.md).

## Prerequisites
- Git, Python 3.10+ (prefer 3.12), and local [Ollama](https://ollama.com/download).
- Installed model with **tools** capability. Qwen3 8B is a starting point; choose based on RAM/VRAM.
- Local model server on `127.0.0.1:11434`.

## Commands (PowerShell)
```powershell
git clone https://github.com/digitalfire/WarWagon.git
cd WarWagon
py -3 -m unittest discover -s tests -v
ollama list
ollama pull qwen3:8b
$env:WW_MODEL = "qwen3:8b"
$env:WW_MODEL_BASE_URL = "http://127.0.0.1:11434/v1"
Invoke-RestMethod "http://127.0.0.1:11434/api/tags"
py -3 -m warwagon.preflight --model $env:WW_MODEL
py -3 -m warwagon.agent --model $env:WW_MODEL --max-steps 12 --output artifacts/lab-agent-run.json
$result = Get-Content artifacts/lab-agent-run.json -Raw | ConvertFrom-Json
$result.agent_discovery_score
$result.usage
$result.trace | Format-List
```

Preflight sends one harmless structured `report_probe` call, not a security testing action. If it fails, diagnose model API/tool capability before running WarWagon.

## Check a published local HTTP port

Run the standalone probe from the network namespace where the port is
published. For a Windows-host loopback port, use Windows Python with the
checkout available on its module path.

~~~powershell
py -3 -m warwagon.http_probe --port 8080 --output artifacts/http-connectivity.json
~~~

Replace the example port with the host port to check. The probe sends
one unauthenticated HEAD request to the IPv4 loopback root. It records
the HTTP status and timings, follows zero redirects, and uses no model.
A received redirect is a valid connectivity result. This check does
not serve as a model-driven assessment trace.

## Run an ARC smoke review
```powershell
py -3 -m warwagon.arc --model $env:WW_MODEL --proposal docs/adr/0001-docs-as-code.md --output artifacts/arc-review.json
```
This calls the configured model nine times with distinct reviewer instructions and isolated context. It does not create consensus from independent models when only one model is configured. ARC runs independently of the lab. See the [ARC runbook](real-agent-and-arc.md) for multiple reviewers and the validated local profile.

## What to report back
- Model tag and Ollama version
- Preflight `tool_call_correct` and `usage`
- Agent `agent_discovery_score` / `usage` and whether its trace contains tool calls
- Error messages, without API keys or private data

## Troubleshooting
- **Connection refused:** Ollama is not running or port differs; verify `Invoke-RestMethod http://127.0.0.1:11434/api/tags`.
- **404 model missing:** Model tag doesn't match `ollama list`; pull and set the exact name.
- **No tool calls:** Use a model explicitly tagged `tools`, run preflight, and ensure compatible Ollama version.
- **HTTP 400:** Check the exact provider API compatibility and tool schema. Preflight reports the HTTP error.
- **Tool-call object arguments:** WarWagon normalizes JSON objects to JSON strings before Chat Completions replay.
- **No agent credit:** Inspect whether the trace includes a reflected-markup observation and a final claim referring to `/search`. A verified fixture alone does not earn agent credit.
- **Long run:** Smaller model or too many inference steps; use `--max-steps 5` for triage, then restore a fair budget.
- **One reviewer model:** Separate prompts do not equal independent model consensus; don't promote an ADR on this basis.

## Evidence boundary
Do not paste model API keys or private run data. The fixture binds loopback only. Current scorer is intentionally narrow and may under-credit or over-credit particular outputs; it is not a general vulnerability verifier.
