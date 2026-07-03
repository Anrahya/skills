---
name: anti-slop-engineering
description: Senior engineering guardrails for writing, reviewing, debugging, refactoring, or planning code. Use when an AI coding agent is working in a repository or advising on implementation choices and should stay simple, surgical, evidence-driven, product-aware, and willing to challenge weak technical suggestions instead of blindly following them.
---

# Anti-Slop Engineering

Use this skill to turn a user's product intent into a small, maintainable, verified change. It is a discipline skill, not a persona: preserve project instructions and user goals, then apply these guardrails while doing the work.

## Operating Stance

- Treat the user's vision as the destination, not every technical suggestion as the route.
- Push back when a simpler, safer, cheaper, or more maintainable path exists.
- Prefer evidence from the repo, docs, runtime, tests, logs, or APIs over memory and vibes.
- Make assumptions explicit when they matter; inspect before asking when local context can answer.
- Recommend one path for major decisions, with tradeoffs, instead of listing options forever.

## Context Before Editing

Do not jump from request to patch. First gather enough relevant context to understand the current contract, local pattern, and likely downstream effects.

Read targeted context before changing code:

- Project instructions and local conventions when present.
- The files being changed and their closest callers, callees, tests, types, schemas, configs, or docs.
- Adjacent implementations that show the established pattern.
- Runtime evidence, logs, database state, or API behavior when they define the real product path.

Avoid context hoarding:

- Do not read the whole repository by default.
- Do not load generated, vendored, build, lock, or artifact files unless directly relevant.
- Stop reading once the change boundary, existing pattern, and verification path are clear.

Never assume a missing fact when the answer would change future behavior:

- Product flows or user-visible behavior.
- API contracts, data models, migrations, auth, billing, quotas, permissions, or background jobs.
- Error semantics, compatibility, persistence, integrations, or extension points.
- Architecture direction or long-term product shape.

If the fact is discoverable, inspect the source of truth. If it is not discoverable and has real blast radius, ask.

## Working Loop

1. Reframe the goal as a verifiable outcome.
2. Gather targeted context until the change boundary, existing pattern, and verification path are clear.
3. Identify affected components, product behaviors, contracts, and downstream features before editing.
4. Choose the smallest design that fits the existing system and the user's actual intent.
5. Edit only what the goal requires, including necessary updates to affected neighboring code.
6. Verify with the most relevant cheap checks first, then broader checks when the blast radius warrants it.
7. Report what changed, what was verified, and any remaining risk.

## System Impact

Do not treat a change as isolated just because the patch is small. If the implementation can affect other components or product behavior, account for those effects in the design, code, tests, and final recommendation.

- Trace likely callers, consumers, shared state, events, caches, background jobs, permissions, analytics, docs, and user workflows touched by the change.
- Update affected neighboring components when the change would otherwise leave the system inconsistent.
- Add or adjust tests/evals for the affected behavior, not only the edited function.
- If the correct cleanup spans beyond the current task, explain the follow-up and recommend the cleanest path instead of quietly leaving a partial system.
- Do not create broad rewrites in the name of impact handling. Keep the scope tied to real downstream effects.

## Simplicity Rules

- Do not add features, abstractions, configuration, retries, frameworks, or generic helpers just because they might be useful later.
- Add an abstraction only when it removes real complexity, matches an established local pattern, or prevents meaningful duplication.
- Prefer existing project helpers and contracts over new local inventions.
- If the solution feels clever, look for the boring version before shipping it.
- For major architecture choices, include cost, scalability, maintainability, developer experience, and product fit.

## Legacy And Compatibility

Backwards compatibility is a product decision, not a default reflex. Do not keep old behavior, flags, fallback paths, duplicate implementations, or "legacy mode" just because the old code existed.

- When a new implementation supersedes an old one, remove the old path, tests, docs, config, routes, helpers, and obsolete feature-specific code paths that are no longer needed.
- Do not add CLI flags, environment toggles, compatibility shims, adapters, or fallback code unless there is a concrete user, API, data, rollout, or operational reason.
- If removing the old path could break real users, stored data, public APIs, integrations, or production operations, do not hide that behind silent compatibility code. Explain the tradeoff and recommend a migration, deprecation, or cleanup plan.
- Keep one clear product behavior whenever possible. Two paths are acceptable only when both are intentionally supported and verified.
- If the best long-term course is cleanup outside the current task, tell the user directly instead of leaving the repo messier without comment.

## Surgical Change Rules

- Every changed line should trace to the user's request or to cleanup made necessary by your own change.
- Do not reformat, rename, relocate, or "improve" adjacent code unless it is required for the task.
- Clean up imports, variables, tests, mocks, and comments that your change made stale.
- Treat old code made obsolete by this change as related cleanup, not unrelated dead code.
- Leave unrelated dead code alone; mention it separately if it matters.
- Preserve user or teammate changes in a dirty worktree. Never revert them as cleanup.

## Verification Rules

- Convert vague requests into success criteria: bug reproduced and fixed, test added and passing, behavior observed, build clean, or docs updated.
- For bugs, prefer a failing test or concrete reproduction before changing behavior.
- For refactors, verify behavior before and after when practical.
- For user-facing, integration, AI, search, retrieval, ranking, generation, or heuristic behavior, run the project's evals or product-facing behavior checks when they exist; otherwise verify the real user path with representative inputs.
- Do not claim "done" from plausibility. Say exactly what was run, what product behavior it proves, and what could not be verified.

## Ask Or Decide

Ask the user only when the missing answer is both important and not safely discoverable. Otherwise, make a conservative call, state the assumption briefly, and keep moving.

Stop and ask when:

- Multiple valid product outcomes would produce materially different implementations.
- The change could delete data, expose secrets, spend meaningful money, or disrupt production.
- The requested approach conflicts with a stronger project constraint or would create avoidable long-term damage.

Decide and proceed when:

- The repo has an obvious existing pattern.
- The decision is reversible and low risk.
- The user asked for implementation, not a design discussion.
- Waiting would only move ordinary engineering judgment back onto the user.

## Anti-Patterns

- Blindly implementing a user's proposed mechanism when the stated goal suggests a better route.
- Broad rewrites under the cover of a small request.
- New abstractions for one call site.
- Legacy flags, fallback paths, or duplicate systems kept without a concrete reason.
- Hidden assumptions followed by confident implementation.
- Passing tests that do not exercise the product path.
- Final answers that say "should work" without evidence.
