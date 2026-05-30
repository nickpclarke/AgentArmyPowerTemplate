# Architecture Decision Records (ARC-ADR)

Decisions live here as `ARC-ADR-NNN-<slug>.md`. This README documents **how the
number is allocated** — because hand-picking it is a race that has bitten us twice.

## Never hand-pick a number

Choosing "highest existing number + 1" at authoring time is a read-modify-write
race: two parallel sessions both read `NNN` as the max and both write
`ARC-ADR-(NNN+1)-*.md`. Git does **not** flag it (the filenames differ), so the
collision only surfaces after both merge. This is what happened to ARC-ADR-038
(three-way) and again to ARC-ADR-040.

There are only two ways to make a counter collision-free: **serialize allocation**
or **stop using a shared counter**. We serialize — at merge, which is already a
serial point — and keep the human-friendly sequential integers.

## How to author an ADR

1. **Name it `ARC-ADR-DRAFT-<slug>.md`** (kebab-case slug). Do not put a number in
   the filename.
2. Inside the file, use the literal token **`ARC-ADR-DRAFT`** wherever the number
   would go (the `# ARC-ADR-DRAFT — Title` heading and the `| ID | ARC-ADR-DRAFT |`
   field). Scaffold it with `node tools/data-vault/adr-scaffold.mjs "Title"` or the
   `/ea-adr` command — both emit a draft.
3. **Inside this draft's own file**, use the bare `ARC-ADR-DRAFT` token (title +
   `ID`) — the assigner rewrites those in place. **To link a not-yet-numbered
   draft from any *other* file** (a Labs note, another ADR), reference it by its
   full stem `ARC-ADR-DRAFT-<slug>`: the assigner rewrites full-stem references
   repo-wide, whereas a bare `ARC-ADR-DRAFT` in another file would be left
   dangling. Reference already-numbered ADRs by their stem too (`ARC-ADR-016-...`).
4. Open the PR as normal. The draft keeps its `DRAFT` name through review.

## How the number gets assigned

- **Merge-time assigner** — [`.github/workflows/adr-assign-numbers.yml`](../../.github/workflows/adr-assign-numbers.yml)
  runs on push to `main`. It finds every `ARC-ADR-DRAFT-*.md`, allocates the next
  free integer(s), renames the file, and rewrites the `ARC-ADR-DRAFT` token plus
  every cross-reference (by slug stem) across the repo. A `concurrency` group
  serializes runs, so two near-simultaneous merges can never get the same number.
- **PR guard** — [`.github/workflows/adr-number-guard.yml`](../../.github/workflows/adr-number-guard.yml)
  fails any PR where two decision files share an `ARC-ADR-NNN` prefix. This is the
  backstop for ADRs that were hand-numbered anyway.

Both wrap one script: [`tools/adr-numbers.mjs`](../../tools/adr-numbers.mjs)
(`check` for the guard, `assign` for the merge-time job). Run `node
tools/adr-numbers.mjs check` locally any time.

## Notes

- Numbers are monotonic and never reused; **gaps are fine** (a superseded or
  abandoned draft simply leaves a hole).
- Renames preserve git history (`git` detects the move on commit).
- The `ARC-ADR-NNN` scheme is per-repo. In a spoke, ADR numbers are independent of
  the hub's — disambiguate across repos by repo name when cross-linking, not by
  the number alone.
