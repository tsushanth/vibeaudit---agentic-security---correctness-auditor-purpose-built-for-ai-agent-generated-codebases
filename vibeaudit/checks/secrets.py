"""Hardcoded-secret check: regex scan for common credential shapes."""

import math
import re
from collections import Counter
from pathlib import Path

from ..report import Finding

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

_PATTERNS = [
    ("aws access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private key", re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("slack token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,48}")),
    ("github token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}")),
]

_ASSIGNMENT_RE = re.compile(
    r"""(?i)\b(api[_-]?key|secret|password|passwd|token|access[_-]?key)\b\s*[:=]\s*["']([^"']{16,})["']"""
)

_PLACEHOLDER_RE = re.compile(
    r"(?i)^(changeme|your[_-].*|example.*|xxx+|placeholder.*|\.\.\.|<.*>|\$\{.*\}|none|null|test.*)$"
)

_ENTROPY_THRESHOLD = 3.5


def _shannon_entropy(value):
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((n / length) * math.log2(n / length) for n in counts.values())


def _scan_file(file_path, root):
    findings = []
    try:
        text = file_path.read_text(errors="ignore")
    except OSError:
        return findings

    rel = str(file_path.relative_to(root))
    for lineno, line in enumerate(text.splitlines(), start=1):
        matched_specific = False
        for label, pattern in _PATTERNS:
            if pattern.search(line):
                findings.append(Finding(
                    category="secret",
                    severity="high",
                    file=rel,
                    line=lineno,
                    message=f"hardcoded {label} detected",
                ))
                matched_specific = True
        if matched_specific:
            continue

        for match in _ASSIGNMENT_RE.finditer(line):
            value = match.group(2)
            if _PLACEHOLDER_RE.match(value):
                continue
            if _shannon_entropy(value) >= _ENTROPY_THRESHOLD:
                findings.append(Finding(
                    category="secret",
                    severity="medium",
                    file=rel,
                    line=lineno,
                    message=f"hardcoded {match.group(1)} with high-entropy value",
                ))
    return findings


def check(path):
    root = Path(path)
    findings = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in file_path.parts):
            continue
        findings.extend(_scan_file(file_path, root))
    return findings
