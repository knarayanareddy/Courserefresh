# Frozen evidence — cr-20260926-1726-793

Shipped with the repository on purpose: `app/out/` is gitignored, so a pointer into it
resolves to nothing on a clone and the hashes in `specs/courserefresh/EVIDENCE.md`
cannot be checked by anyone. Everything here is a copy of a real run's artifacts.

- `MANIFEST.sha256` — every file, hashed. `app/tools/audit_claims.py` re-hashes it on
  every battery run, so a bundle that no longer matches its manifest fails the build.
- `receipts.jsonl` — the chained decision log (each row hashes the row before it).
- `digest.md` / `digest.html` — the report and the console page, refusals first.
- `course/**` — the lesson versions and diffs the run wrote.

Regenerate a local copy with the commands in `EVIDENCE.md` §4; the run id will differ
(it is a timestamp), which is why the hashes here are the ones that travel.
