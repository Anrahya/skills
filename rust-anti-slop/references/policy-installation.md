# Repository policy installation and migration

Read this reference only when asked to add, migrate, or enforce repository-wide lint, formatting, dependency, unsafe-code, or CI policy. Do not apply it during ordinary implementation or review work.

## 1. Inspect the repository and establish the baseline

Run the bundled read-only audit first. It requires Python 3.11 or newer:

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
- declared edition and `rust-version` or MSRV,
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

Record the pre-existing state. Separate baseline failures from failures introduced by the policy setup.

## 2. Classify applicable profiles

Every owned crate receives the baseline profile. Add specialized profiles only where relevant:

- **Public library:** API documentation, semver, panic and error contracts, feature compatibility, and public dependency exposure.
- **Application or binary:** explicit process boundaries, configuration parsing, shutdown, logging, and top-level error reporting.
- **Async or service:** cancellation, task ownership, bounded backpressure, blocking boundaries, lock usage, and `Send` requirements.
- **Unsafe, FFI, or system:** isolated unsafe surface, documented invariants, Miri where supported, ABI and layout checks, and platform-specific tests.
- **Parser, protocol, or serialization:** boundary validation, fuzz or property tests, numeric conversion checks, and stable wire representations.
- **Feature-heavy or cross-platform:** feature matrix checks, target checks, and no accidental all-features assumptions.
- **`no_std` or embedded:** allocator, panic strategy, target, and host-tool limitations.
- **Generated, proc-macro, or build output:** generator-level checks or narrow exclusions; never hand-clean generated output.

Read `lint-policy.md` before selecting lints and `specialized-gates.md` before adding optional tools. Read the other risk references selected by these profiles.

## 3. Establish the active toolchain and supported lint set

Honor the repository's pinned toolchain. If none is pinned, use the documented or current active toolchain; do not silently create a pin unless requested.

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

List supported lints before writing configuration:

```bash
cargo clippy -- -W help
rustc -W help
```

Do not add a lint the pinned toolchain does not recognize. Preserve the declared `rust-version`; when MSRV is older than the active toolchain, ensure Clippy respects it.

## 4. Integrate Cargo lint policy

Use `../assets/Cargo.lints.toml` as a reviewed starting point, not a blind paste.

For a workspace:

1. Merge applicable settings into `[workspace.lints.rust]` and `[workspace.lints.clippy]` in the workspace root.
2. Add the following to every owned member crate that should inherit the policy:

```toml
[lints]
workspace = true
```

Workspace lints are not implicitly inherited. Confirm each intended member opts in. Do not add `[lints]` to a virtual workspace root where it is ignored; use `[workspace.lints]` there.

For a single package, use `[lints.rust]` and `[lints.clippy]` in that package manifest.

Policy rules:

- Set `clippy::all` to `deny` through Cargo lint configuration.
- Cherry-pick high-signal pedantic, restriction, nursery, and cargo lints. Do not enable those groups wholesale.
- Set `unused_must_use` to `deny`.
- Set `unreachable_pub` to `deny` for internal crates and applications; review public-library behavior first.
- Set `unexpected_cfgs` to `deny` after declaring legitimate custom cfg names.
- Use `unsafe_code = "forbid"` only when the whole crate or workspace must remain safe and no valid exception can exist.
- Otherwise use `unsafe_code = "deny"`, isolate legitimate unsafe code, and permit it only at a dedicated boundary with a specific reason.
- Keep `unsafe_op_in_unsafe_fn = "deny"` whenever unsafe code exists.
- Treat warnings as CI failures only with a pinned or reviewed toolchain strategy.

Do not duplicate lint policy across crate roots unless Cargo lint tables cannot be used.

## 5. Configure Clippy behavior and project-specific bans

Merge `../assets/clippy.toml` with existing configuration. Preserve existing values unless they weaken explicitly requested policy or are objectively obsolete.

Use `disallowed-methods`, `disallowed-types`, `disallowed-macros`, and `await-holding-invalid-types` only for repository-specific invariants. Every ban requires:

- a clear failure mode,
- an approved replacement or boundary,
- a scope where the replacement is valid,
- a reason embedded in configuration,
- a migration plan for existing uses.

Do not globally ban `std::sync::Mutex` in async code; it can be correct when not held across `.await`. Ban concrete misuse, not folklore.

## 6. Preserve formatting policy

Use existing rustfmt configuration. If none exists and installation was requested, `../assets/rustfmt.toml` is a conservative starting point.

Do not combine policy installation with unrelated formatting churn. Format owned changed source where possible, then verify the repository with:

```bash
cargo fmt --all -- --check
```

Never use unstable rustfmt options unless the repository deliberately pins nightly for formatting.

