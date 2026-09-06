from pathlib import Path

from vibeaudit.checks import iac

FIXTURES = Path(__file__).parent.parent / "vibeaudit" / "fixtures"


def test_bad_commit_flags_open_sg_and_root_container():
    findings = iac.check(FIXTURES / "demo_bad_commit")
    messages = " ".join(f.message for f in findings)

    assert "0.0.0.0/0" in messages
    assert "public-read" in messages
    assert "runAsUser: 0" in messages
    assert "privileged mode" in messages
    assert len(findings) == 4


def test_clean_commit_has_no_findings():
    findings = iac.check(FIXTURES / "demo_clean_commit")
    assert findings == []
