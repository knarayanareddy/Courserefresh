# AGENTS.md — how to work in this repo without breaking it

You are (probably) an autonomous coding agent. This file is the entry contract. `specs/` is the
source of truth; if code disagrees with the spec, the spec wins until the spec is changed first
(`specs/constitution.md` Art. XVI).

## Read, in this order, before touching anything

1. `specs/constitution.md` — 16 articles. Articles II–XV are non-negotiable; Art. XII least of all.
2. `specs/README.md` — the package index and which file answers which question.
3. `specs/courserefresh/BUILD.md` §0 — the build order and the Core-First Warden's veto.
4. `specs/courserefresh/tasks.md` — what is done (`[x]`), degraded (`[~]`), blocked (`[!]`), todo (`[ ]`).
5. `specs/courserefresh/TRACEABILITY.md` — every AC with the command that proves it.
6. `specs/courserefresh/SETUP.md` — the credential checklist (names only; `.env` is gitignored) and the
   exact commands that prove the wiring before any key exists.

## The laws that bite

- **Models propose, code decides** (Art. VIII). Never let model output select an action; the
  decision lives in `specs/courserefresh/skin/policy.py` (oracle) and `app/n8n/policy_node.js`
  (production). Both must stay identical: `node app/tests/test_gate_parity.py`.
- **Never invent a number** (Art. VI). `unmeasured` is legal; a plausible guess is a violation.
  Put measured values in `specs/courserefresh/RECEIPTS.md`, never a memory of a value.
- **No publish without a `revert_gate`** (Art. XI). If your change can alter a lesson without a
  declared undo condition, it is a bug.
- **Don't touch the gold set to make a test pass** (Art. VII). `skin/gold.jsonl` is frozen at a
  version; relabel only with a new `gold_version` and a row in `AMENDMENTS.md`.
- **A course change keeps the course coherent** (review 05, teacher seat): every lesson has objectives
  and prerequisites in `course/agent-ops/curriculum.json`; a change regenerates the quiz item it
  affects and *names* the downstream lessons to revisit — it never rewrites them unattended.
  `python3 app/tests/test_curriculum.py` decides.
- **Never read `os.environ` by hand.** Use `app/lib/config.py` (`Config`), so precedence stays
  explicit > environment > `.env` > defaults, secrets are never printed, and the preflight can name
  what is missing. Round 3 shipped with this bug; `test_live_modules.py` now fails if it returns.
- **The canvas decides, the oracle polices.** If you touch `app/n8n/policy_node.js`, re-run
  `python3 app/tools/make_n8n_exports.py` (the exports embed it byte-for-byte) and
  `node app/tests/test_gate_parity.py`. If you touch either rulebook, the other must change in the
  same commit or the battery fails.
- **Nothing leaves the machine with a key in it.** Before you share a run, use
  `python3 app/tools/collect_live.py`: it redacts every secret value it can see, summarises learner
  telemetry as counts, and exits 3 (refusing the handoff) if a secret-shaped string survived.
  `app/tests/test_handoff.py` proves it, including a planted token.
- **A receipt must still describe the file.** If you change anything that writes artifacts, run `python3 app/tests/test_artifacts.py` — hashes are re-computed from disk, and a revert must keep the text it claims to restore (Art. IX.3).
- **Hostile input is in scope** (Art. X): `cr-inject-01` must always escalate, with the hostile
  string visible on the receipt.
- **A review finding is `open` until its verification command's output is pasted** (Art. XVI.4).
  See `specs/courserefresh/AMENDMENTS.md`.

## Everyday commands

```sh
sh app/check.sh                                     # the whole battery — must be green before you claim anything
python3 specs/courserefresh/skin/policy.py --eval specs/courserefresh/skin/gold.jsonl
python3 specs/courserefresh/skin/policy.py --explain cr-inject-01
python3 app/run_walking_skeleton.py                 # one loop, sim mode, writes course/**
python3 app/run_walking_skeleton.py --seed-demo    # adds the labelled seeded rehearsal
python3 app/run_walking_skeleton.py --report        # the digest
python3 app/tools/metrics.py                        # one JSON of every number the run produced
python3 app/tools/reset_course.py                   # back to the authored baseline (v3 / v1s)
python3 app/tools/make_n8n_exports.py               # regenerate wf-cr-* around the current policy node
python3 app/tests/test_curriculum.py                # objectives, quiz alignment, micro-lesson contract
python3 app/tests/test_artifacts.py                 # artifacts vs receipts, caps, the failed-write path
python3 app/run_walking_skeleton.py --root app/out/e7 --chaos write-fail   # rehearse a witnessed failure
```

## House rules

- Writes go to `course/**` (the artifact) and `app/out/**` (gitignored state). Nothing else is
  written at runtime; a publish path outside `course/**` is rejected before the write (TM16).
- No network calls from `app/**` or the n8n `POLICY` node. Fetching is Apify's job in the live loop.
- Plain `python3` only in the test battery (no pytest dependency); exit code 0 = green.
- When you change behaviour: update the spec first, add the `AMENDMENTS.md` row, then the code —
  and never claim a task is done until its command has run in front of you.
