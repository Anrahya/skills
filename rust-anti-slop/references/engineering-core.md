# Rust engineering core

Use this reference for every implementation, review, debugging, refactoring, or repair task in owned Rust code. It governs decisions the compiler and Clippy cannot prove.

## Decision hierarchy

When several implementations are possible, prefer in this order:

1. Correct behavior and explicit invariants.
2. Simple ownership and state transitions.
3. Small, local, reviewable change.
4. Strong types at boundaries and inside the domain.
5. Deterministic failure and testability.
6. Clear operational behavior: cancellation, shutdown, resource cleanup, observability.
7. Measured performance.
8. Extensibility only for a concrete present requirement.

Do not trade an earlier item for a later one without evidence.

## Scope and change discipline

- Understand the call path and data flow before editing.
- Change the smallest coherent surface that solves the real problem.
- Preserve public behavior unless the task explicitly changes it.
- Do not mix feature work, lint migration, dependency upgrades, formatting, and architecture refactors in one diff unless they are inseparable.
- Do not opportunistically rewrite neighboring code because a different style is possible.
- Delete obsolete code rather than commenting it out.
- Do not create speculative extension points, compatibility layers, aliases, adapters, or configuration knobs for hypothetical future use.
- Do not create a shared abstraction until there is actual shared behavior and the common contract is stable enough to name.
- Duplication of two short, evolving call sites can be safer than a premature abstraction. Reassess when the pattern is real.

## Behavioral proof and blast radius

Before editing:

- Derive the contract from the request plus observable current behavior, callers, tests, and documentation. Label facts and inferences.
- Name the observable outcome, non-goals, and cheapest trustworthy proof.
- For a bug, reproduce the same symptom through the same surface when safe and practical. If reproduction is blocked, preserve the strongest evidence and state the gap.
- For a changed type, API, state, protocol, persistence format, feature, or target, search for callers, constructors, trait implementations, serialized or persisted forms, conditional compilation, public consumers, tests, and failure, cancellation, and cleanup paths.
- Name the load-bearing invariants and what could break.

After editing:

- Exercise the narrowest real surface that proves the outcome and compare it with the baseline.
- Revisit every affected consumer and load-bearing invariant found before editing.
- Treat compilation, linting, and self-authored tests as supporting evidence, not substitutes when real behavior can be exercised.

## Verifiable sequencing

For multi-file, multi-crate, migration, or repository-wide work:

- Split the change into the smallest ordered units that each leave the repository coherent.
- End every unit with the most relevant proof checkpoint. Do not continue on a failed checkpoint; find the cause or revise the plan first.
- Migrate affected callers and remove the obsolete path in the same verifiable wave.
- Do not add a temporary shim, alias, dual path, or compatibility layer unless the final external contract requires it.
- If a unit disproves the design, re-plan instead of accumulating exceptions around it.

## Testing

Tests should prove behavior and failure modes, not implementation trivia.

- Every bug fix receives a regression test that fails before the fix when practical.
- Test public or meaningful behavior at the narrowest stable boundary.
- Unit-test pure logic, integration-test contracts between components, and end-to-end-test only critical flows.
- Prefer real lightweight implementations or fakes at actual boundaries over deep mocking.
- Do not mock the function under test or duplicate its implementation in assertions.
- Do not assert only that code does not panic.
- Test error paths, cancellation, timeouts, empty and maximal inputs, malformed data, restart or recovery, and resource cleanup where relevant.
- Avoid sleeps and real wall-clock timing. Inject clocks or use runtime time control.
- Avoid shared mutable global fixtures and order-dependent tests.
- Use temporary directories and files safely and cleanly.
- Do not update snapshots blindly. Review semantic changes.
- Property-test invariants with large input spaces.
- Fuzz parsers, codecs, protocol state, and untrusted boundary conversion.
- Concurrency tests must force or interleave meaningful states rather than rely on chance.
- Coverage is a map of untested areas, not a target that justifies low-value tests.

