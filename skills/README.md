# skills/

The skills themselves. For what each one does and when to reach for it, see the
annotated catalog and routing tables in the [root README](../README.md) — this file
covers only the mechanics of the directory.

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

## Installing

Symlink the ones you want into `~/.claude/skills/` (or `.claude/skills/` in a repo):

```bash
for d in /path/to/eval-library/skills/*/; do
  ln -sfn "${d%/}" ~/.claude/skills/"$(basename "$d")"
done
```

Symlinks beat copies — edits land immediately and there is one source of truth.
Copying a directory also works, since each is self-contained by design.

## The two mirrored files

`interaction-contract.md` and `platform-mechanics.md` are copies of `INTERACTION.md`
and `PLATFORM.md` at the repo root. They ship inside each skill so a directory works
standalone when copied somewhere else.

**Edit the root file, then re-mirror. Never edit a mirror.**

```bash
cd /path/to/eval-library
for f in INTERACTION.md:interaction-contract.md PLATFORM.md:platform-mechanics.md; do
  src="${f%%:*}"; dst="${f##*:}"
  for d in skills/*/; do
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
