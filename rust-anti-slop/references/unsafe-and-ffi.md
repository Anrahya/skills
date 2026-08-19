# Unsafe Rust and FFI

Read this reference when a task involves unsafe blocks or functions, raw pointers, atomics, custom allocators, memory mapping, ABI or layout, native libraries, callbacks, or other FFI boundaries.

Safe Rust is the default. Unsafe code creates a proof obligation.

For every unsafe block or function:

- state the exact safety invariant,
- identify who establishes it,
- identify how long it remains true,
- keep the unsafe region as small as is logically reviewable,
- expose a safe API that enforces the invariant where possible,
- test edge cases and invalid boundary conditions,
- run Miri where supported,
- consider sanitizers or platform tests for FFI and native integration,
- document ownership, aliasing, alignment, lifetime, initialization, layout, thread-safety, and unwind assumptions as applicable.

Reject:

- unsafe used for performance without measurement,
- `transmute` where explicit conversions exist,
- raw-pointer arithmetic without bounded reasoning,
- manufacturing lifetimes,
- `mem::forget` as casual lifecycle management,
- `MaybeUninit` without initialization proof,
- FFI structs without explicit representation and layout review,
- C strings and buffers without length, termination, and ownership rules,
- callbacks whose lifetime or thread model is implicit,
- unwinding across an FFI boundary,
- `unsafe impl Send/Sync` without a written invariant.

A `// SAFETY:` comment must explain why the unsafe contract is satisfied at that site. Restating the operation is insufficient.
