# Rust anti-slop engineering policy

Use this reference while writing, reviewing, debugging, refactoring, or fixing lint findings in owned Rust code. It governs decisions that the compiler and Clippy cannot prove.

## 1. Decision hierarchy

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

## 2. Scope and change discipline

- Understand the call path and data flow before editing.
- Change the smallest coherent surface that solves the real problem.
- Preserve public behavior unless the task explicitly changes it.
- Do not mix feature work, lint migration, dependency upgrades, formatting, and architecture refactors in one diff unless they are inseparable.
- Do not opportunistically rewrite neighboring code because a different style is possible.
- Delete obsolete code rather than commenting it out.
- Do not create speculative extension points, compatibility layers, aliases, adapters, or configuration knobs for hypothetical future use.
- Do not create a shared abstraction until there is actual shared behavior and the common contract is stable enough to name.
- Duplication of two short, evolving call sites can be safer than a premature abstraction. Reassess when the pattern is real.

## 3. Types are evidence

Use the type system to preserve facts already known by the program.

Prefer:

- newtypes for identifiers, units, validated strings, and values with domain invariants,
- enums for closed state machines and finite variants,
- structs with named fields over position-heavy tuples,
- non-empty/container types when emptiness is invalid,
- typed timestamps, durations, byte counts, sequence numbers, and protocol versions,
- validated boundary types constructed through fallible constructors,
- private fields and constructors that maintain invariants,
- exhaustive matching when new variants must force review.

Reject without specific justification:

- internal `serde_json::Value`, `HashMap<String, Value>`, or `HashMap<String, String>` where keys and value kinds are known,
- booleans whose meaning is unclear at call sites,
- multiple booleans that encode a state machine,
- sentinel numbers or strings,
- `Option<T>` where absence is not a valid state,
- `Result<T, String>` in non-trivial code,
- `Box<dyn Error>` or `anyhow::Error` crossing domain/library API boundaries,
- generic `Context`, `Data`, `Info`, `Payload`, `Manager`, `Helper`, `Util`, `Service`, or `Handler` names that conceal responsibility,
- type aliases used only to hide an unreadable type rather than improve the model,
- wildcard enum matches that silently absorb future variants.

### Boundary rule

Untyped or weakly typed data may exist at external boundaries: JSON, environment variables, CLI arguments, database rows, network frames, plugin messages, or FFI. Parse and validate once at the boundary. After successful parsing, pass typed domain values inward. Do not repeatedly inspect strings and JSON throughout the core.

## 4. Ownership and borrowing

Do not treat the borrow checker as an obstacle to silence. It is exposing an ownership decision.

Before adding `clone()`, answer:

1. Who should own the value after this operation?
2. Is the clone semantically required, or only convenient?
3. What is cloned: pointer metadata, a small copy-like value, or heap-backed data?
4. How often is the path executed and how large can the value become?
5. Would moving, borrowing, splitting the struct, changing call order, or returning ownership express the design better?

Rules:

- Prefer moves when ownership transfers.
- Prefer borrows when the callee only observes.
- Prefer `&str`/`&[T]` inputs when ownership is unnecessary, but do not force borrowed APIs that make lifetimes infect unrelated layers.
- Do not return references into mutable/global caches unless lifetime and invalidation are genuinely stable.
- Use `Cow` only when both borrowed and owned modes are materially required.
- Use `Arc` only for genuine shared ownership across independently living owners or tasks.
- Use `Rc` only for genuine single-thread shared ownership.
- Call `Arc::clone`/`Rc::clone` explicitly when pointer cloning must be visible.
- Do not wrap values in `Arc` preemptively because code may become async or concurrent later.
- Do not introduce interior mutability to avoid designing ownership.
- Do not hold broad mutable borrows across unrelated work; shrink mutation scope.
- Do not make fields public to bypass borrowing or module design.

### Synchronization

