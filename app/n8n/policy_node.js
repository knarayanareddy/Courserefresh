/**
 * Courserefresh POLICY node — production rulebook (n8n Code node, Run Once for Each Item).
 *
 * This file is loaded verbatim into the n8n canvas (WIRING.md §3) and is kept identical to the
 * oracle `specs/courserefresh/skin/policy.py` by `app/tests/test_gate_parity.py`.
 *
 * Rule order (normative): safety -> evidence -> relevance -> authority -> integrity -> budget ->
 * default ESCALATE(unknown_state). First match wins. No network, no clock, no randomness.
 *
 * Input:  the DecisionInput (specs/shared/data-model.md §5) as `item.json.input`
 * Output: { action, reason_codes, authority, notes }
 */

const THRESHOLDS = {
  evidence: { min_sources: 2, source_agreement_min: 0.5, quote_supported_min: 0.8 },
  relevance: { learner_impact_min: 0.4 },
  safety: { injection_min: 0.5 },
  budgets: { publishes_per_day: 6, tokens_per_change: 60000, notify_per_learner_day: 1, notify_per_learner_week: 3 },
  revert: { n_min: 5, window_h: 48 },
  diff: { max_lines: 400 }
};

const COHORT_NOTIFY = ["material_breaking", "material_deprecation"];
const PUBLISHABLE = ["material_breaking", "material_deprecation", "material_new_capability"];
const MATERIALITIES = ["material_breaking", "material_deprecation", "material_new_capability", "cosmetic",
  "marketing_noise", "ambiguous", "contradictory", "unverifiable"];
const AUTHORITIES = ["PA0", "PA1", "PA2", "PA3"];

function num(v) {
  if (typeof v === "boolean" || v === null || v === undefined) return null;
  const n = Number(v);
  if (!isFinite(n)) return null;
  return n >= 0 && n <= 1 ? n : null;
}

function out(action, reasons, authority, notes = "") {
  return { action, reason_codes: reasons, authority, notes };
}

function independentPublishers(sources) {
  if (!Array.isArray(sources) || sources.length === 0) return null;
  const set = new Set(sources.filter((s) => s && typeof s === "object")
    .map((s) => String(s.publisher || s.source_id || "?").toLowerCase()));
  return set.size;
}

function malformed(inp) {
  const required = ["event_id", "stream", "materiality", "learner_impact", "source_agreement",
    "quote_supported", "sources_verified", "injection_or_jailbreak", "authority", "freeze_active"];
  for (const f of required) if (inp[f] === undefined || inp[f] === null) return f;
  if (!MATERIALITIES.includes(inp.materiality)) return "materiality";
  if (!AUTHORITIES.includes(inp.authority)) return "authority";
  for (const f of ["learner_impact", "source_agreement", "quote_supported", "injection_or_jailbreak"]) {
    if (num(inp[f]) === null) return f;
  }
  if (!["change", "learner", "revert"].includes(inp.stream)) return "stream";
  return null;
}

