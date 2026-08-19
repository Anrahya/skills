---
name: rust-anti-slop
description: Write, review, debug, refactor, harden, and govern Rust or Cargo repositories with an evidence-driven anti-slop discipline. Use for Rust implementation and review tasks; resolving compiler or Clippy findings; assessing ownership, errors, async lifecycle, unsafe/FFI, dependencies, features, APIs, or tests; or installing and migrating lint, formatting, dependency, and CI policy. Adapt to the pinned toolchain, MSRV, crate roles, features, targets, and existing conventions.
compatibility: Requires filesystem and command-execution access to a local Rust or Cargo repository. The bundled audit requires Python 3.11+. Optional gates may require rustup, cargo-deny, cargo-nextest, cargo-hack, cargo-llvm-cov, cargo-semver-checks, Miri, cargo-fuzz, or Dylint.
metadata:
  version: "1.1.0"
---

# Rust anti-slop

Apply a strict, evidence-driven Rust engineering discipline to owned code, or install that discipline as repository policy when requested. The objective is not to maximize lint counts. The objective is to make incorrect, vague, wasteful, difficult-to-review, and unjustified code hard to introduce while avoiding rewrites that make the design worse.

Treat compiler and lint findings as evidence of a possible defect, not as permission to mechanically mutate code. Preserve behavior, repository conventions, public contracts, unrelated work, and supported targets.

## Choose the workflow

- **Engineering and review:** Use the engineering workflow for implementation, debugging, review, refactoring, hardening, or resolving existing findings. Do not install new repository-wide policy or optional tools unless the task requires it.
- **Policy installation and migration:** Use the full installation workflow when asked to add, migrate, or enforce lint, formatting, dependency, unsafe-code, or CI policy across a crate or workspace.

## Non-negotiable operating rules

1. Inspect before editing. Do not infer the workspace layout, toolchain, MSRV, feature model, runtime, or crate boundaries from one file.
2. Read repository instructions first. `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, task-runner files, and CI are authoritative unless the user explicitly overrides them.
3. Check `git status` and the relevant diff before touching files. Preserve unrelated work. Never use destructive cleanup commands.
4. Honor the pinned toolchain and declared `rust-version`. Do not upgrade Rust, editions, dependencies, lockfiles, or CI actions unless the task requires and justifies it.
5. Verify lint names against the repository's active Clippy version before changing lint policy. Do not trust remembered lint catalogs.
6. Do not enable all of `clippy::restriction`, `clippy::nursery`, `clippy::pedantic`, or `clippy::cargo` blindly. Select high-signal lints that fit this repository. Some restriction lints conflict; nursery lints may be incomplete; pedantic lints intentionally produce false positives.
7. Do not make lint pass by adding clones, allocations, dynamic dispatch, `Arc`, `Mutex`, `Box`, `String`, broad trait objects, broader visibility, lossy casts, `unwrap`, `expect`, panic paths, or dependencies unless the design independently requires them.
8. Do not suppress a lint globally to silence one local case. Use the narrowest possible `#[expect(..., reason = "...")]` or `#[allow(..., reason = "...")]` only after proving that the code is correct and the lint is unsuitable there.
9. Do not run `cargo clippy --fix`, `cargo fix`, formatter-wide rewrites, or dependency updates on a dirty repository without reviewing the exact scope first.
10. Do not edit generated, vendored, copied, binding-generated, migration-generated, or macro-expanded source as though it were owned application code. Fix the generator, exclude the generated path narrowly, or document why it cannot be checked.
11. A clean lint run is not proof of good architecture. Apply the engineering policy in `references/rust-engineering-policy.md` to owned code and while resolving findings.
12. No "temporary" slop. Do not leave unexplained `TODO`, `FIXME`, `todo!`, `unimplemented!`, dead code, commented-out alternatives, ignored errors, debug output, or placeholder abstractions in the completed change.

## Engineering and review workflow

1. Inspect the task-local code path, repository instructions, relevant manifests, pinned toolchain/MSRV, existing tests, and current diff. Read `references/rust-engineering-policy.md` before making non-trivial design or repair decisions.
2. Establish the behavioral contract and the relevant ownership, error, lifecycle, concurrency, unsafe, feature, target, and public-API constraints. Distinguish pre-existing failures from task-introduced failures.
3. Implement or recommend the smallest coherent change that fixes the underlying problem. Preserve types and error evidence; do not launder borrow-checker, lint, or test failures with clones, allocations, panics, broad dynamic types, or suppressions.
4. Apply specialized guidance only when the risk exists. Read `references/lint-policy.md` when changing lints and `references/specialized-gates.md` when unsafe code, feature matrices, parsers, concurrency, semver, coverage, fuzzing, or cross-target behavior justifies an additional gate.
5. Run the repository's canonical checks with the intended features and targets. Prefer focused tests first, then the relevant formatter, compiler, Clippy, test, rustdoc, and policy gates in proportion to the change.
6. Inspect the final diff and apply the acceptance gate below. Report exact commands and results, remaining exceptions, pre-existing failures, and anything not verified.

