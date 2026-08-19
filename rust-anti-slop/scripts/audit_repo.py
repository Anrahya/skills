#!/usr/bin/env python3
"""Read-only Rust repository anti-slop audit.

This script reports repository structure, policy configuration, and lexical signals
that deserve manual review. It never edits files and does not claim semantic proof.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "node_modules",
    "target",
    "vendor",
}

CONFIG_CANDIDATES = (
    "rust-toolchain.toml",
    "rust-toolchain",
    "rustfmt.toml",
    ".rustfmt.toml",
    "clippy.toml",
    ".clippy.toml",
    "deny.toml",
    ".cargo/config.toml",
    ".cargo/config",
    "justfile",
    "Justfile",
    "Makefile",
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
)


@dataclass(frozen=True)
class Signal:
    name: str
    pattern: re.Pattern[str]
    explanation: str


SIGNALS = (
    Signal("unwrap", re.compile(r"\.unwrap\s*\("), "Production panic convenience; inspect invariants and test-only use."),
    Signal("expect", re.compile(r"\.expect\s*\("), "Inspect whether the message is evidence or panic camouflage."),
    Signal("panic macro", re.compile(r"\bpanic!\s*\("), "Recoverable failures should not panic."),
    Signal("unreachable macro", re.compile(r"\bunreachable!\s*\("), "Requires a proven local invariant."),
    Signal("todo macro", re.compile(r"\btodo!\s*\("), "Placeholder path."),
    Signal("unimplemented macro", re.compile(r"\bunimplemented!\s*\("), "Placeholder path."),
    Signal("dbg macro", re.compile(r"\bdbg!\s*\("), "Likely debugging residue."),
    Signal("stdout/stderr print", re.compile(r"\b(?:println|eprintln)!\s*\("), "Review CLI boundary versus debug residue."),
    Signal("Result.ok erasure", re.compile(r"\.ok\s*\(\s*\)"), "May discard useful failure evidence."),
    Signal("let underscore", re.compile(r"\blet\s+_\s*="), "May ignore must-use values, futures, handles, or guards."),
    Signal("unsafe token", re.compile(r"\bunsafe\b"), "Unsafe proof surface; lexical count includes comments/docs."),
    Signal("allow attribute", re.compile(r"#!?\s*\[\s*allow\s*\("), "Every owned-code suppression needs narrow scope and reason."),
    Signal("expect attribute", re.compile(r"#!?\s*\[\s*expect\s*\("), "Verify reason and that expectation remains narrow."),
    Signal("serde_json::Value", re.compile(r"\bserde_json\s*::\s*Value\b"), "Untyped JSON should normally remain at adapters/boundaries."),
    Signal(
        "String-to-Value map",
        re.compile(r"HashMap\s*<\s*String\s*,\s*(?:serde_json\s*::\s*)?Value\s*>"),
        "Potential stringly typed internal contract.",
    ),
    Signal("Arc<Mutex", re.compile(r"\bArc\s*<\s*(?:(?:std|tokio)\s*::\s*sync\s*::\s*)?Mutex\s*<"), "Review ownership and synchronization invariant."),
    Signal("unbounded channel", re.compile(r"\bunbounded(?:_channel)?\s*\("), "Review memory bound and backpressure."),
    Signal("boxed trait object", re.compile(r"\bBox\s*<\s*dyn\s+"), "Review whether runtime-open polymorphism is real."),
    Signal("anyhow Result", re.compile(r"\banyhow\s*::\s*Result\b"), "Usually appropriate at app boundaries, not domain/library contracts."),
    Signal("task spawn", re.compile(r"\b(?:tokio|async_std)\s*::\s*(?:task\s*::\s*)?spawn\s*\("), "Verify handle, cancellation, error, and shutdown ownership."),
    Signal("sleep", re.compile(r"\b(?:std\s*::\s*thread|tokio\s*::\s*time|async_std\s*::\s*task)\s*::\s*sleep\s*\("), "Review blocking behavior and deterministic tests."),
    Signal("wildcard import", re.compile(r"\buse\s+[^;\n]*::\s*\*\s*;"), "Review explicit API surface; preludes/tests may be intentional."),
)


def run(command: list[str], cwd: Path, timeout: int = 20) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, completed.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)


def iter_files(root: Path, suffix: str) -> Iterable[Path]:
    for path in root.rglob(f"*{suffix}"):
        if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file():
            yield path


def load_toml(path: Path) -> tuple[dict, str | None]:
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle), None
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return {}, str(exc)


def relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def print_heading(title: str) -> None:
    print(f"\n== {title} ==")


def inspect_manifests(root: Path) -> None:
    print_heading("Cargo manifests")
    manifests = sorted(iter_files(root, "Cargo.toml"))
    if not manifests:
        print("No Cargo.toml files found.")
        return

    for manifest in manifests:
        data, error = load_toml(manifest)
        rel = relative(manifest, root)
        if error:
            print(f"- {rel}: TOML parse error: {error}")
            continue

        package = data.get("package", {})
        workspace = data.get("workspace")
        name = package.get("name", "<virtual workspace>")
        edition = package.get("edition", "<inherited/unspecified>")
        rust_version = package.get("rust-version", "<inherited/unspecified>")
        lint_table = data.get("lints", {})
        inherits = lint_table.get("workspace") is True
        roles: list[str] = []
        if "lib" in data or (manifest.parent / "src/lib.rs").exists():
            roles.append("lib")
        if "bin" in data or (manifest.parent / "src/main.rs").exists():
            roles.append("bin")
        if package.get("build") or (manifest.parent / "build.rs").exists():
            roles.append("build-script")
        if package.get("publish") is False:
            roles.append("unpublished")
        if data.get("lib", {}).get("proc-macro") is True:
            roles.append("proc-macro")
        role_text = ", ".join(roles) if roles else "unknown"
        print(
            f"- {rel}: package={name}, edition={edition}, rust-version={rust_version}, "
            f"roles={role_text}, lints.workspace={inherits}"
        )
        if workspace is not None:
            members = workspace.get("members", [])
            default_members = workspace.get("default-members", [])
            resolver = workspace.get("resolver", "<unspecified>")
            print(f"  workspace resolver={resolver}, members={members}, default-members={default_members}")
            if "lints" not in workspace:
                print("  signal: workspace has no [workspace.lints] table")


def inspect_configs(root: Path) -> None:
    print_heading("Repository policy/config files")
    found = False
    for candidate in CONFIG_CANDIDATES:
        path = root / candidate
        if path.exists():
            found = True
            print(f"- {candidate}")
    if not found:
        print("No common Rust policy/config files found beyond Cargo manifests.")

    workflow_dir = root / ".github" / "workflows"
    if workflow_dir.is_dir():
        workflows = sorted(p.name for p in workflow_dir.iterdir() if p.is_file())
        print(f"- .github/workflows: {workflows}")


def inspect_tools(root: Path) -> None:
    print_heading("Available toolchain")
    commands = (
        ("rustc", "rustc", ["rustc", "-Vv"]),
        ("cargo", "cargo", ["cargo", "-V"]),
        ("clippy", "cargo-clippy", ["cargo", "clippy", "-V"]),
        ("rustfmt", "rustfmt", ["cargo", "fmt", "--version"]),
        ("cargo-deny", "cargo-deny", ["cargo", "deny", "--version"]),
    )
    for label, executable, command in commands:
        if shutil.which(executable) is None:
            print(f"- {label}: not found")
            continue
        code, output = run(command, root)
        first_line = output.splitlines()[0] if output else f"exit {code}"
        print(f"- {label}: {first_line}")


def inspect_git(root: Path) -> None:
    print_heading("Git state")
    if not (root / ".git").exists() and shutil.which("git"):
        code, top = run(["git", "rev-parse", "--show-toplevel"], root)
        if code != 0:
            print("Not inside a Git worktree.")
            return
    if shutil.which("git") is None:
        print("git not found")
        return
    code, output = run(["git", "status", "--short"], root)
    if code != 0:
        print(output or "git status failed")
    elif output:
        print(output)
    else:
        print("Working tree clean.")


def inspect_metadata(root: Path) -> None:
    print_heading("Cargo metadata")
    if shutil.which("cargo") is None:
        print("cargo not found; metadata skipped")
        return
    code, output = run(
        ["cargo", "metadata", "--format-version", "1", "--no-deps", "--locked"],
        root,
        timeout=30,
    )
    if code != 0:
        print(f"metadata failed: {output[:1000]}")
        return
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        print(f"metadata JSON parse failed: {exc}")
        return
    packages = data.get("packages", [])
    workspace_members = set(data.get("workspace_members", []))
    print(f"packages={len(packages)}, workspace-members={len(workspace_members)}")
    for package in packages:
        if package.get("id") not in workspace_members:
            continue
        features = sorted(package.get("features", {}).keys())
        targets = [target.get("kind", []) for target in package.get("targets", [])]
        direct_deps = package.get("dependencies", [])
        print(
            f"- {package.get('name')} {package.get('version')}: "
            f"features={features}, targets={targets}, direct-deps={len(direct_deps)}"
        )


def scan_rust(root: Path, max_examples: int) -> None:
    print_heading("Lexical Rust signals (manual review required)")
    rust_files = sorted(iter_files(root, ".rs"))
    if not rust_files:
        print("No Rust source files found.")
        return

    total_lines = 0
    matches: dict[str, list[tuple[str, int, str]]] = {signal.name: [] for signal in SIGNALS}
    counts: dict[str, int] = {signal.name: 0 for signal in SIGNALS}

    for path in rust_files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lines = text.splitlines()
        total_lines += len(lines)
        for line_no, line in enumerate(lines, start=1):
            for signal in SIGNALS:
                occurrences = len(signal.pattern.findall(line))
                if occurrences == 0:
                    continue
                counts[signal.name] += occurrences
                if len(matches[signal.name]) < max_examples:
                    snippet = line.strip()
                    if len(snippet) > 180:
                        snippet = snippet[:177] + "..."
                    matches[signal.name].append((relative(path, root), line_no, snippet))

    print(f"Rust files={len(rust_files)}, lines={total_lines}")
    for signal in SIGNALS:
        count = counts[signal.name]
        if count == 0:
            continue
        print(f"\n- {signal.name}: {count}")
        print(f"  review: {signal.explanation}")
        for path, line_no, snippet in matches[signal.name]:
            print(f"  {path}:{line_no}: {snippet}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default=".", help="Cargo repository root")
    parser.add_argument("--max-examples", type=int, default=6, help="examples shown per lexical signal")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    print(f"Rust anti-slop read-only audit: {root}")
    print("Lexical matches are review signals only; comments, docs, tests, and valid boundary code may match.")

    inspect_git(root)
    inspect_tools(root)
    inspect_configs(root)
    inspect_manifests(root)
    inspect_metadata(root)
    scan_rust(root, max(0, args.max_examples))

    print_heading("Next review")
    print("1. Separate pre-existing failures from policy-introduced failures.")
    print("2. Classify crate roles and select only applicable lint profiles.")
    print("3. Fix underlying ownership/type/error/lifecycle design; do not launder lint findings.")
    print("4. Run the repository's canonical format, check, Clippy, test, doc, and dependency gates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
