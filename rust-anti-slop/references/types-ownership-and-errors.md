# Types, ownership, dispatch, and errors

Read this reference when a task changes or reviews types, ownership, borrowing, traits, generics, dispatch, or error contracts.

## Types are evidence

Use the type system to preserve facts already known by the program.

Prefer:

- newtypes for identifiers, units, validated strings, and values with domain invariants,
- enums for closed state machines and finite variants,
- structs with named fields over position-heavy tuples,
- non-empty or container types when emptiness is invalid,
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
- `Box<dyn Error>` or `anyhow::Error` crossing domain or library API boundaries,
- generic `Context`, `Data`, `Info`, `Payload`, `Manager`, `Helper`, `Util`, `Service`, or `Handler` names that conceal responsibility,
- type aliases used only to hide an unreadable type rather than improve the model,
- wildcard enum matches that silently absorb future variants.

Untyped or weakly typed data may exist at external boundaries such as JSON, environment variables, CLI arguments, database rows, network frames, plugin messages, or FFI. Parse and validate once at the boundary. After successful parsing, pass typed domain values inward. Do not repeatedly inspect strings and JSON throughout the core.

## Ownership and borrowing

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
- Prefer `&str` and `&[T]` inputs when ownership is unnecessary, but do not force borrowed APIs that make lifetimes infect unrelated layers.
- Do not return references into mutable or global caches unless lifetime and invalidation are genuinely stable.
- Use `Cow` only when both borrowed and owned modes are materially required.
- Use `Arc` only for genuine shared ownership across independently living owners or tasks.
- Use `Rc` only for genuine single-thread shared ownership.
- Call `Arc::clone` or `Rc::clone` explicitly when pointer cloning must be visible.
- Do not wrap values in `Arc` preemptively because code may become async or concurrent later.
- Do not introduce interior mutability to avoid designing ownership.
- Do not hold broad mutable borrows across unrelated work; shrink mutation scope.
- Do not make fields public to bypass borrowing or module design.

Synchronization-specific ownership rules live in `async-state-and-boundaries.md` and apply when locks, atomics, channels, or concurrent actors are involved.

## Traits, generics, enums, and dynamic dispatch

Choose dispatch based on the actual extension model.

- Use direct concrete types when there is one implementation and no boundary requiring substitution.
- Use an enum for a closed set of variants controlled by the repository.
- Use generics when static dispatch and compile-time composition are valuable and type proliferation remains manageable.
- Use `dyn Trait` for genuinely open runtime polymorphism, plugin boundaries, or heterogeneous collections.
- Use traits at architectural boundaries where alternate implementations are real, such as clocks, filesystems, network transports, persistence, process runners, or model providers.
- Do not introduce a trait solely to mock an internal concrete type. Test behavior through real seams or a small fake at an actual boundary.
- Keep traits small and capability-focused. Avoid god traits that mirror an entire subsystem.
- Avoid blanket implementations that make coherence and behavior hard to reason about.
- Avoid generic parameters that exist only to look reusable.
- Avoid associated-type puzzles when a concrete type or enum is clearer.
- Do not box futures or trait objects to escape a difficult type until the ownership and API model is understood.

## Error handling

Errors are part of the contract.

- Distinguish expected domain failures from programmer invariant violations.
- Preserve causal chains and source errors where useful.
- Add context at boundaries where the operation and relevant identifiers are known.
- Do not log and return the same error at every layer; choose an ownership point for reporting.
- Make retryability, cancellation, timeout, validation, not-found, conflict, and unavailable states distinguishable when callers act differently.
- Use typed errors for libraries and domain or core layers.
- `anyhow` may be appropriate at a binary's outer orchestration boundary, but not as a substitute for domain contracts.
- `thiserror` may reduce boilerplate, but adding it still requires a dependency justification.

Reject:

- `.unwrap()` or `.expect()` in production paths without a statically established invariant and narrow documented exception,
- `.ok()` used to erase failure,
- `let _ = fallible_call()` or ignored task and channel results,
- `map_err(|_| ...)` that discards useful causes,
- `Err(format!(...))` for structured failures,
- catch-all errors that prevent caller decisions,
- converting every failure into HTTP 500 or a generic agent error,
- retry loops without classification, limit, jitter or backoff policy, and cancellation,
- panics for user input, network, filesystem, database, configuration, or ordinary resource failures.

A panic is acceptable only when continuing would indicate an internal programming bug and the invariant is local, stable, and demonstrably established. Prefer constructors and types that make the state impossible. If an invariant cannot be represented, document where it is established and test it. Replacing `unwrap()` with `expect("cannot fail")` does not provide evidence.