## Policy installation and migration workflow

### 1. Inspect the repository and establish the baseline

Run the bundled read-only audit first:

```bash
python3 <skill-directory>/scripts/audit_repo.py .
```

Treat its output as leads for manual inspection, not semantic proof.

Then inspect at least:

- repository instructions and contribution rules,
- `git status --short` and the relevant diff,
- root and member `Cargo.toml` files,
- `Cargo.lock`, `rust-toolchain.toml`, `rust-toolchain`, and `.cargo/config.toml`,
- `rustfmt.toml`, `.rustfmt.toml`, `clippy.toml`, `.clippy.toml`, and `deny.toml`,
- workspace members, default members, excluded crates, and resolver version,
- each crate's role: binary, public library, internal library, proc macro, build helper, FFI wrapper, generated bindings, test support, benchmark, or example,
- declared edition and `rust-version`/MSRV,
- feature definitions, default features, mutually exclusive features, target-specific dependencies, and supported targets,
- `#![no_std]`, embedded, WASM, mobile, Windows, Unix, or cross-compilation constraints,
- async runtime and concurrency model,
- current `unsafe` usage, FFI, raw pointers, atomics, custom allocators, memory mapping, or platform APIs,
- serialization and untyped boundary data,
- build scripts and procedural macros,
- existing CI, pre-commit hooks, task runners, and quality commands,
- generated and vendored paths that must not receive owned-source policy,
- current warnings and failing tests before policy changes.

Use `cargo metadata --format-version 1 --no-deps --locked` when Cargo is available. If the repository intentionally has no lockfile, report that metadata was skipped rather than creating one merely for inspection.

Record the pre-existing state. If baseline checks already fail, separate those failures from failures introduced by the anti-slop setup.

### 2. Classify which policy profiles apply

Every owned crate receives the baseline profile. Add specialized profiles only where relevant:

- **Public library:** API documentation, semver, panic/error contracts, feature compatibility, and public dependency exposure.
- **Application/binary:** explicit process boundaries, configuration parsing, shutdown, logging, and top-level error reporting.
- **Async/service:** cancellation, task ownership, bounded backpressure, blocking boundaries, lock usage, and `Send` requirements.
- **Unsafe/FFI/system:** isolated unsafe surface, documented invariants, Miri where supported, ABI/layout checks, and platform-specific tests.
- **Parser/protocol/serialization:** boundary validation, fuzz/property tests, numeric conversion checks, and stable wire representations.
- **Feature-heavy/cross-platform:** feature matrix checks, target checks, and no accidental all-features assumptions.
- **`no_std`/embedded:** allocator, panic strategy, target, and host-tool limitations.
- **Generated/proc-macro/build output:** generator-level checks or narrow exclusions; never hand-clean generated output.

Read `references/lint-policy.md` before selecting lints and `references/specialized-gates.md` before adding optional tools.

### 3. Establish the active toolchain and supported lint set

Honor the repository's pinned toolchain. If none is pinned, use the repository's documented toolchain or current active toolchain; do not silently create a pin unless requested.

Inspect versions:

```bash
rustc -Vv
cargo -V
cargo clippy -V
cargo fmt --version
```

If Clippy or rustfmt is missing and rustup manages the active toolchain, install only the missing components for that toolchain:

```bash
rustup component add clippy rustfmt
```

List supported lints using the active toolchain before writing configuration:

```bash
cargo clippy -- -W help
rustc -W help
```

Do not add a lint that the pinned toolchain does not recognize. When the MSRV is older than the active toolchain, preserve the declared `rust-version` and ensure Clippy is configured to respect it.

### 4. Integrate Cargo lint policy

Use `assets/Cargo.lints.toml` as a reviewed starting point, not as a blind paste.

For a workspace:

1. Merge applicable settings into `[workspace.lints.rust]` and `[workspace.lints.clippy]` in the workspace root.
2. Add this to every owned member crate that should inherit the policy:

```toml
[lints]
workspace = true
```

Workspace lints are not implicitly inherited. Confirm each member opts in. Do not add `[lints]` to a virtual workspace root where it is ignored; use `[workspace.lints]` there.

For a single-package repository, use `[lints.rust]` and `[lints.clippy]` in that package manifest instead of workspace tables.

Policy rules:

