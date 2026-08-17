# Contributing

Two things live here and they have different bars: **skills** in `skills/`, and
**runnable evals** in `examples/`. Mechanics for each are in
[skills/README.md](skills/README.md) and [examples/README.md](examples/README.md). This
file covers what gets accepted.

## What makes a good skill

A skill earns its place by owning **one artifact** that something downstream consumes. If
you cannot name the artifact it produces and the skill that consumes it next, it is
probably a section of an existing card rather than a new one.

The card format is a constraint, not a template to fill:

- **Trigger** — the requests that should route here, including the ones that look similar
  and should not.
- **Do** — the procedure, in order. Six or seven steps. Each one an action, not a topic.
- **Avoid** — the mistakes people actually make at this stage, not generic caution.
- **Check** — what "done" means, verifiable by reading the artifact.
- **Risk** — what goes wrong *even when the procedure was followed*. This is the section
  that carries the most value and the one most often written as filler.
- **Braintrust** — platform mechanics specific to this stage.

Write the `description` frontmatter for a router, not a human. It should state when to
use the skill **and when not to**, since the "do not use" half is what prevents a broad
skill from swallowing requests that belong elsewhere.

## Rules the review will check

**One criterion, one home.** If a paragraph would be true of three or more skills, it
belongs in `skills/PLATFORM.md` or `skills/INTERACTION.md`, cited rather than restated.
Duplication across cards drifts silently and is the main thing this library keeps fighting.

**Numbers carry a hedge and a source.** Thresholds go in `references/`, never in the card,
and every empirical claim carries a provenance tag. A number that *is* the method — the
rule of three, K ≥ 3 runs, ≥ 2 raters — stays in the card. Tunable defaults do not.

**No dead references.** Every `references/*.md` pointer, cross-skill mention, and link
must resolve. No paths from your machine, no pointers into repos a reader cannot open, no
names of colleagues.

**Frontmatter must be valid.** `name` matches the directory exactly, is lowercase with
hyphens, under 64 characters, and prefixed `braintrust-`. `description` stays under 1,024
characters. These come from the [Agent Skills standard](https://agentskills.io); breaking
them makes the skill unloadable rather than merely untidy.

**Mirrors are generated.** Never hand-edit `references/interaction-contract.md` or
`references/platform-mechanics.md`. Edit the source and re-run the loop in
`skills/README.md`.

## Checking your work

```bash
# names match directories, prefixes and caps hold, references resolve, mirrors intact
python3 - <<'PY'
import re, os, glob
skills = {d for d in os.listdir('skills') if os.path.isdir(f'skills/{d}')}
bad = []
for sk in sorted(skills):
    body = open(f'skills/{sk}/SKILL.md').read()
    fm = re.match(r'^---\n(.*?)\n---\n', body, re.S)
    if not fm: bad.append(f'{sk}: no frontmatter'); continue
    name = re.search(r'^name: (.+)$', fm.group(1), re.M)
    if not name or name.group(1).strip() != sk: bad.append(f'{sk}: name != directory')
    elif len(sk) > 64 or not re.fullmatch(r'[a-z0-9-]+', sk): bad.append(f'{sk}: invalid name')
    elif not sk.startswith('braintrust-'): bad.append(f'{sk}: missing prefix')
    for r in re.findall(r'`(references/[\w.-]+\.md)`', body):
        if not os.path.exists(f'skills/{sk}/{r}'): bad.append(f'{sk}: dangling {r}')
for src, dst in (('skills/INTERACTION.md', 'interaction-contract'),
                 ('skills/PLATFORM.md', 'platform-mechanics')):
    text = open(src).read()
    for m in glob.glob(f'skills/*/references/{dst}.md'):
        if not open(m).read().endswith(text): bad.append(f'{m}: drifted from {src}')
print('\n'.join(bad) if bad else f'clean — {len(skills)} skills')
PY
```

## Examples

Lower ceremony, one bar: it has to run. Self-contained directory, its own README covering
the question and the commands, pinned models and dataset version, no credentials, no
absolute paths. An example is worth adding when it demonstrates something a card can only
describe.

## Licensing

Contributions are accepted under [Apache 2.0](LICENSE).
