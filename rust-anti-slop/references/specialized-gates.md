# Specialized Rust quality gates

Add these gates only when they control a real project risk. Every tool adds installation, update, CI, and interpretation cost. A tool is justified when its failure mode is relevant and its output is actionable.

## 1. Baseline gate

The baseline for owned Rust code is:

```bash
cargo fmt --all -- --check
cargo check --workspace --all-targets --all-features --locked
cargo clippy --workspace --all-targets --all-features --locked -- -D warnings
cargo test --workspace --all-targets --all-features --locked
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --all-features --no-deps --locked
```

Adapt feature and workspace flags to the repository. Do not use `--all-features` when features are mutually exclusive, target-specific, or intentionally unsupported together.

## 2. `cargo-deny`: dependency policy

Use when the project consumes third-party crates and wants deterministic policy for:

- known advisories,
- allowed licenses,
- banned crates or versions,
- wildcard dependency requirements,
- duplicate-version review,
- allowed registries and git sources.

Commands:

```bash
cargo deny init
cargo deny check
```

Rules:

- Generate a current config before merging the asset template.
- Do not copy a license allowlist without matching the project's distribution/legal policy.
- Every ignored advisory, license exception, allowed git source, banned-crate wrapper, duplicate skip, or skip tree requires a reason.
- Keep unknown registries and unknown git sources denied unless the repository deliberately uses them.
- `multiple-versions = "warn"` is usually more honest than universal denial; inspect with `cargo tree --duplicates`.
- Do not use cargo-deny as a substitute for reviewing direct dependencies and feature flags.

## 3. Miri: unsafe and undefined behavior

Use for crates with unsafe code or low-level invariants that Miri can execute. Miri runs programs/tests in an interpreter and detects classes of undefined behavior.

Typical flow:

```bash
rustup +nightly component add miri
cargo +nightly miri setup
cargo +nightly miri test
```

Constraints:

- Miri requires nightly and does not support every OS API, FFI call, or dependency.
- Run the subset that is meaningful and report exclusions honestly.
- Passing Miri is not a complete proof of soundness.
- Add deterministic tests that exercise unsafe invariants; an unexecuted unsafe path gains nothing from Miri.
- Keep the production toolchain unchanged unless the project already uses nightly; Miri can be a separate CI job.

## 4. `cargo-hack`: feature combinations

Use for libraries or applications with meaningful optional features.

Examples:

```bash
cargo hack check --workspace --feature-powerset --depth 2
cargo hack test --workspace --each-feature
cargo hack clippy --workspace --each-feature -- -D warnings
```

Design a bounded matrix. A full powerset can explode exponentially and may include intentionally invalid combinations.

Test at least:

- default features,
- no default features,
- each independent feature,
- known interacting feature groups,
- supported target-specific combinations,
- intentionally exclusive combinations as compile-fail/config validation where appropriate.

Do not claim `--all-features` proves feature correctness.

## 5. `cargo-semver-checks`: public library compatibility

Use for published crates or internal libraries with consumers that rely on semver-compatible APIs.

Typical command:

```bash
cargo semver-checks check-release
```

Use against the intended baseline release/branch. Review findings; generated APIs, cfg/feature differences, and intentional major-version changes require context.

Semver checks do not replace:

- behavioral compatibility tests,
- serialization/wire compatibility,
- database migration compatibility,
- feature/default behavior review,
- MSRV checks.

## 6. `cargo-llvm-cov`: coverage visibility

Use to identify important untested code paths, not to manufacture a vanity percentage.

Examples:

```bash
cargo llvm-cov --workspace --all-features
cargo llvm-cov --workspace --all-features --html
cargo llvm-cov --workspace --all-features --fail-under-lines <reviewed-threshold>
```

Rules:

- Exclude generated/bindings code only with a reason.
- Prefer risk-based thresholds per crate/subsystem over one arbitrary global number.
- Inspect uncovered error, cancellation, recovery, and boundary paths.
- Do not add assertions that merely execute lines without proving behavior.
- Coverage cannot prove concurrency interleavings, soundness, or correctness.

## 7. Property testing

Use for pure logic with broad input spaces and clear invariants, including:

- parsers and serializers,
- canonicalization,
- state-machine transitions,
- arithmetic/units,
- round trips,
- idempotence,
- ordering and deduplication,
- command/event reduction.

Properties should express domain truth, for example:

- `decode(encode(x)) == x` for supported values,
- normalization is idempotent,
- applying a rejected transition leaves state unchanged,
- resource accounting never becomes negative,
- parser never panics for arbitrary bytes.

Do not simply generate random examples without a meaningful property. Keep shrinking output reproducible and retain regression cases for discovered failures.

## 8. Fuzzing

Use `cargo-fuzz` or the repository's existing fuzz framework for untrusted binary/text input, codecs, protocol frames, archive formats, or state machines.

A fuzz target should:

- be deterministic for the same input,
- avoid network and wall-clock dependencies,
- bound memory/time where possible,
- assert meaningful invariants, not only no-panic,
- preserve crashing inputs as regression fixtures,
- exercise boundary conversion before trusted domain logic.