- A mutex protects an invariant, not merely a value. State the invariant.
- Keep critical sections small and obvious.
- Never hold a synchronous or asynchronous lock across `.await` unless the design explicitly requires it and the consequences are understood.
- Prefer message passing when a single owner can serialize state transitions cleanly.
- Prefer a lock when shared in-memory state with short critical sections is simpler than an actor.
- Do not use an actor merely to avoid a mutex, or a mutex merely to avoid defining messages.
- Do not nest locks without a documented ordering rule.
- Do not combine `Arc<Mutex<Option<Arc<RwLock<_>>>>>`-style ownership. Redesign the state and lifecycle.
- Choose atomics only when lock-free semantics are needed and memory ordering is understood. `SeqCst` is not a substitute for understanding, and weaker orderings are not a performance decoration.

## 5. Traits, generics, enums, and dynamic dispatch

Choose dispatch based on the actual extension model.

- Use direct concrete types when there is one implementation and no boundary requiring substitution.
- Use an enum for a closed set of variants controlled by the repository.
- Use generics when static dispatch and compile-time composition are valuable and type proliferation remains manageable.
- Use `dyn Trait` for genuinely open runtime polymorphism, plugin boundaries, or heterogeneous collections.
- Use traits at architectural boundaries where alternate implementations are real: clock, filesystem, network transport, persistence, process runner, model provider.
- Do not introduce a trait solely to mock an internal concrete type. Test behavior through real seams or a small fake at an actual boundary.
- Keep traits small and capability-focused. Avoid "god traits" that mirror an entire subsystem.
- Avoid blanket implementations that make coherence and behavior hard to reason about.
- Avoid generic parameters that exist only to look reusable.
- Avoid associated-type puzzles when a concrete type or enum is clearer.
- Do not box futures or trait objects to escape a difficult type until the ownership and API model is understood.

## 6. Error handling

Errors are part of the contract.

### Required behavior

- Distinguish expected domain failures from programmer invariant violations.
- Preserve causal chains and source errors where useful.
- Add context at boundaries where the operation and relevant identifiers are known.
- Do not log and return the same error at every layer; choose an ownership point for reporting.
- Make retryability, cancellation, timeout, validation, not-found, conflict, and unavailable states distinguishable when callers act differently.
- Use typed errors for libraries and domain/core layers.
- `anyhow` may be appropriate at a binary's outer orchestration boundary, but not as a substitute for domain contracts.
- `thiserror` may reduce boilerplate, but adding it still requires a dependency justification.

### Reject

- `.unwrap()` or `.expect()` in production paths without a statically established invariant and narrow documented exception,
- `.ok()` used to erase failure,
- `let _ = fallible_call()` or ignored task/channel results,
- `map_err(|_| ...)` that discards useful causes,
- `Err(format!(...))` for structured failures,
- catch-all errors that prevent caller decisions,
- converting every failure into HTTP 500 or a generic agent error,
- retry loops without classification, limit, jitter/backoff policy, and cancellation,
- panics for user input, network, filesystem, database, configuration, or ordinary resource failures.

### Invariants and panics

A panic is acceptable only when continuing would indicate an internal programming bug and the invariant is local, stable, and demonstrably established. Prefer constructors and types that make the state impossible. If an invariant cannot be represented, document where it is established and test it.

Do not replace `unwrap()` with `expect("cannot fail")`. The message is not evidence.

## 7. Async and task lifecycle

Async code must have ownership and shutdown semantics.

For every spawned task, identify:

- who owns the task,
- whether the `JoinHandle` is retained,
- how errors are observed,
- how cancellation is requested,
- what happens on parent failure,
- what happens during shutdown,
- whether the task may outlive dependencies it references,
- whether restart is allowed and who performs it.

Rules:

- Do not spawn detached tasks by dropping or ignoring handles without an explicit supervised lifecycle.
- Do not use async functions that contain no meaningful await point.
- Do not perform blocking filesystem, process, DNS, compression, crypto, or CPU-heavy work on an async executor thread without an appropriate boundary.
- Use bounded channels by default. Capacity is part of the resource and backpressure design; name or document why it is sufficient.
- Unbounded channels require a proven upper bound elsewhere and an explicit reason.
- Handle closed channels and lagged/broadcast receivers deliberately.
- Avoid select loops that are not cancellation-safe. Know which futures lose progress when dropped.
- Use timeouts at boundaries, not arbitrary sleeps.
- Use structured concurrency where child work should not outlive parent work.
- Do not hold borrowed guards, locks, or temporary resources across `.await` accidentally.
- Do not clone large request/context objects into every task. Extract the owned data each task needs.
- Do not hide task failure behind logging only.

