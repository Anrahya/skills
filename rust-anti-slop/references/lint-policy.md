# Rust lint selection policy

This reference defines a curated lint strategy. It intentionally avoids "enable everything" configurations that create contradictory guidance, false positives, or code rewritten solely for lint aesthetics.

Before adding any lint to `Cargo.toml`, confirm that the repository's active pinned Clippy recognizes it:

```bash
cargo clippy -- -W help
```

Lint availability and behavior follow the toolchain. Preserve the repository's MSRV and toolchain pin.

## 1. Levels and priorities

Recommended intent:

- `deny`: high-signal policy violation that should block CI.
- `warn`: migration signal or context-sensitive review item.
- `allow`: deliberately disabled policy, preferably documented at the central configuration.
- `forbid`: use sparingly when no local exception can ever be legitimate.

When a group and individual lints are both configured through Cargo, give the group a lower priority so specific decisions win:

```toml
[workspace.lints.clippy]
all = { level = "deny", priority = -1 }
unwrap_used = "deny"
```

Do not use `warnings = "deny"` as the only policy. It makes every future warn-by-default compiler/Clippy addition a breaking CI change. If CI uses `-D warnings`, pin the toolchain and upgrade it through reviewed changes.

## 2. Rust compiler baseline

Use these where supported and appropriate:

```toml
[workspace.lints.rust]
unsafe_code = "deny"
unsafe_op_in_unsafe_fn = "deny"
unused_must_use = "deny"
unreachable_pub = "deny"
unexpected_cfgs = "deny"
trivial_casts = "deny"
trivial_numeric_casts = "deny"
unused_qualifications = "warn"
```

Notes:

- Change `unsafe_code` to `forbid` only for crates that must remain entirely safe. `forbid` cannot be overridden locally.
- `unreachable_pub` is excellent for applications/internal crates. Review public libraries and macro-generated/export patterns before denying it.
- Configure legitimate custom cfg names before denying `unexpected_cfgs`.
- Do not enable `unused_results` globally without migration evidence; it can produce severe noise for APIs not marked `must_use`.
- Consider `non_ascii_idents = "deny"` where source identifiers must be ASCII for security/review consistency, but do not impose it on projects intentionally using other scripts.
- Consider edition-compatibility groups during an edition migration, not as permanent unrelated noise.

## 3. Clippy baseline: high-signal default

Set `clippy::all` to `deny`. It includes Clippy's default correctness, suspicious, style, complexity, and performance groups.

Then cherry-pick strict lints that control common low-evidence agent output. A strong baseline candidate set is:

```toml
[workspace.lints.clippy]
all = { level = "deny", priority = -1 }

allow_attributes_without_reason = "deny"
dbg_macro = "deny"
enum_glob_use = "deny"
exit = "deny"
expect_used = "deny"
let_underscore_must_use = "deny"
map_err_ignore = "deny"
mem_forget = "deny"
missing_safety_doc = "deny"
panic = "deny"
print_stderr = "deny"
print_stdout = "deny"
todo = "deny"
unimplemented = "deny"
unreachable = "deny"
unwrap_used = "deny"
wildcard_imports = "deny"
```

Interpretation:

- `expect_used` and `unwrap_used` deny production convenience panics. Tests may receive a narrower policy if the project accepts `expect` with specific setup messages.
- `panic`/`unreachable` are policy lints, not claims that all panics are impossible. Narrow exceptions require a proven invariant.
- `map_err_ignore` catches loss of source error evidence.
- `let_underscore_must_use` catches explicit must-use erasure.
- `allow_attributes_without_reason` makes exceptions reviewable.
- `print_stdout`/`print_stderr` prevent debug remnants in libraries/services; CLI binaries may need narrow exceptions or a logging/output boundary.
- `exit` should usually be confined to the outermost binary boundary if used at all.

## 4. Ownership, allocation, and API-shape profile

Enable after checking the existing codebase and false-positive behavior on the pinned toolchain:

```toml
[workspace.lints.clippy]
boxed_local = "deny"
clone_on_ref_ptr = "deny"
fn_params_excessive_bools = "deny"
large_types_passed_by_value = "deny"
needless_collect = "deny"
rc_buffer = "deny"
rc_mutex = "deny"
redundant_clone = "deny"
result_large_err = "deny"
struct_excessive_bools = "deny"
too_many_arguments = "deny"
too_many_lines = "warn"
type_complexity = "warn"
unnecessary_box_returns = "deny"
unnecessary_wraps = "deny"
vec_box = "deny"
```

Do not "fix" these mechanically:

