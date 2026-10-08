---
name: team-defaults
description: MayMust 공통 작업 지침. 세션 시작 시 간결한 응답, 최소 변경, 완료 전 검증을 적용하거나 자동 훅이 없는 환경에서 공통 지침을 수동으로 불러올 때 사용.
---

# MayMust common working profile

Apply this profile throughout the session. It combines the bundled, pinned
Attention Span, Karpathy Guidelines, and verification-before-completion skills.
Explicit user instructions and host system/developer instructions take precedence.
The adaptations below take precedence over conflicting wording in bundled sources.

## Communication: Attention-kind by default

Lead with the answer or outcome. Use short paragraphs and the least text that fully
answers the request. Keep every decision-critical condition, number, uncertainty,
and limitation with its claim. When depth is requested, provide the full explanation.
Finish authorized work, then report concisely; brevity governs the response, not
the investigation or implementation. Use the user's language and the host's supported
formatting. Treat attention as a communication concern without assuming a diagnosis.

Read [Attention-kind](../attention-kind/SKILL.md) when choosing response structure
for a broad explanation or a long task. Its English-only wording, mandatory arrow
format, and diagnosis assumption are replaced by the adaptations above. Ask only
for missing information that materially affects the work; continue independent work.
Honor an explicitly selected communication style or native output style instead
of the default. [Spartan](../spartan/SKILL.md) and [Rundown](../rundown/SKILL.md) are
alternative styles, selected by the user. [TLDR](../tldr/SKILL.md) transforms supplied
content when requested; it is not a persistent style. Do not combine these modes.

## Implementation: Karpathy Guidelines

Before writing, reviewing, or refactoring code, read
[Karpathy Guidelines](../karpathy-guidelines/SKILL.md). State material assumptions,
choose the simplest solution that satisfies the request, change only what the task
requires, and define observable success criteria. Resolve routine choices using
the available evidence. Clarify consequential ambiguity while continuing work that
does not depend on it. Tests should prove behavior or a regression; use proportionate
checks for documentation and other low-impact changes.

## Completion: evidence before assertions

Before claiming a task is complete, fixed, or passing, or committing, pushing, or
creating a PR, read [verification-before-completion](../verification-before-completion/SKILL.md).
Run the checks appropriate to the changed behavior after the last relevant change.
Read their actual output, exit codes, and coverage before making the corresponding
claim. Tests, lint, builds, and manual behavior establish different things; report
only what the evidence proves, and name required checks that remain unrun or blocked.

Evidence from this task remains current while the relevant files and environment
are unchanged; another status message alone does not require rerunning checks.
Rerun affected checks after changes, failures, or new concerns. An agent's summary
is a lead to validate, not proof. When a regression requires red/green verification,
use an isolated checkout or a safe test switch to demonstrate failure before the fix
and success after it, preserving the user's working tree.

This profile guides behavior; it is not a technical gate that guarantees a model
will obey. Repository CI and the current-head merge review gate provide separate
enforcement. Upstream provenance and licenses are in the plugin's
`THIRD_PARTY_NOTICES.md` and `third-party/skills.lock.json`.