## 8. State machines and lifecycle

Represent lifecycle explicitly.

Prefer an enum such as:

```rust
#[derive(Debug)]
enum JobState {
    Queued,
    Running { started_at: Instant },
    Cancelling,
    Completed { output: Output },
    Failed { error: JobError },
}
```

over independent booleans such as `started`, `done`, `failed`, and `cancelled` that permit contradictory combinations.

Rules:

- Centralize state transitions.
- Validate transition preconditions.
- Keep one source of truth.
- Do not mirror the same state in memory, database, cache, and channel without a reconciliation/invalidation model.
- Do not add caches without ownership, key validity, eviction, memory bound, and invalidation semantics.
- Do not use `Option` to represent every lifecycle stage.
- Make terminal states and restart behavior explicit.

## 9. Serialization, storage, and protocols

- Define stable wire/storage types separately from evolving domain types when compatibility matters.
- Validate versions and unknown variants deliberately.
- Avoid serializing internal structs merely because `#[derive(Serialize, Deserialize)]` is convenient.
- Avoid `#[serde(default)]` when absence should be an error.
- Avoid flattening arbitrary maps into typed payloads unless extensibility is a real protocol requirement.
- Do not silently ignore unknown fields for security- or correctness-sensitive inputs unless forward compatibility requires it.
- Bound payload sizes, collection lengths, recursion, and decompression expansion at untrusted boundaries.
- Use checked numeric conversions and define overflow behavior.
- Preserve transactional integrity across related writes.
- Do not use JSON blobs as an internal database schema when fields are queried or constrained.
- Migrations must be deterministic, reversible where required, and tested against representative previous data.

## 10. Public API and module boundaries

- Keep items private by default.
- Use `pub(crate)` when only the workspace crate needs access.
- Export the smallest stable contract.
- Do not re-export dependency types accidentally unless they are intentionally part of the public API.
- Do not create broad `prelude` modules by default.
- Do not use wildcard imports outside narrow, conventional contexts.
- Avoid public fields when constructors/accessors preserve invariants.
- Avoid a public generic parameter merely because an implementation detail is generic.
- Document errors, panics, safety, cancellation, blocking behavior, ordering, and side effects for public APIs where relevant.
- Public async APIs should state cancellation behavior when dropping the returned future matters.
- Do not expose internal synchronization primitives in APIs unless callers must coordinate directly.
- For published crates, treat feature names and default features as API.

## 11. Dependencies and features

Before adding a dependency, inspect:

- whether the repository already has a suitable dependency,
- direct and transitive dependency count,
- default features and whether they are necessary,
- MSRV and target support,
- maintenance/security posture,
- license and source,
- compile-time and binary-size cost,
- whether its types leak into public APIs,
- whether a small standard-library implementation is clearer and safer,
- whether reimplementing the domain would be riskier than depending on a mature crate.

Rules:

- Pin git dependencies to immutable revisions when they are unavoidable.
- Do not use wildcard versions.
- Do not disable default features mechanically; understand what they select.
- Keep feature flags additive where practical.
- Avoid mutually exclusive features unless architecture demands them.
- Do not hide platform differences behind features when target cfg is the correct mechanism.
- Do not add a dependency solely to avoid five lines of obvious code.
- Do not write homemade crypto, parsers for complex standards, TLS, URL handling, or synchronization primitives to reduce dependency count.
- Remove unused dependencies only after checking build scripts, proc macros, target cfgs, examples, benches, and feature combinations.
- Treat duplicate crate versions as a diagnostic, not automatic slop.

## 12. Unsafe and FFI

Safe Rust is the default. Unsafe code creates a proof obligation.

For every unsafe block or function:

- state the exact safety invariant,
- identify who establishes it,
- identify how long it remains true,
- keep the unsafe region as small as is logically reviewable,
- expose a safe API that enforces the invariant where possible,
- test edge cases and invalid boundary conditions,
- run Miri where supported,
- consider sanitizers/platform tests for FFI and native integration,
- document ownership, aliasing, alignment, lifetime, initialization, layout, thread-safety, and unwind assumptions as applicable.

Reject:

