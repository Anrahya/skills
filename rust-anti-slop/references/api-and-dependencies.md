# Public APIs, crate boundaries, dependencies, and features

Read this reference when a task changes or reviews public APIs, visibility, crate or module boundaries, dependencies, Cargo features, MSRV, or target support.

## Public API and module boundaries

- Keep items private by default.
- Use `pub(crate)` when only the current crate needs access.
- Export the smallest stable contract.
- Do not re-export dependency types accidentally unless they are intentionally part of the public API.
- Do not create broad `prelude` modules by default.
- Do not use wildcard imports outside narrow, conventional contexts.
- Avoid public fields when constructors or accessors preserve invariants.
- Avoid a public generic parameter merely because an implementation detail is generic.
- Document errors, panics, safety, cancellation, blocking behavior, ordering, and side effects for public APIs where relevant.
- Public async APIs should state cancellation behavior when dropping the returned future matters.
- Do not expose internal synchronization primitives in APIs unless callers must coordinate directly.
- For published crates, treat feature names and default features as API.

## Dependencies and features

Before adding a dependency, inspect:

- whether the repository already has a suitable dependency,
- direct and transitive dependency count,
- default features and whether they are necessary,
- MSRV and target support,
- maintenance and security posture,
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
