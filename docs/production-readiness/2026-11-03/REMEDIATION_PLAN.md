# Courserefresh — remediation plan

This is future work, not an execution record. Findings and evidence are in [REVIEW.md](REVIEW.md). Do not use real learners, credentials, or public endpoints until the owner approves the security and deployment design.

## Dependency map and phase gates

| Phase / task | Depends on | Entry → exit |
|---|---|---|
| P0 / T1 baseline | Owner provides isolated workspace | Pinned source → recorded reproduction and risk inventory |
| P1 / T2 time and revert | T1 | Reproducible measurements → boundary and negative tests pass |
| P1 / T3 access and consent | T1, owner identity decision | Threat model → authenticated isolated integration tests pass |
| P2 / T4 evidence UX | T1 | Labeled demo → demonstrably honest evidence display |
| P2 / T5 automation | T2–T4 | Stable checks → separate required candidate checks exercised |
| P3 / T6 operations | T3, T5, owner platform approval | Deployment design → observed recovery in a non-production environment |
| P4 / T7 independent acceptance | T2–T6 | Evidence package → independent, owner-approved decision |

### T1 — Establish a reproducible baseline (CR-01–07)

**Paths:** observed `app/check.sh`, `app/tests/test_artifacts.py`, `app/lib/telemetry.py`, `viz/package.json`, `course-refresh-demo-video/package.json`. **Prerequisites:** isolated copy and owner permission; no production credentials.

1. Inventory versions, configuration, outputs and simulated versus external paths. 2. In a disposable, restricted environment run the documented `sh app/check.sh` as a **planned** baseline, recording status and logs. 3. Reproduce an expired telemetry event, partial revert and unauthenticated request without real learner data.

**Output:** revision-bound baseline and reproducible failure cases. **Verification:** a reviewer checks paths, isolation, exit codes and that reproductions exercise real code paths. **DoD:** [ ] Baseline captured. [ ] Each reproduction independently reviewed. [ ] No secrets or learner data in artifacts.

### T2 — Repair measurement and revert evidence (CR-02, CR-05)

**Paths:** observed `app/lib/telemetry.py:172–201`, `app/run_live.py:737–759`, `app/tests/test_artifacts.py:73–83`; test-file additions are proposed. **Prerequisite:** T1; owner agrees on time-window and version semantics.

1. Define UTC boundaries, malformed/future timestamps, and owner-approved eligibility for target, other-version and unversioned rows. 2. Filter before cohort/delta calculation, inject the clock, and wire the approved version rule from the actual `learn_phase` caller through the revert decision; fail safely when the target version is unknown. 3. Compare full restored content, allowing only the documented marker; test mixed old/new, boundary, malformed, future and wrong-version rows through the learn-to-revert seam.

**Output:** corrected calculation, version wiring and independent regression fixtures. **Verification:** integration fixtures invoke `learn_phase` with eligible and ineligible version rows chosen to alter the cohort or revert outcome if admitted; assert ineligible rows cannot change the gate or decision under the approved rule. Deliberately remove the time filter, bypass version wiring and corrupt a restored body; respective tests must fail, then pass with the intended implementation. **DoD:** [ ] Window and version eligibility match approved semantics. [ ] No stale-data or ineligible-version influence on the integration gate. [ ] Full restoration and negative controls verified.

### T3 — Secure console and learner intake (CR-01, CR-03; preventive injection/privacy)

**Paths:** observed `app/serve.py`, `app/lib/console.py`, `app/lib/telemetry.py`, `specs/security/threat-model.md`. **Prerequisites:** T1 and owner-approved identity and consent model.

1. Specify route roles, identity binding, consent, safe binds, TLS, retention and demo access. 2. Fail closed; protect reads/writes, remove URL credentials, add CSRF protection where relevant, enforce limits and block cross-learner consent changes. 3. Test unauthorized and cross-identity access, revocation, oversized input, replay, hostile text and privacy-safe logs through actual HTTP and decision paths.

**Output:** implemented access policy and updated threat model. **Verification:** independent tests prove denial with absent/wrong credentials, cross-learner submission and unauthorized resume; controlled valid requests succeed. Test transport encryption and secret redaction in the chosen deployment. **DoD:** [ ] No public fail-open default. [ ] Learner consent is identity-bound. [ ] Abuse and injection tests exercise real boundaries.

