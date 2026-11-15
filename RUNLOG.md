# RUNLOG — agent factory execution log

Every production run of the domainame agent factory: the request (issue), the
execution (branch, PR, tests), the independent review rounds, and the merge.

This repo doubles as a two-agent pipeline demo: an independent reviewer agent
(Fable, a separate model run via a local CLI) authors the requirement and
reviews the result; an executor agent implements; the human owner delegated
the merge gate to the review verdict for these runs.

| Run | Issue | Branch | PR | Tests | Review | Outcome |
|-----|-------|--------|-----|-------|--------|---------|
| 1 | [#1](https://github.com/tempometer/domainame/issues/1) validate_fqdn + env/zone guard | `issue-1-validate-fqdn` | [#2](https://github.com/tempometer/domainame/pull/2) | 58/58 (local) | R1 GO-with-changes (2 RC) → fixes → R2 **GO** | squash-merged `d1c5c32` |
| 2 | [#5](https://github.com/tempometer/domainame/issues/5) English README (owner requirement) | `issue-5-english-readme` | [#8](https://github.com/tempometer/domainame/pull/8) | 58/58 (docs-only) | R1 GO-with-changes (1 RC) → fixes → R2 **GO** | squash-merged `fe5f0db` |
| 3 | [#3](https://github.com/tempometer/domainame/issues/3) fullmatch in validate_domain_label | `issue-3-label-fullmatch` | [#10](https://github.com/tempometer/domainame/pull/10) | 62/62 (local) | **GO**, 0 RC; 3 test OPC applied pre-merge | squash-merged `bfef325` |

## Run 1 — 2026-11-15, issue #1 (validate_fqdn + env/zone guard)

- **Request**: issue #1 — requirement authored by the independent reviewer
  agent (Fable) after reading the repo; filed by the factory intake
  (tempometer). Syntax-only `validate_fqdn()`, env/zone guard in
  `generate_fqdn`, CLI `--validate-fqdn` + exit 2 on invalid `--zone`/`--env`.
- **Executed by**: executor agent (ZCode session), branch
  `issue-1-validate-fqdn`, commit `fffb52a`.
- **Implementation**: policy-free RFC 1123 validator (single trailing dot
  allowed and excluded from the 253-byte total; per-label errors quote the
  offending label) → fail-fast env/zone guard before label generation →
  CLI flag + `parser.error` paths → tests 29 → 48 → README/docstring lines.
- **Review round 1 (Fable — GO-with-changes)**:
  - RC-1: regex `$` matches before a trailing `\n`, so
    `validate_fqdn("example.com\n") == []`. Real defect, confirmed
    independently before fixing → `LABEL_RE.fullmatch` in the new validator.
  - RC-2: `env="dev."` passed validation (trailing dot legal for a full
    name) but joined into an empty label (`dev..keen-falcon…`). → explicit
    trailing-dot rejection for `env` in the library and the CLI.
  - Fix commit `7338ba7` also applied 10 non-blocking suggestions (exact
    stderr expectations, `assertRaisesRegex` part naming, `.`/`a..`/`..`/
    254+`.` cases, empty-string CLI case, `--env`-without-`--zone` pin,
    golden `--seed 7` line, dot-aware 253-byte total, CLI
    `try/except ValueError → parser.error`, fail-fast order).
- **Review round 2 (Fable — GO)**: fix diff verified against the tree;
  RC-1/RC-2 closed; no new defects. Remaining nit (two CLI-test needles
  match the argparse usage line) folded into
  [#4](https://github.com/tempometer/domainame/issues/4).
- **Follow-ups filed**: [#3](https://github.com/tempometer/domainame/issues/3)
  (inherited `$`-anchor defect in `validate_domain_label`),
  [#4](https://github.com/tempometer/domainame/issues/4) (CLI polish batch).
- **Verification before merge**: `python -m unittest discover -s tests -t .`
  — 58/58; live CLI runs of both review RCs (`INVALID` on `\n`, exit 2 on
  `--env dev.`); re-run of the suite on `main` after merge.
- **Merge**: squash-merged after the round-2 GO — merge gate delegated by
  the owner for this run ("merge if the review is OK").

## Run 2 — 2026-11-15, issue #5 (English README — owner requirement)

- **Request**: owner directive — the professional language of the repo is
  English; Ukrainian README preserved as `README.ua.md`.
- **Review round 1 (GO-with-changes)**: RC-1 — the EN href said
  `haikunater` (typo; the UA original had the correct `haikunator`).
  12 non-blocking fixes applied (de-calc English, terminology consistency,
  strict parity restored, `←` arrow). Reviewer confirmed full parity:
  10/10 sections, identical examples/numbers/identifiers, UA file
  byte-identical apart from the cross-link.
- **Review round 2 (GO)** + 2 discretionary polish notes applied pre-merge.
- Inherited UA typos split into
  [#9](https://github.com/tempometer/domainame/issues/9) (the run's
  criterion demanded "UA unchanged").
- **Merge**: `fe5f0db` (squash), issue #5 auto-closed.

## Run 3 — 2026-11-15, issue #3 (inherited `$`-anchor defect)

- **Request**: `validate_domain_label` still used `.match` against a `^…$`
  pattern, so a trailing `\n` passed as valid (the sibling of run 1's RC-1).
- **Fix**: `LABEL_RE.fullmatch`; confirmed the last bare-`.match` validation
  site in the repo.
- **Review (GO, 0 required changes)**: all three callers covered; generated
  labels can never contain `\n`; sanitize proven `\n`-safe. 3 test
  suggestions applied pre-merge: positive 63-byte boundary, `"a"*62 + "\n"`
  case, and the real-harm path `generate_fqdn(label="keen-falcon\n") →
  ValueError`. Suite 60 → 62.
- **Merge**: `bfef325` (squash), issue #3 auto-closed.

## Backlog (next up)

[#6](https://github.com/tempometer/domainame/issues/6) CI + badge →
[#4](https://github.com/tempometer/domainame/issues/4) CLI polish →
[#7](https://github.com/tempometer/domainame/issues/7) pyproject packaging →
[#9](https://github.com/tempometer/domainame/issues/9) UA README typos.

