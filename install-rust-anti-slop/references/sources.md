# Primary references

Use current versions of these sources when maintaining this skill. Tool behavior and lint availability follow the repository's pinned toolchain, not this file.

- Agent Skills specification: https://agentskills.io/specification
- Cargo workspaces and workspace lint inheritance: https://doc.rust-lang.org/cargo/reference/workspaces.html
- Cargo lint configuration: https://doc.rust-lang.org/cargo/reference/lints.html
- Cargo check command and target/feature selection: https://doc.rust-lang.org/cargo/commands/cargo-check.html
- Cargo tree and duplicate dependencies: https://doc.rust-lang.org/cargo/commands/cargo-tree.html
- Cargo feature model: https://doc.rust-lang.org/cargo/reference/features.html
- Cargo continuous integration guidance: https://doc.rust-lang.org/cargo/guide/continuous-integration.html
- Clippy overview and lint groups: https://doc.rust-lang.org/clippy/
- Clippy lint categories and guidance: https://doc.rust-lang.org/clippy/lints.html
- Clippy usage and configuration: https://doc.rust-lang.org/clippy/usage.html
- Clippy configuration keys: https://doc.rust-lang.org/clippy/lint_configuration.html
- Stable Clippy lint index: https://rust-lang.github.io/rust-clippy/stable/index.html
- rustc lint listing: https://doc.rust-lang.org/rustc/lints/index.html
- `unsafe_op_in_unsafe_fn`: https://doc.rust-lang.org/rustc/lints/listing/allowed-by-default.html#unsafe-op-in-unsafe-fn
- cargo-deny documentation: https://embarkstudios.github.io/cargo-deny/
- Miri: https://github.com/rust-lang/miri
- Dylint: https://github.com/trailofbits/dylint
- cargo-nextest: https://nexte.st/
- cargo-llvm-cov: https://github.com/taiki-e/cargo-llvm-cov

## Maintenance rules

- Verify every configured lint with the pinned `cargo clippy -- -W help` before adding it.
- Prefer `cargo deny init` from the installed version before merging policy.
- Do not upgrade examples merely because latest documentation differs; preserve the repository's toolchain/MSRV.
- Re-review individual nursery/restriction lints when the pinned toolchain changes.