function decideChange(inp) {
  const a = inp.authority, m = inp.materiality, b = inp.budgets || {};
  // 1) safety
  if (inp.freeze_active) return out("DRAFT", ["freeze_active"], a);
  if (num(inp.injection_or_jailbreak) >= THRESHOLDS.safety.injection_min) return out("ESCALATE", ["injection_or_jailbreak"], a);
  if (inp.assessment_touched) return out("ESCALATE", ["assessment_change_requires_human"], a);
  // 2) evidence
  if (m === "contradictory") return out("ESCALATE", ["source_conflict"], a);
  if (m === "unverifiable") return out("ESCALATE", ["unverifiable"], a);
  if (m === "ambiguous") return out("ESCALATE", ["ambiguous_change"], a);
  if (inp.seed) {
    if (inp.claims_upstream) return out("ESCALATE", ["seeded_source_misrepresented"], a, "rehearsal presented as a vendor change");
    return out("PUBLISH", [m, "seeded_rehearsal"], a, "SEEDED REHEARSAL — not a vendor release");
  }
  const publishers = independentPublishers(inp.sources);
  if (publishers !== null && publishers < THRESHOLDS.evidence.min_sources) {
    return out("ESCALATE", ["insufficient_corroboration"], a,
      publishers + " independent publisher(s) in " + Number(inp.sources_verified) + " source(s)");
  }
  if (Number(inp.sources_verified) < THRESHOLDS.evidence.min_sources ||
      num(inp.source_agreement) < THRESHOLDS.evidence.source_agreement_min) return out("ESCALATE", ["insufficient_corroboration"], a);
  if (num(inp.quote_supported) < THRESHOLDS.evidence.quote_supported_min) return out("ESCALATE", ["quote_unsupported"], a);
  // 3) relevance
  if (m === "marketing_noise") return out("NO_CHANGE", ["immaterial_change"], a);
  if (m === "cosmetic" || num(inp.learner_impact) < THRESHOLDS.relevance.learner_impact_min) return out("DRAFT", ["low_learner_impact"], a);
  // 4) authority
  if (a === "PA0") return out("DRAFT", ["authority_insufficient"], a, "PA0: observe only");
  if (COHORT_NOTIFY.includes(m) && a !== "PA2") return out("DRAFT", ["authority_insufficient"], a, "cohort notification required (PA2)");
  // 5) integrity floor
  if (inp.revert_gate_present === false) return out("ESCALATE", ["integrity_floor_missing_gate"], a);
  if (Number(inp.diff_lines || 0) > THRESHOLDS.diff.max_lines) return out("ESCALATE", ["diff_too_wide"], a);
  if (inp.previous_version_available === false) return out("ESCALATE", ["previous_version_missing"], a);
  // 6) budget
  if (Number(b.publishes_used || 0) >= Number(b.publishes_cap || THRESHOLDS.budgets.publishes_per_day)) return out("ESCALATE", ["over_budget"], a, "publishes");
  if (Number(b.tokens_used || 0) >= Number(b.tokens_cap || THRESHOLDS.budgets.tokens_per_change)) return out("ESCALATE", ["over_budget"], a, "tokens");
  // 7) default
  if (PUBLISHABLE.includes(m)) {
    const reasons = [m];
    if (inp.seed) reasons.push("seeded_rehearsal");
    return out("PUBLISH", reasons, a, "lesson " + (inp.lesson_touched || "?"));
  }
  return out("ESCALATE", ["unknown_state"], a, "unhandled materiality " + m);
}

function decideLearner(inp) {
  const a = inp.authority;
  if (inp.freeze_active) return out("NO_CHANGE", ["freeze_active"], a);
  if (inp.grade_impacting) return out("ESCALATE", ["grade_impacting_requires_human"], a);
  if (!inp.consent) return out("NO_CHANGE", ["consent_missing"], a);
  const caps = inp.caps || {};
  if (Number(caps.notifications_today || 0) >= THRESHOLDS.budgets.notify_per_learner_day) return out("NO_CHANGE", ["rate_limited"], a, "day cap");
  if (Number(caps.notifications_week || 0) >= THRESHOLDS.budgets.notify_per_learner_week) return out("NO_CHANGE", ["rate_limited"], a, "week cap");
  if (inp.stuck && inp.concept_recently_dispatched) return out("NO_CHANGE", ["rate_limited"], a, "concept cap: " + (inp.concept || ""));
  if (inp.stuck) return out("DISPATCH", ["stuck_signals_met"], a, inp.concept || "");
  return out("NO_CHANGE", ["no_signal"], a);
}

function decideRevert(inp) {
  const a = inp.authority;
  if (inp.freeze_active) return out("NO_CHANGE", ["freeze_active"], a);
  if (!inp.revert_gate_present) return out("ESCALATE", ["revert_gate_absent"], a);
  if (inp.previous_version_available === false) return out("ESCALATE", ["previous_version_missing"], a);
  const c = inp.cohort || {};
  if (c.n === undefined || c.n === null || c.quiz_delta === undefined || c.quiz_delta === null ||
      c.hours_since_publish === undefined || c.hours_since_publish === null) return out("NO_CHANGE", ["measurement_incomplete"], a);
  if (Number(c.n) < THRESHOLDS.revert.n_min) return out("NO_CHANGE", ["cohort_below_minimum"], a, "n=" + c.n);
  if (Number(c.hours_since_publish) < THRESHOLDS.revert.window_h) return out("NO_CHANGE", ["gate_window_open"], a);
  if (Number(c.quiz_delta) <= 0) return out("REVERT", ["revert_gate_satisfied"], a);
  return out("NO_CHANGE", ["no_improvement_measured"], a);
}

function decide(inp) {
  const bad = malformed(inp);
  if (bad) {
    const authority = AUTHORITIES.includes(inp.authority) ? inp.authority : "PA0";
    return out("ESCALATE", ["unknown_state"], authority, "invalid:" + bad);
  }
  if (inp.stream === "change") return decideChange(inp);
  if (inp.stream === "learner") return decideLearner(inp);
  return decideRevert(inp);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { decide, THRESHOLDS, MATERIALITIES, PUBLISHABLE };
}

// n8n runtime: read the input and emit one item per decision
if (typeof $input !== "undefined" && typeof module === "undefined") {
  return $input.all().map((item) => ({ json: { decision: decide(item.json.input), input_hash: item.json.input_hash } }));
}