- A `type_complexity` finding is not solved merely by hiding the type behind an alias. Simplify state/ownership or use a named contract when it adds meaning.
- `too_many_arguments` may indicate a missing cohesive parameter object, but do not create a generic `Options` bag full of unrelated fields.
- `too_many_lines` is a review signal. Do not fragment a coherent algorithm into arbitrary one-use helpers.
- `large_types_passed_by_value` requires ownership/API analysis; borrowing may make lifetime design worse at some boundaries.
- `redundant_clone` is historically in the nursery group; enable the individual lint only after validating it on the pinned toolchain.
- `unnecessary_wraps` can conflict with trait/API uniformity. Use a narrow reason if a fallible signature is contractually necessary.

## 5. Error and control-flow profile

Useful candidates:

```toml
[workspace.lints.clippy]
fallible_impl_from = "deny"
if_then_some_else_none = "deny"
manual_assert = "deny"
manual_let_else = "warn"
match_wild_err_arm = "deny"
match_wildcard_for_single_variants = "deny"
question_mark = "deny"
try_err = "deny"
wildcard_enum_match_arm = "deny"
```

Guidance:

- Prefer `TryFrom` for fallible conversion.
- Exhaustive enum matching is valuable when new variants must trigger review. Keep a wildcard when forward compatibility genuinely requires it and document that policy.
- Do not turn every branch into combinator-heavy code merely because a lint suggests it. Readability and debugger behavior matter.
- `manual_assert` is appropriate where a condition is truly an invariant. Do not convert recoverable user/input failures into assertions.

## 6. Async and concurrency profile

For async/service crates, consider:

```toml
[workspace.lints.clippy]
async_yields_async = "deny"
await_holding_lock = "deny"
await_holding_refcell_ref = "deny"
let_underscore_future = "deny"
large_futures = "warn"
```

Context-sensitive candidates:

```toml
[workspace.lints.clippy]
future_not_send = "warn"
```

Use Clippy configuration for repository-specific invalid guards:

```toml
await-holding-invalid-types = [
  # "project_crate::NonAwaitSafeGuard",
]
```

Notes:

- `future_not_send` is useful when tasks must run on a multi-threaded executor. It is wrong as a universal rule for intentionally local/single-thread futures.
- A large future may need boxing or scope reduction, but do not box every future blindly. Inspect captured state and hot-path impact.
- `await_holding_lock` does not replace lifecycle and lock-order review.
- Add project-specific bans for unbounded channels only when bounded backpressure is an explicit invariant.

## 7. Numeric and indexing profile

For parsers, protocols, storage, finance, counters, sizes, offsets, and untrusted numeric input, consider:

```toml
[workspace.lints.clippy]
as_conversions = "deny"
cast_possible_truncation = "deny"
cast_possible_wrap = "deny"
cast_precision_loss = "warn"
cast_sign_loss = "deny"
checked_conversions = "deny"
float_cmp = "deny"
indexing_slicing = "deny"
string_slice = "deny"
```

Do not apply this profile blindly to graphics/DSP/numerical code where casts and float comparisons have designed semantics. In those crates, use domain-specific conversion helpers and narrow documented exceptions.

Resolution rules:

- Prefer `TryFrom`/`try_into` at untrusted boundaries.
- Use checked/saturating/wrapping arithmetic only when its semantics are explicitly correct.
- Do not replace indexing with `.get(...).unwrap()`; return/propagate an error or prove the invariant.
- Direct indexing can be acceptable with a local proven invariant; document the proof narrowly.
- Approximate floating-point comparison needs explicit tolerance semantics, not a generic epsilon copied from the internet.

## 8. Public-library profile

For published/public libraries, consider:

```toml
[workspace.lints.clippy]
doc_markdown = "deny"
missing_errors_doc = "deny"
missing_panics_doc = "deny"
missing_safety_doc = "deny"
redundant_pub_crate = "deny"
```

Also consider the compiler's `missing_docs` policy at the crate level if the project is prepared to document the entire public surface. Do not enable it during an unrelated change and then generate low-value documentation to silence it.

Documentation must describe real contracts: errors, panics, safety, cancellation, blocking, side effects, ordering, and feature behavior. "Returns the result" is slop.

## 9. Unsafe profile

For crates containing legitimate unsafe code:

```toml
[workspace.lints.rust]
unsafe_code = "deny"
unsafe_op_in_unsafe_fn = "deny"

[workspace.lints.clippy]
missing_safety_doc = "deny"
undocumented_unsafe_blocks = "deny"
unsafe_derive_deserialize = "deny"
```

Optional after evaluation:

```toml
[workspace.lints.clippy]
multiple_unsafe_ops_per_block = "warn"
```

