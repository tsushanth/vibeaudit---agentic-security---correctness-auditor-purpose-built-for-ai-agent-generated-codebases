"""Thin wrapper around the git CLI: commit message, commit diff, staged diff."""

import subprocess


class GitError(Exception):
    pass


def _run(args, cwd):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as e:
        raise GitError("git executable not found") from e
    except subprocess.CalledProcessError as e:
        raise GitError(e.stderr.strip() or str(e)) from e
    return result.stdout


def is_git_repo(path):
    try:
        output = _run(["rev-parse", "--is-inside-work-tree"], cwd=path)
    except GitError:
        return False
    return output.strip() == "true"


def get_commit_message(commit, path):
    return _run(["log", "-1", "--format=%B", commit], cwd=path).strip()


def get_commit_diff(commit, path):
    """Diff introduced by `commit` (against its parent, or full diff if it's a root commit)."""
    return _run(["show", "--format=", commit], cwd=path)


def get_staged_diff(path):
    return _run(["diff", "--cached"], cwd=path)
