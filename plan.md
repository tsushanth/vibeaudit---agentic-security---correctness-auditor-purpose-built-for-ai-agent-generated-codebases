# VibeAudit — Local MVP Scaffold Plan

Goal: prove the core value locally — running one CLI command against a git
repo/diff surfaces the four AI-agent failure modes (hallucinated packages,
hardcoded secrets, insecure IaC defaults, intent-violating logic). No
deployment, no product surface beyond the terminal.

## 1. Stack choice

**Python 3, single-package CLI, stdlib-first.**

- `argparse` for the CLI (no click/typer — one subcommand, doesn't earn a
  dependency).
- `urllib.request` (stdlib) for the two registry-existence checks (npm,
  PyPI) — no `requests` needed for two GET calls.
- `re` for secrets and IaC pattern matching — no AST/parser libraries; regex
  over file contents and `git diff` text is enough to prove the concept.
- One real third-party dependency: `anthropic` (Python SDK), used only by
  the intent-violation check.

Why Python over Node/Go: the checks are mostly "regex + one HTTP call +
one LLM call" — no compiled binary, no build step, no package.json/tsconfig
ceremony. A single-file-per-check layout is the lightest thing that still
reads as a real tool.

Why one LLM call is in scope despite "keep it minimal": detecting
*silently-wrong logic that passes tests but violates intent* is a semantic
judgment, not a pattern match — it cannot be demonstrated with regex or a
registry lookup. This is the one exception allowed under "unless the core
value is literally impossible to demonstrate without it." It reads
`ANTHROPIC_API_KEY` from the environment; no key management/storage beyond
that.

## 2. Explicitly out of scope for this local MVP

- No auth, accounts, or multi-user anything.
- No billing/licensing.
- No hosting, server, daemon, or webhook listener.
- No actual GitHub Action YAML/CI wiring (the pitch says "CLI/GitHub
  Action," but a GitHub Action is just this same CLI invoked in someone
  else's YAML — not needed to prove local value).
- No database or persistent state. Findings are printed to stdout
  (text or `--format json`); nothing is stored between runs.
- No custom-trained model or fine-tuning ("tuned on vibe-coding failure
  signatures" becomes, for the MVP, a hand-curated regex/heuristic set,
  and one prompted Claude call for the intent check — not a trained
  classifier).
- No multi-ecosystem coverage: only `package.json`/npm and
  `requirements.txt`/PyPI for the hallucinated-package check (proves the
  mechanism; more ecosystems are a config addition later, not a design
  change).
- No IaC coverage beyond Terraform (`.tf`) and Kubernetes manifests
  (`.yaml`/`.yml` with `kind:`) — enough to demo "public bucket / open SG /
  root container," not a full IaC parser.

## 3. File/directory layout

```
vibeaudit/
  cli.py                  # entry point: `python -m vibeaudit scan [...]`
  checks/
    __init__.py
    packages.py           # slopsquatting: diffs package.json/requirements.txt,
                           # queries npm/PyPI registry for existence
    secrets.py            # regex set for AWS keys, private key headers,
                           # generic high-entropy tokens, Slack/GitHub tokens
    iac.py                 # regex/line-scan over .tf and k8s yaml for
                           # 0.0.0.0/0 SGs, public-read ACLs, runAsUser 0 /
                           # missing securityContext
    intent.py              # sends commit message + diff to Claude, asks it
                           # to flag logic that contradicts stated intent
  git_utils.py             # thin wrapper: get staged diff / diff for a
                           # given commit range via subprocess + `git`
  report.py                # collects findings from all checks, renders
                           # text table or JSON
  fixtures/
    demo_bad_commit/       # a small git-less sample tree used by tests and
      package.json         #   the manual walkthrough:
      requirements.txt     #   - one hallucinated npm package
      main.tf              #   - one hallucinated PyPI package
      deploy.yaml          #   - one hardcoded AWS key
      app.py               #   - open 0.0.0.0/0 security group in main.tf
                            #   - root container in deploy.yaml
                            #   - a function whose logic inverts a stated
                            #     intent in its docstring/commit message
    demo_clean_commit/     # same shape, no findings — for the "no false
      ...                  #   positives on clean code" sanity check
  requirements.txt          # just: anthropic
tests/
  test_packages.py          # mocks the registry HTTP call; asserts a
                             # known-fake package name is flagged
  test_secrets.py           # runs secrets.py over fixtures/, asserts the
                             # planted AWS key is caught and nothing else is
  test_iac.py                # asserts the open SG / root container are
                              # both flagged, and the clean fixture is not
  # intent.py is excluded from automated tests (it calls a real LLM) —
  # verified manually, see below
```

## 4. Verification

**Automated (offline, no API key required):**
- `pytest tests/` — unit tests per static check module, each run against
  `fixtures/demo_bad_commit` (must flag) and `fixtures/demo_clean_commit`
  (must not flag, i.e. checks a false-positive baseline too).
- `packages.py`'s registry lookup is mocked in tests so the suite doesn't
  depend on network access.

**Manual run-through (end-to-end, proves the actual pitch):**
1. `git init` a scratch repo, copy in `fixtures/demo_bad_commit/`, commit it
   with a message describing the *intended* behavior (e.g. "add input
   validation before writing to DB").
2. Run `python -m vibeaudit scan --commit HEAD` from the scaffold.
3. Confirm the output lists all four categories: the fake npm/PyPI package,
   the hardcoded AWS key, the open security group / root container, and
   (with `ANTHROPIC_API_KEY` set) the logic that contradicts the commit
   message.
4. Repeat against `fixtures/demo_clean_commit/` and confirm zero findings.
5. Run once with `ANTHROPIC_API_KEY` unset to confirm the three static
   checks still work and `intent.py` fails/skips with a clear message
   rather than crashing the whole scan.
