"""Import an explicit Wazuh alerts.json JSONL file for offline triage.

Wazuh record format:
https://documentation.wazuh.com/current/user-manual/capabilities/malware-detection/fim-threat-detection-rules.html

An importer-local severity mapping uses Wazuh rule levels 0–4 (low),
5–9 (medium), 10–12 (high), and 13–16 (critical). File changes are
observations. Escalation labels require a separate source.
https://documentation.wazuh.com/current/user-manual/ruleset/rules/rules-classification.html

Run with python -m benchmarks.triage.fim_import SOURCE --output ALERTS.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re


_FILE_EVENT_GROUPS = {
    "syscheck_file", "syscheck_entry_added", "syscheck_entry_modified", "syscheck_entry_deleted",
}


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_json_constant(_value):
    raise ValueError("invalid JSON constant")


def _text(record, key, field, *, required=False):
    if key not in record and not required:
        return None
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValueError(f"{field} must contain valid Unicode")
    return value


def _section(record, key, *, required=False):
    if key not in record and not required:
        return {}
    value = record.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _observed_at(record):
    value = _text(record, "timestamp", "timestamp")
    if value is None:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    else:
        value = re.sub(r"([+-]\d{2})(\d{2})$", r"\1:\2", value)
    try:
        timestamp = datetime.fromisoformat(value)
        if timestamp.tzinfo is None:
            raise ValueError("missing time zone")
        return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except (ValueError, OverflowError) as exc:
        raise ValueError("timestamp must be an ISO 8601 date and time with a UTC offset") from exc


def _severity(level):
    if type(level) is not int or not 0 <= level <= 16:
        raise ValueError("rule.level must be an integer from 0 through 16")
    if level >= 13:
        return "critical"
    if level >= 10:
        return "high"
    if level >= 5:
        return "medium"
    return "low"


def _convert_record(record, raw, line_number):
    rule = _section(record, "rule")
    groups = rule.get("groups")
    file_event_group = isinstance(groups, list) and any(
        isinstance(group, str) and group in _FILE_EVENT_GROUPS for group in groups
    )
    if "syscheck" not in record and not file_event_group:
        return None

    syscheck = _section(record, "syscheck", required=True)
    path = _text(syscheck, "path", "syscheck.path", required=True)
    rule_id = _text(rule, "id", "rule.id", required=True)
    level = rule.get("level")
    severity = _severity(level)
    description = _text(rule, "description", "rule.description")
    event = _text(syscheck, "event", "syscheck.event")
    agent_id = _text(_section(record, "agent"), "id", "agent.id")
    manager_name = _text(_section(record, "manager"), "name", "manager.name")
    observed_at = _observed_at(record)

    digest = hashlib.sha256(raw).hexdigest()
    vendor = {"path": path, "rule_id": rule_id, "rule_level": level}
    for key, value in (
        ("event", event), ("agent_id", agent_id), ("manager_name", manager_name),
    ):
        if value is not None:
            vendor[key] = value
    alert = {
        "id": f"wazuh-fim:{line_number}:{digest}",
        "summary": f"{description or 'Wazuh file-integrity event'} [{path}]",
        "severity": severity,
        "evidence": [],
        "source": {"line": line_number, "record_sha256": digest},
        "wazuh": vendor,
    }
    if observed_at is not None:
        alert["observed_at"] = observed_at
    if manager_name is not None and agent_id is not None:
        # Agent IDs are manager-local. The tuple keeps separators in source
        # fields from colliding and retains the path exactly as reported.
        scope = json.dumps([manager_name, agent_id, path], separators=(",", ":"))
        alert["scope"] = f"wazuh-fim:{scope}"
    return alert


def import_alerts(source_path):
    """Build v1 triage inputs with SHA-256 digests of the original bytes.

    Blank lines and unrelated records contribute to the file digest and line
    numbering. A record digest includes its line ending when present. The
    export should come from one Wazuh environment with unique manager names.
    """
    alerts = []
    file_digest = hashlib.sha256()
    with source_path.open("rb") as source:
        for line_number, raw in enumerate(source, start=1):
            file_digest.update(raw)
            if not raw.strip():
                continue
            try:
                record = json.loads(
                    raw.decode("utf-8"),
                    object_pairs_hook=_strict_object,
                    parse_constant=_invalid_json_constant,
                )
                if not isinstance(record, dict):
                    raise ValueError("expected a JSON object")
                alert = _convert_record(record, raw, line_number)
            except ValueError as exc:
                raise ValueError(f"source line {line_number}: {exc}") from exc
            if alert is not None:
                alerts.append(alert)

    if not alerts:
        raise ValueError("source contains no Wazuh file-integrity alerts")
    return {
        "kind": "triage_alerts",
        "schema_version": 1,
        "source": {"kind": "wazuh-alerts-jsonl", "sha256": file_digest.hexdigest()},
        "alerts": alerts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", type=Path, help="explicit Wazuh JSONL export")
    parser.add_argument("--output", type=Path, required=True, help="new v1 triage alerts artifact")
    args = parser.parse_args()
    try:
        artifact = import_alerts(args.source)
        with args.output.open("x", encoding="utf-8") as output:
            json.dump(artifact, output, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()
