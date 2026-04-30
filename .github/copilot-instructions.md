Use the GitHub issue body as the source of truth.

Before editing:
1. Read the issue.
2. Inspect the repository.
3. Identify existing validation commands.
4. Keep the PR bounded.

When implementing:
- Prefer existing repository patterns.
- Add examples and validators with schema/contract changes.
- Keep registry contracts separate from execution-plane behavior.
- Do not broaden authority semantics beyond the issue.
- Do not modify unrelated workflow or policy files.

When opening the PR:
- Link the issue.
- Include validation evidence.
- List known gaps.
- State non-goals preserved.
- Do not mark ready if validation did not run.
