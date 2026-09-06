"""Entry point: `python -m vibeaudit scan [--path PATH] [--commit COMMIT] [--format text|json]`."""

import argparse
import sys

from . import git_utils, report
from .checks import iac, intent, packages, secrets


def build_parser():
    parser = argparse.ArgumentParser(
        prog="vibeaudit",
        description="Audit AI-agent-generated code for slopsquatting, hardcoded "
                     "secrets, insecure IaC defaults, and intent-violating logic.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="scan a directory / commit")
    scan.add_argument("--path", default=".", help="directory to scan (default: current directory)")
    scan.add_argument("--commit", default="HEAD", help="commit to use for the intent check (default: HEAD)")
    scan.add_argument("--format", choices=["text", "json"], default="text", help="output format")

    return parser


def run_scan(args):
    findings = []
    findings.extend(packages.check(args.path))
    findings.extend(secrets.check(args.path))
    findings.extend(iac.check(args.path))

    if git_utils.is_git_repo(args.path):
        try:
            message = git_utils.get_commit_message(args.commit, args.path)
            diff = git_utils.get_commit_diff(args.commit, args.path)
            findings.extend(intent.check(message, diff))
        except intent.IntentCheckSkipped as e:
            print(f"warning: skipping intent check ({e})", file=sys.stderr)
        except git_utils.GitError as e:
            print(f"warning: skipping intent check, could not read git history ({e})", file=sys.stderr)
    else:
        print("warning: skipping intent check, not a git repository", file=sys.stderr)

    if args.format == "json":
        print(report.render_json(findings))
    else:
        print(report.render_text(findings))

    return 1 if findings else 0


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "scan":
        return run_scan(args)
    parser.print_help()
    return 1