### T4 — Make demonstration evidence honest and usable (CR-04, CR-07)

**Paths:** observed `viz/src/components/AuthorConsole.tsx`, `viz/src/App.tsx`; the separate `course-refresh-demo-video/src/App.tsx` is also in scope for accessibility. **Prerequisite:** T1.

1. Replace the run-ID proxy with a verified chain result bound to artifact hash and revision, or display “unverified”. 2. Generate dated counts or label them historical; mark illustrative buttons non-operational or make them functional. 3. Test keyboard, names, focus, responsiveness, contrast, reduced motion and caption/speech alternatives in both frontends.

**Output:** provenance-aware demo and accessibility findings/fixes. **Verification:** a tampered chain never shows verified; stale or missing results are visibly unknown; keyboard and screen-reader checks are recorded. **DoD:** [ ] No misleading chain badge. [ ] Counts identify source and revision. [ ] Demonstration controls and accessibility verified.

### T5 — Gate each package independently (CR-06; preventive supply chain)

**Paths:** observed `.github/workflows/deploy-viz-pages.yml`, `viz/package.json`, `course-refresh-demo-video/package.json`, `app/check.sh`; new workflow paths and any missing typecheck/test scripts are **proposed**. **Prerequisites:** T2–T4.

1. Add PR checks for the Python battery and both frontends; define missing typecheck and UI test scripts. 2. Pin actions to reviewed commit SHAs, minimize permissions, and inspect lockfiles and advisories without automatic breaking upgrades. 3. Exercise triggers, artifact provenance and a broken test; distinguish Pages publishing from the engine gate.

**Output:** separate reproducible checks and dependency review. **Verification:** observe each check on the exact candidate SHA, and prove a negative control blocks its gate; owner verifies branch protection separately. **DoD:** [ ] All three package scopes have relevant checks. [ ] Action provenance reviewed. [ ] Broken behavior fails the gate.

### T6 — Deployment and recovery rehearsal (preventive operations)

**Paths:** observed `app/out/` runtime state described by `README.md:34–46`, `.github/workflows/deploy-viz-pages.yml`; deployment and backup configuration paths are **proposed**. **Prerequisites:** T3, T5 and owner approval of platform, accounts, data classification and recovery targets.

1. Define approvals, credential rotation, health, budgets, backup scope, retention and recovery objectives. 2. Deploy to isolated staging; validate access, authorized integrations, pause/resume and notifications. 3. Restore a backup separately, verify chain and course content, rehearse rollback and measure recovery time.

**Output:** runbook and observed staging release/restore evidence. **Verification:** compare restored artifacts and consent state against backups; inspect live staging health and exercise failure alerting. **DoD:** [ ] Recovery measured. [ ] Rollback restores known version and data. [ ] Owner accepts residual risk and operational responsibility.

### T7 — Independent acceptance (all findings)

**Paths:** all observed paths above; evidence package location is **proposed**, not yet created. **Prerequisites:** T2–T6.

1. An independent reviewer maps findings to changes and runtime consumers. 2. Repeat chain-tampering, stale-telemetry, unauthorized-control and broken-revert negative controls. 3. Inspect exact-SHA CI, restore and accessibility evidence; record unresolved items.

**Output:** acceptance ledger with pass/fail/unknown and release SHA. **Verification:** independently reproduce selected results rather than relying on author assertions or check counts. **DoD:** [ ] Each finding disposition supported. [ ] No failed negative control hidden. [ ] Owner signs release decision.

## Production acceptance and release policy

- [ ] Access, identity, privacy and retention approved; no unauthenticated network control or cross-learner consent mutation.
- [ ] Window and version rules, complete restoration and author-review gates independently demonstrated.
- [ ] Exact-SHA checks, dependency review, frontend accessibility and staged integration evidence recorded.
- [ ] Credentials and external accounts provisioned by owner; alerting, backup restore and rollback observed.
- [ ] Demo claims distinguish simulation, historic evidence and live measured behavior.

Owner approval is required for real data, network exposure, credentials, dependency major upgrades, external spend, deployment and retention/deletion policy. Release from a reviewed immutable revision; on incident, pause mutation, preserve restricted evidence, roll back code and compatible state, restore from verified backups when needed, and verify service and data before resuming. Never weaken tests or thresholds to make a gate pass.
