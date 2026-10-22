# Bundled third-party instructions

MayMust 0.8.1 distributes the files below at fixed upstream commits. Installation
does not download upstream `main` or run upstream installers. The complete list of
copied files and their SHA-256 hashes is in [skills.lock.json](third-party/skills.lock.json).
Copied instruction/style files are unchanged; MayMust runtime metadata lives beside
them, and team adaptations live in [team-defaults](skills/team-defaults/SKILL.md).
Material adapted from pstack is the one exception: it is modified on purpose, so the
lock file records the hash of each upstream file it came from instead of a hash of
the shipped copy. See [Adapted material from pstack](#adapted-material-from-pstack-2026-10-22).

| Source | Pinned commit | Included material | Upstream license |
| --- | --- | --- | --- |
| [obra/superpowers](https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d) | `8ca22dba9a94f28898bbce59f2537ff4d87c747d` | Only `verification-before-completion/SKILL.md` | MIT |
| [alexgreensh/attention-span](https://github.com/alexgreensh/attention-span/tree/f4ae0de76ed3ab98fa9398a56f30bbfbaa146590) | `f4ae0de76ed3ab98fa9398a56f30bbfbaa146590` (0.10) | Attention-kind, Spartan, Rundown, TLDR skills; three native Claude output styles. Since upstream 0.9 they live under `plugins/attention-span/` | AGPL-3.0 |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/tree/2c606141936f1eeef17fa3043a72095b4765b9c2) | `2c606141936f1eeef17fa3043a72095b4765b9c2` | `karpathy-guidelines/SKILL.md` | MIT (declared upstream) |
| [cursor/plugins `pstack/`](https://github.com/cursor/plugins/tree/f2bad5225cb2d4f5e58b45aa36be89d16a558c13/pstack) | `f2bad5225cb2d4f5e58b45aa36be89d16a558c13` | `LICENSE` copied unchanged; methods from 17 files adapted into MayMust skills (below) | MIT |

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

## Adapted material from pstack, 2026-10-22

pstack's playbook router, PR, merge, autopilot, and worktree-cleanup steps are not
bundled, because they conflict with the MayMust commit, PR, review, and merge flow.
Only methods that fit that flow were adapted. Each adapted Markdown file in a new
skill starts with a provenance comment that names its upstream path and commit.

| Upstream file under `pstack/skills/` | MayMust file under `skills/` |
| --- | --- |
| `blast-radius/SKILL.md` | `blast-radius/SKILL.md` |
| `benchmark-checklist/SKILL.md`, `principle-explain-the-number/SKILL.md` | `benchmark-checklist/SKILL.md` |
| `how/SKILL.md` and its two prompt templates | `how/` |
| `why/SKILL.md`, `epistemics.md`, investigator and synthesizer prompts, five source guides | `why/` |
| `principle-test-behavior-not-implementation/SKILL.md` | test lens in `self-review/SKILL.md` and `codex-review/references/reviewer-prompt.md` |
| `show-me-your-work/SKILL.md` | evidence rule in `worklog/SKILL.md` |

Changes from upstream: rewritten in Korean to match the other team workflow skills;
Cursor tool names, model roles, the `pstack-models` rule, and the Cursor adapter
removed; subagents made optional so the same skills run in Claude Code and Codex;
`why` sources limited to git, Linear, Notion, and Slack, with `.worklogs/` added to
the git source; investigators and synthesizers made explicitly read-only; results
wired to `pull-request`, `worklog`, and `codex-review`. `how` and `why` are
explicit-only in both runtimes because each run can start several subagents.

`python3 scripts/check_upstream.py` (from the repository root) compares every tracked
file with its upstream's latest commit and prints a JSON report. With `--apply` it copies
changed files and updates the lock, but only for a source whose tracked paths all still
exist, whose license file did not change, and whose adapted material did not change.
It never edits adapted material, so the pinned commit keeps matching every recorded hash.

To update a source, review the new upstream commit, replace only the selected files,
update the commit and hashes in the lock file and this notice, inspect any license
changes, run the hook/distribution tests, and bump the plugin version. Preserve the
one-skill selection for Superpowers. For pstack, compare each upstream path at the
new commit with its `upstream_sha256`, port the relevant changes by hand, and then
update the commit, hashes, and provenance comments.
