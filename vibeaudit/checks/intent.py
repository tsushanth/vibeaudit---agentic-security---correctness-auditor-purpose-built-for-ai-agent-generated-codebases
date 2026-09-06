"""Intent-violation check: asks Claude whether a diff's logic contradicts
the intent stated in its own commit message. This is the one check that
needs an LLM call rather than a pattern match -- "does this code do what it
claims to do" is a semantic judgment, not a regex or a registry lookup."""

import json
import os

_SYSTEM_PROMPT = """You are a meticulous code reviewer looking for \
silently-wrong logic: code that would pass a casual test suite but \
contradicts what the commit message or docstrings say it should do. \
Given a commit message and a unified diff, list any places where the \
implementation appears to contradict the stated intent. Respond with ONLY \
JSON: a list of objects with keys "file", "line" (integer or null), and \
"message" (a one-sentence explanation of the contradiction). If nothing in \
the diff contradicts the stated intent, respond with an empty JSON list: []."""

DEFAULT_MODEL = "claude-sonnet-5"


class IntentCheckSkipped(Exception):
    """Raised when the intent check cannot run and should be skipped."""


def check(commit_message, diff_text, model=None):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise IntentCheckSkipped("ANTHROPIC_API_KEY is not set")

    try:
        import anthropic
    except ImportError as e:
        raise IntentCheckSkipped(
            "the 'anthropic' package is not installed (pip install anthropic)"
        ) from e

    from ..report import Finding

    if not diff_text.strip():
        return []

    client = anthropic.Anthropic(api_key=api_key)
    model = model or os.environ.get("VIBEAUDIT_MODEL", DEFAULT_MODEL)

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Commit message:\n{commit_message}\n\nDiff:\n{diff_text}",
        }],
    )

    text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )

    try:
        items = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return []

    findings = []
    for item in items or []:
        findings.append(Finding(
            category="intent",
            severity="medium",
            file=item.get("file", "unknown"),
            line=item.get("line"),
            message=item.get("message", "logic may contradict stated intent"),
        ))
    return findings