`multiple_unsafe_ops_per_block` can be useful for reducing proof surface but has known context/false-positive tradeoffs. Do not deny it automatically in FFI-heavy code without evaluating the resulting structure.

Do not use a lint as the only unsafe review. Apply Miri where supported and manually inspect every unsafe invariant.

## 10. Dependency/Cargo profile

Do not enable all `clippy::cargo` by default. Select:

```toml
[workspace.lints.clippy]
negative_feature_names = "deny"
redundant_feature_names = "deny"
wildcard_dependencies = "deny"
```

For published crates, consider `cargo_common_metadata` after filling real metadata rather than placeholders.

Treat `multiple_crate_versions` as a review signal, not a universal error. Cargo graphs legitimately contain multiple versions. Use `cargo tree --duplicates` and `cargo-deny` with reasoned skip entries.

## 11. Test policy

A practical strict split is:

- production: deny `unwrap_used`, `expect_used`, `panic`, prints, indexing, and ignored must-use values;
- tests: continue denying `unwrap_used`; optionally permit `expect_used` and direct panic with useful messages;
- test setup may use `expect("specific fixture invariant")` when failure means the test harness is malformed, not when it hides product behavior;
- keep ignored futures/results and debug remnants denied in tests.

Clippy configuration candidates:

```toml
allow-expect-in-tests = true
allow-unwrap-in-tests = false
allow-panic-in-tests = true
allow-print-in-tests = false
allow-dbg-in-tests = false
allow-indexing-slicing-in-tests = false
```

Choose consciously. A repository that values concise tests may permit test indexing; a parser/safety repository may keep it denied.

## 12. Project-specific bans

Clippy can disallow concrete methods, types, macros, and fields. Use this only after defining the permitted boundary.

Examples to evaluate, not blindly copy:

```toml
disallowed-methods = [
  { path = "tokio::sync::mpsc::unbounded_channel", reason = "Runtime work queues require explicit bounded backpressure", allow-invalid = true },
]

disallowed-types = [
  { path = "serde_json::Value", reason = "Untyped JSON is confined to adapter/boundary modules", allow-invalid = true },
]
```

A global `serde_json::Value` ban is wrong if the crate is itself a JSON adapter. In that case, scope the lint exception to the adapter crate/module and keep domain crates typed.

Potential recurring project-specific policies that may require Dylint rather than Clippy config:

- `anyhow::Result` forbidden outside binary/adapters,
- ignored `JoinHandle` from `tokio::spawn`,
- unbounded channels forbidden outside a named compatibility boundary,
- direct environment/filesystem/network/process access forbidden inside domain crates,
- wall-clock access forbidden outside a clock adapter,
- `HashMap<String, serde_json::Value>` forbidden in internal contracts,
- unsafe blocks permitted only inside a dedicated crate/module,
- direct database client use forbidden outside repository adapters,
- `sleep` forbidden in tests,
- public fields forbidden for invariant-bearing domain types.

Implement a custom lint only after the violation recurs and the rule can be detected with low false-positive risk.

## 13. Lints deliberately not blanket-enabled

Do not enable these groups wholesale:

- `clippy::restriction`: individual lints can conflict and intentionally restrict normal language features.
- `clippy::nursery`: contains lints that may be incomplete or need more work.
- `clippy::pedantic`: useful for power users, but intentional false positives can drive excessive local allows.
- `clippy::cargo`: many findings depend on whether a crate is published and on acceptable dependency graph realities.

Do not blanket-enable highly context-sensitive individual lints such as:

- `arithmetic_side_effects`,
- `integer_division`,
- `float_arithmetic`,
- `absolute_paths`,
- all shadowing lints,
- `single_call_fn`,
- `missing_docs_in_private_items`,
- `min_ident_chars`,
- `pub_use`,
- source-item ordering lints.

These can be valid in specialized projects but often generate ceremony rather than correctness.

## 14. Suppression policy

Preferred order:

1. Fix the real defect.
2. Reshape the local design if that improves clarity and correctness.
3. Decide the lint does not fit the crate/module and configure that policy centrally.
4. Use a narrow `#[expect(lint, reason = "...")]` when the finding is expected and should become visible if it stops triggering.
5. Use a narrow `#[allow(lint, reason = "...")]` only when `expect` is unsuitable.

A valid reason names the invariant or external constraint. Invalid reasons include:

- "Clippy is wrong",
- "needed to compile",
- "false positive" without explanation,
- "temporary",
- "legacy code",
- "performance" without measurement,
- "safe" without a proof.

Review suppressions periodically. No blanket `#![allow(clippy::all)]`, `#![allow(warnings)]`, or generated list of dozens of allows in owned code.
