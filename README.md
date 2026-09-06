# VibeAudit

A CLI that audits a codebase for the failure modes AI coding agents (Claude
Code, Cursor, etc.) are known to produce:

- **Slopsquatting** — dependencies in `package.json` / `requirements.txt`
  that don't actually exist on npm / PyPI (hallucinated package names).
- **Hardcoded secrets** — AWS keys, private key headers, Slack/GitHub
  tokens, and other high-entropy credential-shaped strings committed to
  source.
- **Insecure IaC defaults** — open security groups (`0.0.0.0/0`), public S3
  bucket ACLs (Terraform), and root/privileged containers (Kubernetes
  manifests).
- **Intent-violating logic** — code whose behavior contradicts what its own
  commit message or docstring says it should do (via one Claude API call;
  the only check that needs semantic judgment rather than a pattern match).

This is a **local MVP scaffold**: no server, no daemon, no accounts, no
GitHub Action wiring. It's a single CLI command you run against a directory
and/or a git commit, and it prints findings to stdout. See `plan.md` for the
full scope and the deliberate cuts.

## Install

```bash
pip install -r vibeaudit/requirements.txt   # anthropic (only needed for the intent check)
pip install pytest                          # only needed to run the test suite
```

No other setup — the three static checks (packages, secrets, IaC) use only
the standard library.

## Run it

From the repository root:

```bash
python -m vibeaudit scan --path <directory> --commit HEAD
```

- `--path` — directory to scan (default: `.`)
- `--commit` — commit to diff/read the message from, for the intent check
  (default: `HEAD`). Ignored if `--path` isn't inside a git repo.
- `--format text|json` — output format (default: `text`)

Exit code is `1` if any findings were reported, `0` otherwise (so it's
usable as a CI gate).

The intent check requires `ANTHROPIC_API_KEY` to be set in the environment.
If it isn't set (or the target directory isn't a git repo), that one check
is skipped with a warning on stderr — the other three checks still run.

## Try it on the bundled fixtures

`vibeaudit/fixtures/demo_bad_commit/` plants one example of each failure
mode; `vibeaudit/fixtures/demo_clean_commit/` is the same shape with no
issues, to sanity-check for false positives.

```bash
# scratch repo with the "bad" fixture
tmp=$(mktemp -d)
cp -r vibeaudit/fixtures/demo_bad_commit/. "$tmp"/
cd "$tmp" && git init -q && git add -A
git commit -q -m "add input validation before allowing signup"
cd -

python -m vibeaudit scan --path "$tmp" --commit HEAD
# with ANTHROPIC_API_KEY set, also flags is_eligible_for_signup() in app.py
# for always returning True regardless of age, contradicting its own docstring
# and the commit message above.
```

Repeat with `vibeaudit/fixtures/demo_clean_commit/` and it should report
`No findings.`

## Tests

```bash
pytest tests/
```

Covers the three static checks (packages, secrets, IaC) against both
fixtures, with the npm/PyPI registry lookups mocked so the suite runs
offline. The intent check calls a real LLM and is verified manually (see
above) rather than by an automated test.

## Layout

```
vibeaudit/
  cli.py              # `python -m vibeaudit scan ...`
  git_utils.py         # git subprocess wrapper (commit message/diff)
  report.py            # Finding model, text/JSON rendering
  checks/
    packages.py        # slopsquatting: npm/PyPI existence checks
    secrets.py          # regex + entropy scan for hardcoded credentials
    iac.py               # Terraform/Kubernetes insecure-default patterns
    intent.py            # Claude call: does the diff contradict its intent?
  fixtures/
    demo_bad_commit/     # one planted example of each failure mode
    demo_clean_commit/   # same shape, no issues
tests/                    # pytest suite for the three static checks
```
