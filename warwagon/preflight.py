"""WarWagon model endpoint/tool-call preflight. Performs actual inference, no lab actions."""

import argparse
import json
import os
import sys
import time
from urllib.parse import urlsplit

from warwagon.model import ChatModel


PROBE_NAME = "report_probe"
PROBE_MESSAGE = "warwagon-ok"
TOOL = {
    "type": "function",
    "function": {
        "name": PROBE_NAME,
        "description": "Return a diagnostic string. No side effects.",
        "parameters": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
            "additionalProperties": False,
        },
    },
}


def decode_arguments(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None


def check(model: ChatModel):
    started = time.monotonic()
    response = model.complete(
        [
            {
                "role": "system",
                "content": (
                    f"This is a tool-call compatibility test. Call {PROBE_NAME} with message "
                    f"'{PROBE_MESSAGE}'. Do not answer only with text."
                ),
            },
            {"role": "user", "content": f"Use the {PROBE_NAME} tool now."},
        ],
        tools=[TOOL],
    )
    elapsed = round(time.monotonic() - started, 6)

    choices = response.get("choices")
    first = choices[0] if isinstance(choices, list) and choices else None
    message = first.get("message") if isinstance(first, dict) else None
    calls = message.get("tool_calls") if isinstance(message, dict) else None
    parsed = []
    exact_call = False
    if isinstance(calls, list):
        for call in calls:
            function = call.get("function") if isinstance(call, dict) else None
            if not isinstance(function, dict):
                parsed.append({"name": None, "arguments": {}})
                continue
            name = function.get("name")
            args = decode_arguments(function.get("arguments"))
            parsed.append({"name": name if isinstance(name, str) else None, "arguments": args or {}})
            exact_call = (
                len(calls) == 1
                and call.get("type", "function") == "function"
                and name == PROBE_NAME
                and args == {"message": PROBE_MESSAGE}
            )

    if not isinstance(message, dict):
        diagnostic = "fail: model returned a malformed completion message"
    elif calls is not None and not isinstance(calls, list):
        diagnostic = "fail: tool_calls must be an array"
    elif not exact_call:
        diagnostic = "fail: model did not return exactly one expected structured function call"
    else:
        diagnostic = "pass"

    endpoint = urlsplit(model.base_url)._replace(query="", fragment="").geturl()
    usage = response.get("usage")
    return {
        "model": model.model,
        "endpoint": endpoint,
        "tool_call_seen": isinstance(calls, list) and bool(calls),
        "tool_call_correct": exact_call,
        "calls": parsed,
        "usage": usage if isinstance(usage, dict) else {},
        "diagnostic": diagnostic,
        "elapsed_seconds": elapsed,
        "response_id": response.get("id"),
        "response_model": response.get("model"),
        "finish_reason": first.get("finish_reason") if isinstance(first, dict) else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.getenv("WW_MODEL", ""))
    parser.add_argument("--base-url", default=os.getenv("WW_MODEL_BASE_URL", "http://127.0.0.1:11434/v1"))
    args = parser.parse_args()
    if not args.model:
        parser.error("--model or WW_MODEL is required")
    try:
        result = check(ChatModel(args.base_url, args.model))
    except (OSError, ValueError) as exc:
        print(json.dumps({"diagnostic": "error", "error": str(exc), "type": type(exc).__name__}, indent=2))
        sys.exit(2)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["tool_call_correct"] else 1)


if __name__ == "__main__":
    main()
