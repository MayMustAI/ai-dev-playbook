# Bundled third-party instructions

MayMust 0.6.0 distributes the files below at fixed upstream commits. Installation
does not download upstream `main` or run upstream installers. The complete list of
copied files and their SHA-256 hashes is in [skills.lock.json](third-party/skills.lock.json).
Copied instruction/style files are unchanged; MayMust runtime metadata lives beside
them, and team adaptations live in [team-defaults](skills/team-defaults/SKILL.md).

| Source | Pinned commit | Included material | Upstream license |
| --- | --- | --- | --- |
| [obra/superpowers](https://github.com/obra/superpowers/tree/8ca22dba9a94f28898bbce59f2537ff4d87c747d) | `8ca22dba9a94f28898bbce59f2537ff4d87c747d` | Only `verification-before-completion/SKILL.md` | MIT |
| [alexgreensh/attention-span](https://github.com/alexgreensh/attention-span/tree/2714c965e6be1fa2597510e66651e63bc67cb448) | `2714c965e6be1fa2597510e66651e63bc67cb448` | Attention-kind, Spartan, Rundown, TLDR skills; three native Claude output styles | AGPL-3.0 |
| [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills/tree/2c606141936f1eeef17fa3043a72095b4765b9c2) | `2c606141936f1eeef17fa3043a72095b4765b9c2` | `karpathy-guidelines/SKILL.md` | MIT (declared upstream) |

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

To update a source, review the new upstream commit, replace only the selected files,
update the commit and hashes in the lock file and this notice, inspect any license
changes, run the hook/distribution tests, and bump the plugin version. Preserve the
one-skill selection for Superpowers.
