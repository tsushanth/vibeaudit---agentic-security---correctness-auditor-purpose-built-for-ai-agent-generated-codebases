from pathlib import Path

from vibeaudit.checks import secrets

FIXTURES = Path(__file__).parent.parent / "vibeaudit" / "fixtures"


def test_bad_commit_flags_hardcoded_aws_key():
    findings = secrets.check(FIXTURES / "demo_bad_commit")
    assert len(findings) == 1
    assert findings[0].category == "secret"
    assert findings[0].file == "app.py"
    assert "aws access key id" in findings[0].message


def test_clean_commit_has_no_findings():
    findings = secrets.check(FIXTURES / "demo_clean_commit")
    assert findings == []
