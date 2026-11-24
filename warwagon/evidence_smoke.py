"""Run and verify a bounded Ollama evidence smoke on the benign Docker fixture."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from warwagon.http_probe import probe
from warwagon.model import ChatModel
from warwagon.preflight import decode_arguments


FIXTURE_PORT = 48739
FIXTURE_URL = f"http://127.0.0.1:{FIXTURE_PORT}/"
MODEL_URL = "http://127.0.0.1:11434/v1"
TOOL_NAME = "observe_fixture_head"
TOOL = {"type": "function", "function": {
    "name": TOOL_NAME,
    "description": "Read the HTTP status of the benign local fixture using HEAD. Takes no arguments.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}}
PROMPT = (
    "This is a benign HTTP observation test. First call observe_fixture_head once with no arguments. "
    "After the tool returns, report only one JSON object with the exact fields "
    "observation_sha256 (copied verbatim) and status_code (integer copied from the observation). "
    "Never guess or supply a status from your own knowledge."
)
TASK = "Observe the fixture and report its status."
CLAIM_KEYS = {"observation_sha256", "status_code"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def completion(model, messages, tools=None):
    response = model.complete(messages, tools=tools)
    choices = response.get("choices")
    choice = choices[0] if isinstance(choices, list) and choices else None
    message = choice.get("message") if isinstance(choice, dict) else None
    if not isinstance(message, dict):
        raise ValueError("malformed model completion")
    details = {
        "response_id": response.get("id"),
        "response_model": response.get("model"),
        "finish_reason": choice.get("finish_reason"),
        "usage": response.get("usage"),
    }
    return message, details


def initial_messages():
    return [{"role": "system", "content": PROMPT}, {"role": "user", "content": TASK}]


def valid_fixture_call(call):
    function = call.get("function") if isinstance(call, dict) else None
    return (
        isinstance(function, dict)
        and call.get("type", "function") == "function"
        and function.get("name") == TOOL_NAME
        and decode_arguments(function.get("arguments")) == {}
        and isinstance(call.get("id"), str)
        and bool(call["id"].strip())
    )


def observe(model):
    message, details = completion(model, initial_messages(), [TOOL])
    calls = message.get("tool_calls")
    call = calls[0] if isinstance(calls, list) and len(calls) == 1 else None
    if not valid_fixture_call(call):
        raise ValueError("model must select exactly one fixed fixture tool without arguments")
    observation = probe(FIXTURE_PORT)
    if observation.get("error_type") is not None or observation.get("status_code") is None:
        raise ValueError("fixture HEAD did not return an HTTP status")
    return {
        "tool_call": {"id": call["id"], "type": "function", "function": {"name": TOOL_NAME, "arguments": "{}"}},
        "invocation": details,
        "observation": observation,
        "observation_sha256": digest(observation),
    }


def make_claim(model, observed):
    messages = initial_messages()
    call = observed["tool_call"]
    messages.extend([
        {"role": "assistant", "content": "", "tool_calls": [call]},
        {"role": "tool", "tool_call_id": call["id"], "name": TOOL_NAME, "content": json.dumps({
            "observation_sha256": observed["observation_sha256"],
            "status_code": observed["observation"]["status_code"],
        })},
    ])
    message, details = completion(model, messages)
    raw = message.get("content")
    claim = None
    if isinstance(raw, str) and not message.get("tool_calls") and details["finish_reason"] in (None, "stop"):
        fenced = re.fullmatch(r"\`\`\`(?:json)?\s*\n(.*?)\n\`\`\`", raw.strip(), re.DOTALL | re.IGNORECASE)
        try:
            claim = json.loads(fenced.group(1) if fenced else raw)
        except json.JSONDecodeError:
            pass
    return {"claim": claim, "response": raw, "invocation": details}


def checkpoint_value(database, stage, create):
    with database:
        database.execute("BEGIN IMMEDIATE")
        row = database.execute("SELECT payload FROM stages WHERE name = ?", (stage,)).fetchone()
        if row is not None:
            return json.loads(row[0]), True
        result = create()
        database.execute("INSERT INTO stages VALUES (?, ?)", (stage, json.dumps(result)))
        return result, False


def run(model, checkpoint, stop_after_observation=False):
    manifest = {"schema_version": 1, "model": model.model, "contract_sha256": digest([
        FIXTURE_URL, MODEL_URL, TOOL, initial_messages(),
    ])}
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(checkpoint, timeout=1)) as database:
        with database:
            database.execute("CREATE TABLE IF NOT EXISTS stages (name TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        saved, _ = checkpoint_value(database, "manifest", lambda: manifest)
        if saved != manifest:
            raise ValueError("checkpoint belongs to a different model or fixture contract")
        observed, reused = checkpoint_value(database, "observation", lambda: observe(model))
        if stop_after_observation:
            return {"status": "observation_saved", "observation_reused": reused}
        claimed, claim_reused = checkpoint_value(database, "claim", lambda: make_claim(model, observed))

    return {
        "kind": "benign_head_evidence_run",
        **manifest,
        "tool_call": observed["tool_call"],
        "observation": observed["observation"],
        "observation_sha256": observed["observation_sha256"],
        "tool_invocation": observed["invocation"],
        "claim": claimed["claim"],
        "claim_response": claimed["response"],
        "claim_invocation": claimed["invocation"],
        "observation_reused": reused,
        "claim_reused": claim_reused,
    }


def verify(run_record, expected, claim_override=None):
    if expected.get("kind") != "benign_head_expectation" or expected.get("schema_version") != 1:
        raise ValueError("expected a benign fixture expectation artifact")
    expected_status = expected.get("status_code")
    if type(expected_status) is not int or not 100 <= expected_status <= 599:
        raise ValueError("expected status must be an HTTP status code")
    if run_record.get("kind") != "benign_head_evidence_run" or run_record.get("schema_version") != 1:
        raise ValueError("expected a benign fixture run artifact")
    observation = run_record.get("observation")
    if not valid_fixture_call(run_record.get("tool_call")):
        reason = "invalid_fixture_tool_call"
    elif (
        not isinstance(observation, dict)
        or observation.get("method") != "HEAD"
        or observation.get("url") != FIXTURE_URL
        or observation.get("redirects_followed") != 0
        or observation.get("error_type") is not None
        or run_record.get("observation_sha256") != digest(observation)
    ):
        reason = "invalid_observation"
    elif observation.get("status_code") != expected_status:
        reason = "fixture_status_mismatch"
    else:
        claim = run_record.get("claim") if claim_override is None else claim_override
        if (
            not isinstance(claim, dict)
            or set(claim) != CLAIM_KEYS
            or type(claim["status_code"]) is not int
            or claim["observation_sha256"] != run_record["observation_sha256"]
            or claim["status_code"] != expected_status
        ):
            reason = "claim_not_supported"
        else:
            reason = None
    return {"verified": reason is None, "reason": reason,
            "claim_source": "model" if claim_override is None else "supplied"}


def read_object(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return value, hashlib.sha256(raw).hexdigest()


def write_output(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    runner = commands.add_parser("run")
    runner.add_argument("--model", required=True)
    runner.add_argument("--checkpoint", required=True, type=Path)
    completion_mode = runner.add_mutually_exclusive_group(required=True)
    completion_mode.add_argument("--stop-after-observation", action="store_true")
    completion_mode.add_argument("--output", type=Path)
    verifier = commands.add_parser("verify")
    verifier.add_argument("trace", type=Path)
    verifier.add_argument("--expected", required=True, type=Path)
    verifier.add_argument("--claim", type=Path, help="optional externally supplied claim for falsification")
    verifier.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.output is not None and args.output.exists():
            raise ValueError("output must be a new file")
        if args.command == "run":
            if args.output is not None and args.output.resolve() == args.checkpoint.resolve():
                raise ValueError("output and checkpoint must be separate files")
            result = run(ChatModel(MODEL_URL, args.model, api_key=""), args.checkpoint, args.stop_after_observation)
            if args.stop_after_observation:
                print(json.dumps(result))
            else:
                write_output(args.output, result)
            return 0
        trace, trace_sha256 = read_object(args.trace)
        expected, expected_sha256 = read_object(args.expected)
        supplied_claim, supplied_claim_sha256 = read_object(args.claim) if args.claim else (None, None)
        result = verify(trace, expected, supplied_claim)
        result.update({
            "kind": "benign_head_evidence_verification",
            "schema_version": 1,
            "trace_sha256": trace_sha256,
            "expectation_sha256": expected_sha256,
            "supplied_claim_sha256": supplied_claim_sha256,
        })
        write_output(args.output, result)
        return 0 if result["verified"] else 1
    except (OSError, ValueError, sqlite3.Error) as exc:
        parser.exit(2, f"{exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
