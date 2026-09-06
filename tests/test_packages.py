from pathlib import Path

from vibeaudit.checks import packages

FIXTURES = Path(__file__).parent.parent / "vibeaudit" / "fixtures"


def fake_npm_exists(name):
    return "fake" not in name


def fake_pypi_exists(name):
    return "fake" not in name


def test_bad_commit_flags_hallucinated_packages():
    findings = packages.check(
        FIXTURES / "demo_bad_commit",
        npm_exists=fake_npm_exists,
        pypi_exists=fake_pypi_exists,
    )
    categories = {f.category for f in findings}
    assert categories == {"hallucinated-package"}

    messages = " ".join(f.message for f in findings)
    assert "vibeaudit-fake-pkg-3f9a21c8" in messages
    assert "vibeaudit-fake-pypkg-3f9a21c8" in messages
    assert len(findings) == 2


def test_clean_commit_has_no_findings():
    findings = packages.check(
        FIXTURES / "demo_clean_commit",
        npm_exists=fake_npm_exists,
        pypi_exists=fake_pypi_exists,
    )
    assert findings == []