- unsafe used for performance without measurement,
- `transmute` where explicit conversions exist,
- raw-pointer arithmetic without bounded reasoning,
- manufacturing lifetimes,
- `mem::forget` as casual lifecycle management,
- `MaybeUninit` without initialization proof,
- FFI structs without explicit representation/layout review,
- C strings and buffers without length/termination ownership rules,
- callbacks whose lifetime or thread model is implicit,
- unwinding across an FFI boundary,
- `unsafe impl Send/Sync` without a written invariant.

A `// SAFETY:` comment must explain why the unsafe contract is satisfied at that site. Restating the operation is insufficient.

## 13. Testing

Tests should prove behavior and failure modes, not implementation trivia.

Required principles:

- Every bug fix receives a regression test that fails before the fix when practical.
- Test public/meaningful behavior at the narrowest stable boundary.
- Unit-test pure logic; integration-test contracts between components; end-to-end-test only critical flows.
- Prefer real lightweight implementations or fakes at actual boundaries over deep mocking.
- Do not mock the function under test or duplicate its implementation in assertions.
- Do not assert only that code "does not panic."
- Test error paths, cancellation, timeouts, empty/maximal inputs, malformed data, restart/recovery, and resource cleanup where relevant.
- Avoid sleeps and real wall-clock timing. Inject clocks or use runtime time control.
- Avoid shared mutable global fixtures and order-dependent tests.
- Use temporary directories/files safely and cleanly.
- Do not update snapshots blindly. Review semantic changes.
- Property-test invariants with large input spaces.
- Fuzz parsers, codecs, protocol state, and untrusted boundary conversion.
- Concurrency tests must force/interleave meaningful states rather than rely on chance.
- Coverage is a map of untested areas, not a target that justifies low-value tests.

Tests may use `expect` with a specific setup-invariant message when the policy explicitly permits it in test code. Avoid raw `unwrap` because it gives poor failure context.

## 14. Performance and allocation

- Measure before optimizing non-obvious code.
- Fix algorithmic complexity before micro-optimizing syntax.
- Avoid repeated allocation, cloning, parsing, serialization, or lock acquisition in known hot paths.
- Do not contort ordinary code to avoid tiny allocations without evidence.
- Keep zero-copy designs only where ownership/lifetime complexity is justified by measurements.
- Do not use unsafe, custom allocators, object pools, or lock-free structures without profiling and operational need.
- Benchmark representative workloads and guard against optimizer-elided benchmarks.
- Consider compile time, monomorphization, binary size, and memory footprint—not only runtime latency.
- Large generic APIs and deeply nested combinators can shift cost into compilation and diagnostics.

## 15. Logging, security, and operational behavior

- Use structured logging/tracing at ownership boundaries.
- Do not log secrets, tokens, credentials, full sensitive payloads, or unredacted personal data.
- Include stable identifiers and operation context, not giant debug dumps.
- Avoid duplicate error logs at every layer.
- Ensure shutdown flushes or deliberately drops buffered work.
- Bound queues, retries, input sizes, and concurrency.
- Validate paths, command arguments, URLs, redirects, archive extraction, and temporary-file behavior at untrusted boundaries.
- Avoid shell command construction from strings; use argument APIs.
- Do not trust environment variables or configuration files without parsing and validation.
- Do not expose debug errors directly to untrusted clients.
- Use constant-time/security-reviewed primitives where cryptographic comparisons matter.

## 16. Comments, documentation, and naming

Comments should explain:

- why the design is this way,
- an invariant the type system cannot express,
- a safety proof,
- cancellation or ordering behavior,
- a non-obvious external constraint,
- a deliberate tradeoff,
- why a lint exception is correct.

Comments should not:

- narrate obvious syntax,
- repeat function/type names,
- preserve abandoned code,
- claim correctness without evidence,
- become essays compensating for a confusing design.

Names should use domain language and expose responsibility. Reject vague buckets such as `Utils`, `Common`, `Misc`, `Thing`, `Data`, `Manager`, or `Helper` unless the domain genuinely uses that term and the responsibility is narrow.

## 17. Common agent-generated slop patterns

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
- making fields/public functions visible for tests,
- converting compiler errors into runtime errors through boxing/dynamic typing,
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