Fuzzing does not excuse weak input bounds or validation.

## 9. Loom or deterministic concurrency testing

Use Loom for custom synchronization algorithms or small concurrent state machines whose correctness depends on interleavings.

Good candidates:

- lock-free structures,
- custom atomics,
- once/init logic,
- task handoff state,
- shutdown races,
- channel coordination wrappers.

Poor candidates:

- large application integration tests,
- code dominated by unsupported external I/O,
- ordinary mutex-protected data with no subtle interleaving.

Keep the modeled state small. Assert safety and liveness properties where practical. Do not rely on repeated normal tests to probabilistically discover races.

## 10. Sanitizers and native integration

For FFI, native libraries, allocators, or platform-specific unsafe code, consider separate nightly/supported-target jobs for AddressSanitizer, LeakSanitizer, ThreadSanitizer, or platform tools.

Use only on supported targets/toolchains. Report unsupported combinations rather than silently skipping. Keep FFI ownership and unwind contracts documented regardless of sanitizer results.

## 11. Cross-target checks

For libraries and portable applications, run `cargo check` for every supported target family or representative target that changes cfg/dependency behavior.

Examples:

- Linux GNU and musl where both are supported,
- Windows MSVC,
- macOS,
- WASM,
- embedded target,
- 32-bit target where integer-size assumptions matter.

Do not claim portability from host-only CI. Cross-check build scripts and target cfgs; build scripts run on the host and must use Cargo-provided target variables correctly.

## 12. MSRV gate

If `rust-version` is a contract, test it explicitly with that toolchain. Keep dependency resolution compatible with the MSRV policy.

Do not lower MSRV by trial-and-error while ignoring dependency MSRVs. Do not raise MSRV because the development machine is newer unless the change is intentional and documented.

## 13. Mutation testing

Use mutation testing selectively for critical pure logic when ordinary coverage appears high but test strength is uncertain.

It is valuable for:

- authorization and validation rules,
- financial/resource calculations,
- state transitions,
- parsers and matching logic.

It is expensive and noisy for glue code, generated code, UI wrappers, and integration-heavy systems. Review surviving mutants; do not chase a perfect score with brittle implementation tests.

## 14. Benchmark and performance gates

Add benchmarks only for a real performance contract or known hot path.

- Use representative inputs and sizes.
- Prevent optimizer elimination.
- Separate throughput, latency, memory, allocation, and compile-time concerns.
- Store baselines carefully; CI noise can make tiny thresholds useless.
- Do not convert microbenchmark wins into architecture decisions without end-to-end evidence.
- Profile before adding unsafe, pooling, lock-free code, custom allocators, or complex zero-copy lifetimes.

## 15. Dylint: project-specific deterministic policy

Use Dylint only after recurring violations remain that Clippy, compiler lints, Cargo configuration, tests, or simple repository checks cannot express. Dylint loads custom Rust lints from dynamic libraries, allowing a repository to maintain its own lint collection.

High-value custom lint candidates for an agent/runtime codebase may include:

- `anyhow::Result` used outside binary/adapters,
- ignored `JoinHandle` from task spawning,
- unbounded channel construction outside an approved module,
- direct `std::env`, filesystem, process, network, or wall-clock access inside domain crates,
- `serde_json::Value` or `HashMap<String, Value>` in internal domain contracts,
- unsafe code outside a dedicated crate/module,
- direct database client usage outside persistence adapters,
- sleeping in tests,
- public fields on invariant-bearing domain types,
- task spawning without a supervisor wrapper,
- error conversion that drops source information,
- project-specific state transitions bypassing the owning API.

Before implementing a custom lint:

1. Collect several real occurrences.
2. Define the semantic violation and allowed cases.
3. Confirm a low false-positive detection strategy.
4. Decide whether a simpler Clippy disallowed path, test, API redesign, or grep-based repository check is sufficient.
5. Write pass/fail UI tests for the lint.
6. Pin and maintain its compatible toolchain because custom compiler lint APIs are unstable.
7. Provide narrow suppressions with reasons.

Do not start with dozens of custom lints. Encode only repeated, objective failures whose prevention pays for maintenance.

## 16. Gate tiers

A practical split:

### Pull request: fast required

- format check,
- cargo check for normal/default profile,
- Clippy for owned changed workspace,
- unit/integration tests,
- dependency policy if fast,
- targeted feature/target checks touched by the change.

### Main/nightly: comprehensive required

- full feature matrix,
- all supported targets,
- Miri subset,
- coverage report,
- semver check,
- fuzz smoke/regression corpus,
- slower integration/end-to-end tests,
- mutation testing for selected critical crates.

### Release

- reproducible locked build,
- full required target matrix,
- advisories/licenses/sources,
- semver and public artifact review,
- migration/compatibility tests,
- changelog/version checks,
- performance checks where contractual.

A slow gate is not useful if nobody runs or owns it. Document cadence, failure ownership, and remediation.