- Set `clippy::all` to `deny` through Cargo lint configuration.
- Cherry-pick high-signal pedantic, restriction, nursery, and cargo lints. Do not enable those groups wholesale.
- Set `unused_must_use` to `deny`.
- Set `unreachable_pub` to `deny` for internal crates and applications; review public-library behavior before enabling.
- Set `unexpected_cfgs` to `deny` after declaring legitimate custom cfg names.
- Use `unsafe_code = "forbid"` only when the whole crate/workspace is intentionally safe and no valid exception is required.
- Otherwise use `unsafe_code = "deny"`, isolate the smallest legitimate unsafe surface, and permit it only at a dedicated crate/module boundary with a specific reason.
- Keep `unsafe_op_in_unsafe_fn = "deny"` whenever unsafe code exists.
- Treat warnings as CI failures only with a pinned/reviewed toolchain strategy. Do not let an unpinned compiler update break main unexpectedly.

Do not duplicate lint policy across crate roots unless the repository cannot use Cargo lint tables. Central policy is easier to review and harder to drift.

### 5. Configure Clippy behavior and project-specific bans

Merge `assets/clippy.toml` with existing Clippy configuration. Preserve existing values unless they weaken an explicitly requested strict policy or are objectively obsolete.

Use Clippy's `disallowed-methods`, `disallowed-types`, `disallowed-macros`, and `await-holding-invalid-types` only for repository-specific invariants. Examples include an unbounded channel constructor in a service that requires backpressure, wall-clock access outside a clock adapter, or untyped JSON values outside boundary crates.

Never add a ban because a type or method "looks bad." A ban requires:

- a clear failure mode,
- an approved replacement or boundary,
- a scope where the replacement is valid,
- a reason embedded in configuration,
- a migration plan for existing uses.

Do not globally ban `std::sync::Mutex` in async code; a synchronous mutex can be correct when it is not held across `.await`. Ban concrete misuse, not folklore.

### 6. Preserve formatting policy

Use the repository's existing rustfmt configuration. If none exists and the user requested installation, `assets/rustfmt.toml` is a conservative starting point.

Do not combine anti-slop installation with unrelated formatting churn. Run formatting only on owned changed source where possible, then verify the whole repository with:

```bash
cargo fmt --all -- --check
```

Never use unstable rustfmt options unless the repository deliberately pins nightly for formatting.

### 7. Add dependency and supply-chain checks deliberately

Do not add a Rust library dependency merely to implement policy or avoid writing a small clear function. Conversely, do not reimplement complex, security-sensitive, or standards-heavy functionality merely to avoid a dependency.

Inspect:

```bash
cargo tree --duplicates
cargo tree --edges features
```

Duplicate versions are a review signal, not an automatic error. Determine whether they are avoidable, type-incompatible, compile-costly, or security-relevant before changing them.

If dependency policy is in scope:

1. Install or use the repository's existing `cargo-deny` version without upgrading unrelated tools.
2. Prefer generating a current baseline with `cargo deny init` and then merging the reviewed policy from `assets/deny.toml`.
3. Configure advisories, licenses, banned crates, wildcard requirements, registries, and git sources explicitly.
4. Every ignored advisory, license exception, skipped duplicate, allowed git source, or banned-crate wrapper must include a concrete reason.
5. Do not invent a license allowlist. Match the project's distribution model and legal policy.

Do not run `cargo update` as part of installation unless the user requested dependency remediation.

### 8. Add deterministic quality commands and CI gates

Integrate with the repository's existing task runner instead of creating a competing command surface. Prefer one canonical command such as `just check`, `make check`, `cargo xtask check`, or a documented script that CI and agents both run.

The baseline gate normally includes:

```bash
cargo fmt --all -- --check
cargo check --workspace --all-targets --all-features --locked
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo test --workspace --all-targets --all-features --locked
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --all-features --no-deps --locked
cargo deny check
```

Adapt rather than copy blindly:

- Omit `--workspace` for a non-workspace package if repository commands already do so.
- Do not use `--all-features` when features are mutually exclusive or target-specific. Use an explicit feature matrix instead.
- Do not force `--locked` where the repository intentionally tests dependency resolution without a lockfile, but explain the choice.
- `cargo deny check` is conditional on an accepted `deny.toml` policy and installed tool.
- Keep fast pull-request gates separate from slow specialized gates, but ensure slow gates run on a defined schedule or before release.
- Pin the Rust toolchain used for warning-as-error CI, or use an automated reviewed update process.

Do not hide failures with `continue-on-error`, shell `|| true`, ignored exit codes, or warning-only CI for a gate designated as required.

### 9. Migrate existing findings without laundering the design

When strict lints expose existing code, classify findings before editing:

1. **Correctness and safety:** fix first.
2. **Ignored errors, panics, unsafe invariants, cancellation, and resource lifetime:** fix next.
3. **Type/ownership evidence loss, unnecessary cloning/allocation, stringly typed boundaries, and broad APIs:** redesign locally.
4. **Readability and maintainability:** simplify without changing behavior.
5. **Subjective style or false positive:** use a narrow justified expectation/allow or do not enable that lint.

