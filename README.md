# Skills

Personal AI-agent skills I make or find useful.

## Skills

- `anti-slop-engineering`: keep AI-agent implementation work simple, context-aware, product-aware, clean, and verification-driven.
- `rust-anti-slop`: write, review, debug, harden, and govern Rust code without lint-driven or borrow-checker-driven slop.
- `oss-contribution-workflow`: choose, implement, validate, and publish small open-source PRs without creating maintainer burden.

## Install

```bash
npx skills add Anrahya/skills --skill anti-slop-engineering -g -y
npx skills add Anrahya/skills --skill rust-anti-slop -g -y
npx skills add Anrahya/skills --skill oss-contribution-workflow -g -y
```

Restart your agent runtime after installing so the skill is available in new sessions.

## Attribution

`anti-slop-engineering` is inspired by the MIT-licensed `karpathy-guidelines` skill in [`multica-ai/andrej-karpathy-skills`](https://github.com/multica-ai/andrej-karpathy-skills) and adapted into a broader engineering-discipline skill.

`oss-contribution-workflow` is adapted from GitHub's MIT-licensed `make-repo-contribution` skill in [`github/awesome-copilot`](https://github.com/github/awesome-copilot), inspected at upstream commit `28c3a14a`.

## License

MIT.
