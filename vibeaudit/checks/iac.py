"""Insecure IaC defaults check: Terraform open security groups / public
buckets, Kubernetes root or privileged containers."""

import re
from pathlib import Path

from ..report import Finding

_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}

_TF_PATTERNS = [
    (
        re.compile(r'cidr_blocks\s*=\s*\[[^\]]*0\.0\.0\.0/0[^\]]*\]'),
        "security group rule open to 0.0.0.0/0 (all IPs)",
    ),
    (
        re.compile(r'acl\s*=\s*"public-read(-write)?"'),
        "S3 bucket ACL set to public-read",
    ),
    (
        re.compile(r'block_public_acls\s*=\s*false'),
        "S3 bucket public-access block disabled",
    ),
]

_K8S_PATTERNS = [
    (
        re.compile(r'runAsUser:\s*0\b'),
        "container explicitly configured to run as root (runAsUser: 0)",
    ),
    (
        re.compile(r'privileged:\s*true'),
        "container running in privileged mode",
    ),
]


def _scan_lines(file_path, root, patterns):
    findings = []
    rel = str(file_path.relative_to(root))
    text = file_path.read_text(errors="ignore")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pattern, message in patterns:
            if pattern.search(line):
                findings.append(Finding(
                    category="iac",
                    severity="high",
                    file=rel,
                    line=lineno,
                    message=message,
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

        if file_path.suffix == ".tf":
            findings.extend(_scan_lines(file_path, root, _TF_PATTERNS))
        elif file_path.suffix in (".yaml", ".yml"):
            text = file_path.read_text(errors="ignore")
            if "kind:" in text:
                findings.extend(_scan_lines(file_path, root, _K8S_PATTERNS))

    return findings