## 7. Add dependency and supply-chain checks deliberately

Do not add a library dependency merely to implement policy or avoid a small clear function. Do not reimplement complex, security-sensitive, or standards-heavy functionality merely to avoid a dependency.

Inspect:

```bash
cargo tree --duplicates
cargo tree --edges features
```

Duplicate versions are a review signal, not an automatic error. Determine whether they are avoidable, type-incompatible, compile-costly, or security-relevant before changing them.

If dependency policy is in scope:

1. Install or use the repository's existing `cargo-deny` version without upgrading unrelated tools.
2. Prefer generating a current baseline with `cargo deny init`, then merge the reviewed policy from `../assets/deny.toml`.
3. Configure advisories, licenses, banned crates, wildcard requirements, registries, and git sources explicitly.
4. Give every ignored advisory, license exception, skipped duplicate, allowed git source, or banned-crate wrapper a concrete reason.
5. Match the license policy to the project's distribution and legal requirements; never invent an allowlist.

Do not run `cargo update` unless dependency remediation was requested.

## 8. Add deterministic quality commands and CI gates

Integrate with the existing task runner instead of creating a competing command surface. Prefer one canonical command used by both CI and agents.

The baseline normally includes:

```bash
cargo fmt --all -- --check
cargo check --workspace --all-targets --all-features --locked
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo test --workspace --all-targets --all-features --locked
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --all-features --no-deps --locked
cargo deny check
```

Adapt rather than copy blindly:

- Omit `--workspace` for a non-workspace package when appropriate.
- Do not use `--all-features` when features are mutually exclusive, target-specific, or unsupported together. Use an explicit matrix.
- Do not force `--locked` where the repository intentionally tests dependency resolution without a lockfile; explain the choice.
- Run `cargo deny check` only with an accepted policy and installed tool.
- Separate fast pull-request gates from slow specialized gates, but give slow gates a defined cadence.
- Pin the Rust toolchain used for warning-as-error CI or use reviewed updates.

Do not hide required-gate failures with `continue-on-error`, `|| true`, ignored exit codes, or warning-only CI.

## 9. Migrate findings without laundering the design

When strict lints expose existing code, classify findings before editing:

1. Correctness and safety.
2. Ignored errors, panics, unsafe invariants, cancellation, and resource lifetime.
3. Type or ownership evidence loss, unnecessary cloning or allocation, stringly typed boundaries, and broad APIs.
4. Readability and maintainability.
5. Subjective style or false positives.

Read `engineering-core.md` and every matching risk reference before changing owned source. Never resolve findings by:

- replacing `unwrap()` with `expect("should work")` without proving the invariant,
- replacing indexing with `.get(...).unwrap()`,
- cloning to satisfy borrow checking without ownership analysis,
- wrapping everything in `Arc<Mutex<_>>`, `Box`, or `dyn Trait`,
- hiding a complex type behind an alias without improving the design,
- converting typed errors into strings or `anyhow` inside domain or library layers,
- discarding original errors with `map_err(|_| ...)`, `.ok()`, or `let _ =`,
- adding wildcard match arms that hide new enum variants,
- widening visibility for tests or modules,
- adding a trait solely to mock one implementation,
- suppressing a lint at crate or workspace level for one call site,
- changing dependency features without checking behavior,
- adding `#[allow(dead_code)]` around speculative code,
- rewriting clear code into clever iterator chains for style.

## 10. Run specialized gates where justified

Use `specialized-gates.md` to select additional checks such as Miri, `cargo-hack`, `cargo-semver-checks`, coverage, property tests, fuzzing, deterministic concurrency tests, cross-target checks, or Dylint.

Do not install every tool. Additional machinery must control a concrete risk that pays for its maintenance cost.

## 11. Review the final diff as code

Before declaring completion:

- inspect every changed file and the complete diff,
- confirm there is no unrelated formatting or lockfile churn,
- confirm every intended workspace member inherits the lint policy,
- search for new `allow`, `expect`, `unwrap`, `panic`, `todo`, `unimplemented`, `dbg`, `println`, `.ok()`, ignored results, broad value maps, unbounded channels, detached tasks, and unsafe blocks,
- verify every suppression and exception has a specific reason,
- verify generated and vendored exclusions are narrow,
- confirm the policy works on the pinned toolchain or MSRV and intended feature or target matrix,
- run the canonical full check,
- distinguish pre-existing failures from introduced failures,
- document how future agents and humans run the same gates.

## Report

In addition to the skill's normal report, state the toolchain and MSRV inspected, selected policy profiles, Cargo lint inheritance changes, Clippy, rustfmt, and cargo-deny changes, optional tools and the risks they control, and any policy deliberately omitted because it would conflict, create false positives, or encourage worse code.
