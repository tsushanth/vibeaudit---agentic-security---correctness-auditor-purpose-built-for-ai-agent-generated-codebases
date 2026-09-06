"""Finding data model and text/JSON rendering for scan results."""

import json
from dataclasses import asdict, dataclass
from typing import List, Optional

_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Finding:
    category: str  # "hallucinated-package" | "secret" | "iac" | "intent"
    severity: str  # "high" | "medium" | "low"
    file: str
    message: str
    line: Optional[int] = None


def _sort_key(finding: Finding):
    return (_SEVERITY_ORDER.get(finding.severity, 99), finding.category, finding.file, finding.line or 0)


def render_text(findings: List[Finding]) -> str:
    if not findings:
        return "No findings."

    findings = sorted(findings, key=_sort_key)
    lines = [f"{len(findings)} finding(s):", ""]
    for f in findings:
        location = f.file if f.line is None else f"{f.file}:{f.line}"
        lines.append(f"[{f.severity.upper():6}] {f.category:22} {location} - {f.message}")
    return "\n".join(lines)


def render_json(findings: List[Finding]) -> str:
    findings = sorted(findings, key=_sort_key)
    return json.dumps([asdict(f) for f in findings], indent=2)