Tests may use `expect` with a specific setup-invariant message when repository policy permits it. Avoid raw `unwrap` because it gives poor failure context.

## Comments, documentation, and naming

Comments should explain an invariant, safety proof, cancellation or ordering behavior, external constraint, deliberate tradeoff, or justified lint exception. They should not narrate syntax, repeat names, preserve abandoned code, claim correctness without evidence, or compensate for a confusing design.

Names should use domain language and expose responsibility. Reject vague buckets such as `Utils`, `Common`, `Misc`, `Thing`, `Data`, `Manager`, or `Helper` unless the domain genuinely uses that term and the responsibility is narrow.

## Common agent-generated slop triggers

Treat these as review triggers, not automatic convictions:

- cloning immediately after a borrow error,
- wrapping state in `Arc<Mutex<_>>` before defining owners,
- adding a trait with one implementation and one mock,
- returning `Box<dyn Error>` from core logic,
- using `serde_json::Value` throughout the application,
- spawning tasks and dropping handles,
- using unbounded channels by default,
- adding retries around every error,
- creating `FooManager`, `FooService`, `FooFactory`, and `FooBuilder` for a small operation,
- adding generic parameters and associated types for hypothetical reuse,
- splitting ten lines across six modules,
- adding comments to every statement,
- making fields or functions public for tests,
- converting compiler errors into runtime errors through boxing or dynamic typing,
- replacing exhaustive matches with `_`,
- suppressing lint groups globally,
- adding `#[allow(dead_code)]` to speculative work,
- adding `String` conversions to solve lifetime design,
- using `async_trait` or boxed futures without examining native async trait support and object-safety needs,
- using a cache without invalidation or memory limits,
- using a background task where a direct call is simpler,
- turning a deterministic state transition into event soup,
- creating configuration for constants that are not operationally configurable,
- writing tests that mirror internal methods rather than user-visible behavior.

For each trigger, inspect intent and context. Fix the underlying design; do not perform pattern substitution.

## Acceptance gate

A change is not complete merely because it compiles. For owned changed code, require all of the following unless a documented repository constraint makes one inapplicable:

- no compiler, Clippy, rustdoc, formatter, or required policy warnings,
- no ignored `Result`, future, task handle, lock guard, or other must-use value,
- no production `unwrap`, `expect`, `panic!`, `unreachable!`, `todo!`, or `unimplemented!` without a proven invariant and a narrowly justified exception,
- no borrow-checker appeasement clone or allocation,
- no speculative trait, generic, wrapper, manager, helper, service, factory, builder, or abstraction without present evidence,
- no dynamic dispatch for a closed set that an enum or direct call models more clearly,
- no `Arc<Mutex<_>>` or unbounded channel without an ownership or backpressure reason,
- no task spawned without lifecycle, cancellation, error, and shutdown ownership,
- no stringly typed internal protocol or unvalidated untyped boundary data,
- no lossy numeric conversion without explicit checked semantics,
- no new unsafe code without isolated invariants, safety documentation, and appropriate tests,
- no dependency without a concrete reason, reviewed features, and understood maintenance and security cost,
- no widened public API, visibility, or re-export surface without need,
- no tests that depend on sleeps, real wall-clock timing, global state, network flakiness, or unspecified ordering when deterministic seams are practical,
- no comments that narrate obvious syntax; comments explain invariants, tradeoffs, non-obvious intent, or external constraints,
- no dead branches, duplicated state, stale caches without invalidation, or impossible-state encodings left representable without reason,
- no lint or configuration exception lacking a precise reason and narrow scope,
- the observable outcome is proven through the narrowest real surface available, with any verification gap reported,
- affected consumers, contracts, and load-bearing invariants have been re-checked,
- multi-step work did not proceed past a failed proof checkpoint,
- retryable or replayable external effects have explicit and tested duplicate semantics.
