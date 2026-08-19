---
name: rust-anti-slop
description: Apply evidence-driven Rust engineering discipline while writing, reviewing, debugging, refactoring, hardening, or governing Rust and Cargo repositories. Use for ownership and error design, async lifecycle, unsafe/FFI, APIs, dependencies, features, tests, compiler or Clippy findings, and repository lint or CI policy. Adapt to the repository's toolchain, MSRV, crate roles, targets, features, and conventions.
metadata:
  version: "1.2.0"
---

# Rust anti-slop

Make incorrect, vague, wasteful, difficult-to-review, and unjustified Rust code hard to introduce. Compiler and lint findings are evidence, not permission for mechanical rewrites. Preserve behavior, public contracts, supported targets, repository conventions, and unrelated work.

## Route the task

Read each matching reference in full before acting. Do not load references for risks the task does not contain.

| Task or risk | Required reference |
|---|---|
| Any Rust implementation, review, debugging, refactoring, or repair | `references/engineering-core.md` |
| Types, ownership, borrowing, traits, dispatch, or error contracts | `references/types-ownership-and-errors.md` |
| Async tasks, locks, channels, lifecycle, state machines, serialization, performance, security, or operational behavior | `references/async-state-and-boundaries.md` |
| Public APIs, crate boundaries, dependencies, Cargo features, or target support | `references/api-and-dependencies.md` |
| Unsafe code, FFI, raw pointers, atomics, layout, or native integration | `references/unsafe-and-ffi.md` |
| Enabling, changing, suppressing, or migrating compiler or Clippy lints | `references/lint-policy.md` |
| Miri, feature matrices, semver, coverage, property tests, fuzzing, concurrency testing, cross-target checks, mutation testing, benchmarks, or Dylint | `references/specialized-gates.md` |
| Installing or migrating repository-wide lint, formatting, dependency, unsafe-code, or CI policy | `references/policy-installation.md` plus every risk reference it selects |

Templates under `assets/` are reviewed starting points, not universal policy. The audit script may be executed without reading its source.

## Shared invariants

1. Read repository instructions and inspect the task-local code path, manifests, toolchain/MSRV, relevant tests, `git status`, and the current diff before editing. Preserve unrelated work and never use destructive cleanup commands.
2. Honor the pinned toolchain, declared `rust-version`, feature model, supported targets, generated-code boundaries, and existing quality commands. Do not upgrade or broaden scope unless the task requires it.
3. Fix the underlying problem with the smallest coherent change. Do not launder compiler, borrow-checker, lint, or test failures with convenient clones, allocations, dynamic types, panics, broader visibility, dependencies, or suppressions.
4. Preserve error evidence and domain facts. Validate untyped data at boundaries and keep owned core logic typed.
5. Do not edit generated, vendored, copied, binding-generated, migration-generated, or macro-expanded output as owned source. Fix its source or exclude it narrowly.
6. No temporary slop in the completed change: unexplained `TODO`, `FIXME`, `todo!`, or `unimplemented!`; ignored errors; dead alternatives; debug output; speculative abstractions; or unjustified exceptions.
7. Never introduce repository-wide policy, optional tools, dependency updates, lockfile churn, or formatter-wide rewrites during an ordinary engineering task unless explicitly required. Do not run `cargo fix`, `cargo clippy --fix`, or broad automatic rewrites on a dirty repository without reviewing the exact scope first.

## Work

1. Establish the behavioral contract and distinguish pre-existing failures from task-introduced failures.
2. Select and read the matching references above.
3. Implement or recommend the smallest change that preserves the applicable ownership, error, lifecycle, concurrency, unsafe, feature, target, and public-API constraints.
4. Run focused checks first, then the repository's canonical formatter, compiler, Clippy, tests, rustdoc, and policy gates in proportion to the affected features and targets.
5. Inspect the complete final diff. Apply the acceptance gate in `references/engineering-core.md` to owned changed code.

## Report

State the repository context and scope inspected, files changed, exact commands and results, fixed versus outstanding findings, every remaining exception or pre-existing failure, and anything not verified with the resulting risk. Never claim the repository is clean when a required gate was skipped or failed.
