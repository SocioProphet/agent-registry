# Release Dry-Run

This document describes the release dry-run process and how it differs from a stable release.

## Purpose

The release dry-run produces deterministic local metadata artifacts without publishing anything to a release channel, package registry, or Homebrew. It is safe to run on any branch at any time.

## Development formulae vs stable release artifacts

| Property | Development formula | Stable release artifact |
|---|---|---|
| Version | `0.0.0-dry-run` | Tagged semver (e.g. `v1.0.0`) |
| Location | `dist/` (local only) | GitHub Releases + Homebrew tap |
| Homebrew URL | None — not invented | Pinned release archive URL |
| Checksum purpose | Local integrity verification | Homebrew `sha256` field |
| Published? | No | Yes, after tag + review |
| Safe to run in CI? | Yes, always | Only on protected release workflow |

Development formulae are reference-only snapshots of the current example records. They are suitable for local inspection, integration testing, and CI validation. They are **not** suitable for use as Homebrew `url` or `sha256` values.

Stable release artifacts are produced only when a version tag is pushed through the official release process. They carry a permanent URL and a checksum that Homebrew consumers may pin.

## Running the dry-run

```bash
make release-dry-run
```

This writes two files under `dist/`:

- `agent-registry-0.0.0-dry-run.json` — deterministic JSON manifest of all agent registry records
- `agent-registry-0.0.0-dry-run.json.sha256` — SHA-256 checksum of the manifest

The manifest is serialized with sorted keys and consistent indentation so the SHA-256 digest is reproducible across runs given the same input files.

## What the dry-run does NOT do

- Does not publish any artifact to GitHub Releases.
- Does not push to any Homebrew tap.
- Does not use any credentials, tokens, or secrets.
- Does not invent Homebrew formula URLs or checksums for production use.
- Does not grant any live runtime authority.
