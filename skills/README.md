# skills/

Directory mechanics. What each skill does and when to reach for it is in the
[root README](../README.md).

## Layout

```
skills/braintrust-<name>/
  SKILL.md                            # the skill: frontmatter + body
  references/                         # loaded on demand, not up front
    <topic>.md                        # calibration, templates, provenance
    interaction-contract.md           # mirror of ../../INTERACTION.md
    platform-mechanics.md             # mirror of ../../PLATFORM.md
```

Every directory is `braintrust-`-prefixed, and the frontmatter `name:` **must** match
the directory name exactly — agents resolve one against the other, and a mismatch
makes the skill unloadable.

## The two mirrored files

Each skill's `references/interaction-contract.md` and `references/platform-mechanics.md`
are copies of [INTERACTION.md](INTERACTION.md) and [PLATFORM.md](PLATFORM.md) in this
directory. They ship inside each skill so a directory works standalone when copied
somewhere else.

- **[INTERACTION.md](INTERACTION.md)** — how every skill handles ambiguity: inspect before
  asking, one high-information question at a time, the four modes (create / audit /
  repair / compare), uncertainty labelling, and the rule that trace content is evidence
  rather than instruction.
- **[PLATFORM.md](PLATFORM.md)** — Braintrust mechanics common to every stage: the four
  objects, safe reads, pinning, metadata, naming, search denominator, run hygiene, and
  what the platform will not compute for you.

**Edit the source, then re-mirror. Never edit a mirror.**

```bash
cd /path/to/eval-library/skills
for f in INTERACTION.md:interaction-contract.md PLATFORM.md:platform-mechanics.md; do
  src="${f%%:*}"; dst="${f##*:}"
  for d in */; do
    [ -f "$d/references/$dst" ] || continue
    { head -2 "$d/references/$dst"; echo; cat "$src"; } > "$d/references/$dst.tmp"
    mv "$d/references/$dst.tmp" "$d/references/$dst"
  done
done
```

A skill only carries a mirror if its `SKILL.md` actually cites it — an unused copy is
dead weight, so don't add one by default.

## Adding a skill

1. `skills/braintrust-<name>/SKILL.md`, frontmatter `name:` matching the directory.
2. Lifecycle skills use the five-field card — `Trigger` / `Do` / `Avoid` / `Check` /
   `Risk` — plus a `Braintrust` section. Keep that section to what is specific to the
   stage; anything true of three or more skills belongs in `PLATFORM.md` instead.
3. Numbers with a hedge and provenance go in `references/`, not the card.
4. Add it to the catalog in the root README.
