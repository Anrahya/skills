# Async, state, boundaries, and operations

Read this reference when a task involves concurrent actors, locks, atomics, tasks, channels, cancellation, lifecycle state, serialization or storage, hot paths, security boundaries, logging, or other operational behavior.

## Synchronization

- A mutex protects an invariant, not merely a value. State the invariant.
- Keep critical sections small and obvious.
- Never hold a synchronous or asynchronous lock across `.await` unless the design explicitly requires it and the consequences are understood.
- Prefer message passing when a single owner can serialize state transitions cleanly.
- Prefer a lock when shared in-memory state with short critical sections is simpler than an actor.
- Do not use an actor merely to avoid a mutex, or a mutex merely to avoid defining messages.
- Do not nest locks without a documented ordering rule.
- Do not combine `Arc<Mutex<Option<Arc<RwLock<_>>>>>`-style ownership. Redesign the state and lifecycle.
- Choose atomics only when lock-free semantics are needed and memory ordering is understood. `SeqCst` is not a substitute for understanding, and weaker orderings are not a performance decoration.

## Async and task lifecycle

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
- Handle closed channels and lagged or broadcast receivers deliberately.
- Avoid select loops that are not cancellation-safe. Know which futures lose progress when dropped.
- Use timeouts at boundaries, not arbitrary sleeps.
- Use structured concurrency where child work should not outlive parent work.
- Do not hold borrowed guards, locks, or temporary resources across `.await` accidentally.
- Do not clone large request or context objects into every task. Extract the owned data each task needs.
- Do not hide task failure behind logging only.

## State machines and lifecycle

Represent lifecycle explicitly. Prefer enums with data-bearing states over independent booleans that permit contradictory combinations.

- Centralize state transitions.
- Validate transition preconditions.
- Keep one source of truth.
- Do not mirror the same state in memory, database, cache, and channel without a reconciliation or invalidation model.
- Do not add caches without ownership, key validity, eviction, memory bound, and invalidation semantics.
- Do not use `Option` to represent every lifecycle stage.
- Make terminal states and restart behavior explicit.

## Retries, replay, and idempotency

Any externally visible operation that can be retried, replayed, resumed after restart, or repeated after a timeout or ambiguous response must define its duplicate semantics.

- Prefer idempotent convergence: repeating the logical operation reaches the same valid state without duplicating effects.
- When duplicate effects are unacceptable, use a stable idempotency or deduplication identity scoped to the logical operation, not a single transport attempt.
- Persist the deduplication record and outcome atomically with the effect when possible. Otherwise define and test reconciliation for every partial state.
- Make side-effect order, commit points, retryable failures, and ownership of retries explicit. Cancellation or dropping a future does not prove that a remote effect stopped.
- Test the same request twice, a timeout after the effect but before the response, a crash between steps, and restart or replay where those states are possible.
- If an operation is intentionally non-idempotent, enforce and document the at-most-once boundary instead of relying on callers to guess.
- Never claim exactly-once behavior without end-to-end proof across the protocol, storage, recovery, and every retrying participant.

## Serialization, storage, and protocols

- Define stable wire and storage types separately from evolving domain types when compatibility matters.
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

## Performance and allocation

- Measure before optimizing non-obvious code.
- Fix algorithmic complexity before micro-optimizing syntax.
- Avoid repeated allocation, cloning, parsing, serialization, or lock acquisition in known hot paths.
- Do not contort ordinary code to avoid tiny allocations without evidence.
- Keep zero-copy designs only where ownership and lifetime complexity is justified by measurements.
- Do not use unsafe, custom allocators, object pools, or lock-free structures without profiling and operational need.
- Benchmark representative workloads and guard against optimizer-elided benchmarks.
- Consider compile time, monomorphization, binary size, and memory footprint, not only runtime latency.
- Large generic APIs and deeply nested combinators can shift cost into compilation and diagnostics.

## Logging, security, and operational behavior

- Use structured logging or tracing at ownership boundaries.
- Do not log secrets, tokens, credentials, full sensitive payloads, or unredacted personal data.
- Include stable identifiers and operation context, not giant debug dumps.
- Avoid duplicate error logs at every layer.
- Ensure shutdown flushes or deliberately drops buffered work.
- Bound queues, retries, input sizes, and concurrency.
- Validate paths, command arguments, URLs, redirects, archive extraction, and temporary-file behavior at untrusted boundaries.
- Avoid shell command construction from strings; use argument APIs.
- Do not trust environment variables or configuration files without parsing and validation.
- Do not expose debug errors directly to untrusted clients.
- Use constant-time or security-reviewed primitives where cryptographic comparisons matter.
