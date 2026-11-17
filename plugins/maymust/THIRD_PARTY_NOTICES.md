# Bundled third-party instructions

MayMust 0.12.0 distributes the files below at fixed upstream commits. Installation
does not download upstream `main` or run upstream installers. The complete list of
copied files and their SHA-256 hashes is in [skills.lock.json](third-party/skills.lock.json).
Copied instruction/style files are unchanged; MayMust runtime metadata lives beside
them, and team adaptations live in [team-defaults](skills/team-defaults/SKILL.md).
Three embedded principles from pstack are modified on purpose, so the
lock file records the hash of each upstream file it came from instead of a hash of
the shipped copy. See [pstack upstream fidelity](#pstack-upstream-fidelity-2026-11-16).

| Source | Pinned commit | Included material | Upstream license |
| --- | --- | --- | --- |
| [obra/superpowers](https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d) | `8ca22dba9a94f28898bbce59f2537ff4d87c747d` | Only `verification-before-completion/SKILL.md` | MIT |
| [alexgreensh/attention-span](https://github.com/alexgreensh/attention-span/tree/39c6b46b24dddecc4cef4e3ab8dc36d3fbffeb42) | `39c6b46b24dddecc4cef4e3ab8dc36d3fbffeb42` (0.12) | Attention-kind, Spartan, Rundown, TLDR skills; three native Claude output styles. Since upstream 0.9 they live under `plugins/attention-span/` | AGPL-3.0 |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/tree/2c606141936f1eeef17fa3043a72095b4765b9c2) | `2c606141936f1eeef17fa3043a72095b4765b9c2` | `karpathy-guidelines/SKILL.md` | MIT (declared upstream) |
| [cursor/plugins `pstack/`](https://github.com/cursor/plugins/tree/bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7/pstack) | `bf0c7cd80abdbf7fe47b634978a7d1b4071f71a7` | Four standalone skills + LICENSE copied unchanged; three embedded principles adapted | MIT |

## License notices

- Superpowers: Copyright (c) 2025 Jesse Vincent. The upstream MIT notice is preserved
  in [third-party/superpowers/LICENSE](third-party/superpowers/LICENSE).
- Attention Span: upstream attribution is alexgreensh/attention-span. Its complete
  AGPL-3.0 text is preserved in
  [third-party/attention-span/LICENSE](third-party/attention-span/LICENSE).
  Its four skills, three output styles, and the Attention Span adaptations in
  `skills/team-defaults/SKILL.md` are covered by that notice. This repository supplies
  their source as Markdown, alongside the runtime adapter that loads the profile.
- Karpathy Guidelines: the bundled skill retains its `license: MIT` declaration.
  The pinned [upstream README](https://github.com/multica-ai/andrej-karpathy-skills/blob/2c606141936f1eeef17fa3043a72095b4765b9c2/README.md)
  also declares MIT. That upstream commit contains no standalone `LICENSE` file;
  no missing copyright notice has been invented here.
- pstack: Copyright (c) 2026 Lauren Tan. The upstream MIT notice is preserved in
  [third-party/pstack/LICENSE](third-party/pstack/LICENSE) and covers the adapted
  material listed below.

The plugin's license metadata lists both MIT and AGPL-3.0. Do not describe the entire
bundle as MIT-only or remove the upstream notices when redistributing it.

## MayMust adaptations, 2026-10-06

The separate common profile uses Attention-kind as the default, with user-selected
styles taking precedence. It follows the user's language and host formatting,
does not assume a medical diagnosis, and finishes authorized work without adding
unnecessary confirmation steps. Karpathy's principles apply with proportionate
checks. Verification evidence must follow the last relevant change; unchanged,
already-verified work does not need repeated checks for every status message.
Regression red/green demonstrations preserve the user's working tree.

## pstack upstream fidelity, 2026-11-16

At the user's direction, the standalone `blast-radius`, `benchmark-checklist`,
`how`, and `why` SKILL.md files now match the pinned upstream bytes exactly.
`how` uses one exploration/explanation pass. `why` starts with the introducing and
subsequent commits and PR discussions, consulting other sources when that record
is thin. Ten how/why reference files deleted upstream are also removed locally;
the previous source-by-source fan-out and fixed report format are not retained.
All pstack tracking is consolidated at the commit above, including the former
`pstack-benchmark` source. No historical compatibility fork remains.

The same MIT license bytes are preserved. Runtime metadata lives in agents/openai.yaml.
`team-defaults` only maps Cursor-only tools and unbundled playbook names to the host:
Task to an available read-only agent (or sequential fallback), arena to available
independent perspectives, unslop to clarity editing, Opening a PR to the existing
MayMust PR workflow. It does not recreate deleted investigation templates.

Three principles already embedded in team-owned workflows remain adapted:
- principle-explain-the-number: pre-measurement decision/noise floor and evidence
  rules in team-defaults, without altering the upstream benchmark skill.
- principle-test-behavior-not-implementation: the test lens in self-review and
  codex-review, mirrored in the standalone independent-review prompt.
- show-me-your-work: evidence rules in pull-request Design decisions.
These are fragments, not claims that the full upstream skills are installed.
Their input hashes and local use sites are in skills.lock.json.

Future sync follows upstream renames, consolidation and deletion for selected
pstack material after checking provenance, license, local integrity and references.
Do not silently create a MayMust-only fork to preserve an upstream-deleted workflow.
License or capability changes still require review; no upstream text grants new
permissions. The current check_upstream.py mechanically updates copied files only;
adapted changes and deletion/remapping need the scheduled agent's reviewed patch.