Never resolve findings with these laundering moves:

- changing `unwrap()` to `expect("should work")` without proving the invariant,
- changing indexing to `.get(...).unwrap()` or equivalent panic camouflage,
- cloning values to satisfy borrow checking without ownership analysis,
- wrapping everything in `Arc<Mutex<_>>`, `Box`, or `dyn Trait`,
- replacing a complex type with a type alias while leaving the design equally complex,
- converting typed errors into strings or `anyhow` inside domain/library layers,
- discarding an original error with `map_err(|_| ...)`, `.ok()`, or `let _ =`,
- adding `_` wildcard match arms that hide new enum variants,
- widening visibility so tests or modules can reach internals,
- adding a trait solely to mock one concrete implementation,
- suppressing a lint at crate/workspace level for one call site,
- disabling default features or changing dependency features without checking behavior,
- adding `#[allow(dead_code)]` around speculative or abandoned code,
- rewriting working code into clever iterator chains only to satisfy style preferences.

Use the detailed repair rules in `references/rust-engineering-policy.md`.

### 10. Run specialized gates where the risk justifies them

Use `references/specialized-gates.md` to select additional checks. Typical examples:

- Miri for unsafe code and low-level invariants,
- `cargo-hack` for meaningful feature combinations,
- `cargo-semver-checks` for published libraries,
- `cargo-llvm-cov` for coverage visibility,
- property tests and fuzzing for parsers, protocols, codecs, and boundary conversion,
- Loom or deterministic concurrency tests for synchronization algorithms,
- target-specific checks for supported operating systems and architectures,
- Dylint only for recurring project-specific violations that Clippy/configuration cannot express.

Do not install every tool into every repository. Additional machinery must pay for its maintenance cost with a concrete risk it controls.

### 11. Review the final diff as code, not configuration plumbing

Before declaring completion:

- inspect every changed file and the complete diff,
- confirm no unrelated formatting or lockfile churn,
- confirm all workspace members intended to inherit lints actually do,
- search for new `allow`, `expect`, `unwrap`, `expect`, `panic`, `todo`, `unimplemented`, `dbg`, `println`, `.ok()`, ignored `Result`, broad JSON/value maps, unbounded channels, detached tasks, and new unsafe blocks,
- verify every suppression and exception has a specific reason,
- verify generated or vendored exclusions are narrow,
- confirm the policy works on the pinned toolchain/MSRV and intended feature/target matrix,
- run the repository's canonical full check,
- distinguish pre-existing failures from introduced failures,
- ensure documentation tells future agents and humans how to run the same gates.

## Rust anti-slop acceptance gate

A change is not complete merely because it compiles. For owned changed code, require all of the following unless a documented repository constraint makes one inapplicable:

- no compiler, Clippy, rustdoc, formatter, or required policy warnings,
- no ignored `Result`, future, task handle, lock guard, or other must-use value,
- no production `unwrap`, `expect`, `panic!`, `unreachable!`, `todo!`, or `unimplemented!` without a proven invariant and a narrowly justified exception,
- no borrow-checker appeasement clone or allocation,
- no speculative trait, generic, wrapper, manager, helper, service, factory, builder, or abstraction without present evidence,
- no dynamic dispatch for a closed set that an enum or direct call models more clearly,
- no `Arc<Mutex<_>>` or unbounded channel without an ownership/backpressure reason,
- no task spawned without lifecycle, cancellation, error, and shutdown ownership,
- no stringly typed internal protocol or unvalidated untyped boundary data,
- no lossy numeric conversion without explicit checked semantics,
- no new unsafe code without isolated invariants, safety documentation, and appropriate tests,
- no dependency without a concrete reason, reviewed features, and understood maintenance/security cost,
- no widened public API, visibility, or re-export surface without need,
- no tests that depend on sleeps, real wall-clock timing, global state, network flakiness, or unspecified ordering when deterministic seams are practical,
- no comments that narrate obvious syntax; comments explain invariants, tradeoffs, non-obvious intent, or external constraints,
- no dead branches, duplicated state, stale caches without invalidation, or impossible-state encodings left representable without reason,
- no lint/configuration exception lacking a precise reason and narrow scope.

## Final report

Always report clearly:

- task scope and repository context inspected,
- files added or changed,
- commands run and exact results,
- findings fixed versus findings left outstanding,
- every remaining suppression, exception, generated-code exclusion, or pre-existing failure,
- anything not verified and the resulting risk.

For policy installation or migration, also report:

- repository and toolchain/MSRV inspected,
- policy profiles selected and why,
- Cargo lint tables and inheritance changes,
- Clippy/rustfmt/cargo-deny configuration changes,
- optional tools added and the risk each controls,
- any policy intentionally not enabled because it would create false positives, conflict with the project, or encourage worse code.

Do not claim the repository is clean if any required gate was not run or did not pass.
