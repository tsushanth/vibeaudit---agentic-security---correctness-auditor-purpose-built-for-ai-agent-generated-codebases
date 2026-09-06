"""Slopsquatting check: flags dependencies that don't exist on their registry.

AI coding agents sometimes hallucinate plausible-sounding package names.
This check reads package.json / requirements.txt and confirms every
dependency actually exists on npm / PyPI.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from ..report import Finding

NPM_REGISTRY = "https://registry.npmjs.org/{name}"
PYPI_REGISTRY = "https://pypi.org/pypi/{name}/json"

_REQ_LINE_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)")


def _npm_exists(name):
    url = NPM_REGISTRY.format(name=urllib.parse.quote(name))
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        return True  # inconclusive response, don't report a false positive
    except Exception:
        return True  # network unavailable, don't report a false positive


def _pypi_exists(name):
    url = PYPI_REGISTRY.format(name=urllib.parse.quote(name))
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        return True
    except Exception:
        return True


def _parse_package_json(path):
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    names = []
    for key in ("dependencies", "devDependencies"):
        names.extend((data.get(key) or {}).keys())
    return names


def _parse_requirements_txt(path):
    names = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        match = _REQ_LINE_RE.match(line)
        if match:
            names.append(match.group(1))
    return names


def check(path, npm_exists=None, pypi_exists=None):
    npm_exists = npm_exists or _npm_exists
    pypi_exists = pypi_exists or _pypi_exists
    root = Path(path)
    findings = []

    pkg_json = root / "package.json"
    if pkg_json.is_file():
        for name in _parse_package_json(pkg_json):
            if not npm_exists(name):
                findings.append(Finding(
                    category="hallucinated-package",
                    severity="high",
                    file="package.json",
                    message=f'npm package "{name}" does not exist on the npm registry',
                ))

    requirements_txt = root / "requirements.txt"
    if requirements_txt.is_file():
        for name in _parse_requirements_txt(requirements_txt):
            if not pypi_exists(name):
                findings.append(Finding(
                    category="hallucinated-package",
                    severity="high",
                    file="requirements.txt",
                    message=f'PyPI package "{name}" does not exist on PyPI',
                ))

    return findings
