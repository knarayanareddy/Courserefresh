import { useState, useEffect, useRef, useMemo, useCallback } from "react";
import StatusBadge from "./StatusBadge";

// n8n workflow data
const WORKFLOWS = [
  {
    id: "wf-cr-showcase-loop",
    name: "wf-cr-showcase-loop",
    label: "CR Showcase — the whole loop on one canvas",
    trigger: "Webhook: POST /webhook/showcase/cr/loop (or Test workflow)",
    description: "Every phase of Courserefresh — notice, verify, decide, act, learn, report — compressed onto a single 56-node n8n canvas, sticky-notes narrating each lane. Five seeded scenarios traverse the whole loop in one ~10s run: a two-voice change is PUBLISHED and committed to GitHub, a one-voice claim is refused for corroboration, a prompt-injection source is refused by rule R2, a falling cohort quiz trips the revert gate, and a stuck learner gets a consented micro-lesson. Models propose; the deterministic POLICY rulebook decides; the receipt chain is verified before the digest ships.",
    color: "#9B2C1F",
    nodes: [
      { id: "s0",  label: "DEMO IN", type: "trigger", desc: "Webhook /webhook/showcase/cr/loop or the Test-workflow button", x: 60, y: 300 },
      { id: "s1",  label: "SCENARIOS A–E", type: "code", desc: "Seeds 5 demo events: two-voice change · one-voice claim · injected source · falling cohort · stuck learner", x: 290, y: 300 },
      { id: "s2",  label: "LEARN INTAKE", type: "code", desc: "Scenarios D+E: hashed, consent-flagged learner telemetry", x: 520, y: 120 },
      { id: "s3",  label: "REVERT GATE", type: "policy", desc: "quiz_delta −0.12 at n=7 crosses the threshold → REVERT", x: 750, y: 120 },
      { id: "s4",  label: "MICRO-LESSON", type: "notify", desc: "1 concept · ≤2 min · 1 practice · opt-out (stuck learner E)", x: 980, y: 120 },
      { id: "s5",  label: "LEARN RECEIPTS", type: "receipt", desc: "Cohort + dispatch receipts, chained into run-log", x: 1210, y: 120 },
      { id: "s6",  label: "SCAN SOURCES", type: "apify", desc: "Apify actors fetch declared sources; hash + dedupe", x: 520, y: 300 },
      { id: "s7",  label: "SANITIZE", type: "code", desc: "Injection patterns stripped before any model call (R2)", x: 750, y: 300 },
      { id: "s8",  label: "OBSERVE (LLM)", type: "llm", desc: "gpt-oss-120b extracts claims with verbatim quotes", x: 980, y: 300 },
      { id: "s9",  label: "ANCHOR QUOTES", type: "code", desc: "Claim dropped unless it quotes the cached snapshot", x: 1210, y: 300 },
      { id: "s10", label: "JUDGE (LLM)", type: "llm", desc: "Closed questions: novelty · materiality · independence", x: 1440, y: 300 },
      { id: "s11", label: "POLICY", type: "policy", desc: "9.1KB production rulebook — R1–R9 ladder, deterministic, no network", x: 1670, y: 300 },
      { id: "s12", label: "ESCALATE SINK", type: "receipt", desc: "Refusal receipts (B: insufficient corroboration · C: injection R2)", x: 1900, y: 140 },
      { id: "s13", label: "PUBLISH OR REVERT?", type: "branch", desc: "Router: act lane vs escalate/none", x: 1900, y: 460 },
      { id: "s14", label: "GH SHA+COMMIT", type: "git", desc: "Look up blob sha → commit body + diff to main (showcase/)", x: 2130, y: 460 },
      { id: "s15", label: "LEARNER CARD", type: "notify", desc: "Telegram card to consented cohort (PA2 caps respected)", x: 2360, y: 460 },
      { id: "s16", label: "LANES MERGE", type: "branch", desc: "Appends every lane's receipts into one item set", x: 2360, y: 300 },
      { id: "s17", label: "DIGEST RENDER", type: "code", desc: "≤4KB: refusals first → changes → learners → discipline strip", x: 2130, y: 620 },
      { id: "s18", label: "VERIFY CHAIN", type: "code", desc: "Recompute row hashes + chain.prev links → chain_ok", x: 1900, y: 620 },
      { id: "s19", label: "TELEGRAM DIGEST", type: "notify", desc: "Digest to author's channel", x: 1670, y: 620 },
      { id: "s20", label: "RESULTS", type: "http", desc: "Webhook response: per-lane outcomes + chain_ok flag", x: 1440, y: 620 },
    ],
    edges: [
      { from: "s0", to: "s1" },
      { from: "s1", to: "s2" }, { from: "s1", to: "s6" },
      { from: "s2", to: "s3" }, { from: "s3", to: "s4" }, { from: "s4", to: "s5" },
      { from: "s6", to: "s7" }, { from: "s7", to: "s8" }, { from: "s8", to: "s9" },
      { from: "s9", to: "s10" }, { from: "s10", to: "s11" },
      { from: "s11", to: "s12" }, { from: "s11", to: "s13" },
      { from: "s13", to: "s14" }, { from: "s14", to: "s15" },
      { from: "s12", to: "s16" }, { from: "s5", to: "s16" }, { from: "s15", to: "s16" },
      { from: "s16", to: "s17" }, { from: "s17", to: "s18" },
      { from: "s18", to: "s19" }, { from: "s18", to: "s20" },
    ],
    writes: ["showcase/ (GitHub commits)", "receipts/run-log.jsonl", "Telegram cards + digest"],
    n8nUrl: "https://knreddy.app.n8n.cloud/workflow/1dGrPQ8j4M8u2lXU",
  },
  {
    id: "wf-cr-0-scan",
    name: "wf-cr-0-scan",
    label: "Source Scanner",
    trigger: "Schedule: every 60 min + manual webhook",
    description: "Fetches declared sources via Apify actors, hashes snapshots, deduplicates, and forwards new events to triage.",
    color: "#3F5A2A",
    nodes: [
      { id: "n0", label: "THRESHOLDS", type: "config", desc: "Imports injection=0.65, corroboration_min=2, confidence_floor=0.72", x: 60, y: 80 },
      { id: "n1", label: "Schedule", type: "trigger", desc: "60-min cadence or manual webhook", x: 60, y: 200 },
      { id: "n2", label: "Apify: n8n-docs", type: "apify", desc: "website-content-crawler@1.11.0 → n8n release notes", x: 280, y: 140 },
      { id: "n3", label: "Apify: apify-changelog", type: "apify", desc: "website-content-crawler@1.11.0 → Apify changelog", x: 280, y: 260 },
      { id: "n4", label: "Normalize", type: "code", desc: "Extracts url, text, capturedAt; computes content_hash=sha256(text)", x: 500, y: 200 },
      { id: "n5", label: "Dedupe", type: "code", desc: "Compares hash against seen.json; skips duplicates; writes new hashes", x: 700, y: 200 },
      { id: "n6", label: "HTTP → Triage", type: "http", desc: "POSTs SourceSnapshot[] to wf-cr-1-triage webhook", x: 900, y: 200 },
      { id: "n7", label: "Receipt", type: "receipt", desc: "Writes run receipt with snapshot_count, hash list, mode", x: 900, y: 340 },
    ],
    edges: [
      { from: "n1", to: "n2" }, { from: "n1", to: "n3" },
      { from: "n2", to: "n4" }, { from: "n3", to: "n4" },
      { from: "n4", to: "n5" }, { from: "n5", to: "n6" },
      { from: "n5", to: "n7" }, { from: "n6", to: "n7" },
    ],
    writes: ["snapshots/", "receipts/run-log.jsonl"],
    n8nUrl: "https://knreddy.app.n8n.cloud/workflow/8obP1OOXAzK24kfa",
  },
  {
    id: "wf-cr-1-triage",
    name: "wf-cr-1-triage",
    label: "Triage & Decision",
    trigger: "Webhook from wf-cr-0-scan",
    description: "The heart of Courserefresh. Extracts claims, verifies sources, runs the POLICY node, and branches to act or escalate.",
    color: "#96550A",
    nodes: [
      { id: "n0", label: "Webhook", type: "trigger", desc: "Receives SourceSnapshot[] from scan workflow", x: 60, y: 200 },
      { id: "n1", label: "BuildPrompt", type: "code", desc: "Structures snapshot into OBSERVE prompt with closed questions", x: 260, y: 200 },
      { id: "n2", label: "OBSERVE", type: "llm", desc: "gpt-4o-mini: fast claim extraction with verbatim quote anchoring", x: 460, y: 140 },
      { id: "n3", label: "AnchorQuotes", type: "code", desc: "Verifies each claim has a verbatim quote in the cached snapshot", x: 660, y: 140 },
      { id: "n4", label: "JUDGE", type: "llm", desc: "gpt-4o: answers closed Qs — novelty, materiality, independence", x: 460, y: 280 },
      { id: "n5", label: "POLICY", type: "policy", desc: "Deterministic code: R1–R9 rule ladder → action + reason codes. No network calls.", x: 860, y: 200 },
      { id: "n6", label: "Receipt", type: "receipt", desc: "Writes decision receipt with sources[], claims[], judge answers, chain.prev", x: 1060, y: 140 },
      { id: "n7", label: "Branch: ACT", type: "branch", desc: "PUBLISH/REVERT → wf-cr-2-act", x: 1060, y: 260 },
      { id: "n8", label: "Branch: ESCALATE", type: "branch", desc: "Insufficient evidence → escalation queue + digest", x: 1060, y: 360 },
    ],
    edges: [
      { from: "n0", to: "n1" }, { from: "n1", to: "n2" }, { from: "n1", to: "n4" },
      { from: "n2", to: "n3" }, { from: "n3", to: "n5" }, { from: "n4", to: "n5" },
      { from: "n5", to: "n6" }, { from: "n5", to: "n7" }, { from: "n5", to: "n8" },
    ],
    writes: ["receipts/run-log.jsonl", "escalation-queue.jsonl"],
    n8nUrl: "https://knreddy.app.n8n.cloud/workflow/XafXKTwrLXr6dkmR",
  },
  {
    id: "wf-cr-2-act",
    name: "wf-cr-2-act",
    label: "Act & Publish",
    trigger: "Webhook for approved PUBLISH/REVERT decisions",
    description: "Renders the updated lesson body, generates the diff, updates the quiz, commits to the bot branch, and sends the learner card.",
    color: "#3F5A2A",
    nodes: [
      { id: "n0", label: "Webhook", type: "trigger", desc: "Receives approved DecisionResult from triage", x: 60, y: 200 },
      { id: "n1", label: "RenderBody", type: "code", desc: "Applies amendments to lesson body; increments version", x: 260, y: 200 },
      { id: "n2", label: "RenderDiff", type: "code", desc: "Generates unified diff (−/+ format) between vN and vN+1", x: 460, y: 140 },
      { id: "n3", label: "UpdateQuiz?", type: "branch", desc: "If claim touches a quiz item → regenerate that item only", x: 460, y: 280 },
      { id: "n4", label: "GitCommit", type: "git", desc: "Commits course/**, diffs/, CHANGELOG.md on bot/courserefresh branch", x: 660, y: 200 },
      { id: "n5", label: "CardEmail", type: "notify", desc: "Sends learner card to consented cohort (PA2 only); respects caps", x: 860, y: 140 },
      { id: "n6", label: "Receipt", type: "receipt", desc: "Writes publish receipt with before_hash, after_hash, diff_hash, revert_gate", x: 860, y: 280 },
    ],
    edges: [
      { from: "n0", to: "n1" }, { from: "n1", to: "n2" }, { from: "n1", to: "n3" },
      { from: "n2", to: "n4" }, { from: "n3", to: "n4" },
      { from: "n4", to: "n5" }, { from: "n4", to: "n6" },
    ],
    writes: ["course/**", "diffs/", "CHANGELOG.md", "receipts/", "cards/"],
    n8nUrl: "https://knreddy.app.n8n.cloud/workflow/IAqTyjFD5AnUdyGU",
  },
  {
    id: "wf-cr-3-learn",
    name: "wf-cr-3-learn",
    label: "Learn & Revert",
    trigger: "Schedule: every 15 min",
    description: "Reads telemetry, evaluates cohort windows, triggers reverts when gates are satisfied, and dispatches micro-lessons to stuck learners.",
    color: "#7A5C00",
    nodes: [
      { id: "n0", label: "Schedule: 15min", type: "trigger", desc: "Runs every 15 minutes to evaluate learner state", x: 60, y: 200 },
      { id: "n1", label: "ReadTelemetry", type: "db", desc: "Reads hashed telemetry rows from SQLite (14-day retention)", x: 260, y: 200 },
      { id: "n2", label: "CohortWindow", type: "code", desc: "Computes 48h cohort window per recent publish", x: 460, y: 140 },
      { id: "n3", label: "GateEval", type: "code", desc: "Evaluates quiz_delta; n < cohort_min → unmeasured", x: 460, y: 260 },
      { id: "n4", label: "DecideRevert", type: "policy", desc: "gate=satisfied → REVERT; gate=passed → NO_CHANGE", x: 660, y: 200 },
      { id: "n5", label: "StuckCheck", type: "code", desc: "consecutive_wrong ≥ 2 or dwell ≥ 3× median → stuck=true", x: 660, y: 340 },
      { id: "n6", label: "DecideLearner", type: "policy", desc: "stuck+consent+cap → dispatch; no consent → NO_CHANGE(consent_missing)", x: 860, y: 340 },
      { id: "n7", label: "Dispatch", type: "notify", desc: "Sends micro-lesson (1 concept, ≤2 min, 1 practice, opt-out)", x: 1060, y: 340 },
      { id: "n8", label: "Receipt", type: "receipt", desc: "Writes cohort receipt; gate_state; unmeasured if n < floor", x: 1060, y: 200 },
    ],
    edges: [
      { from: "n0", to: "n1" }, { from: "n1", to: "n2" }, { from: "n1", to: "n3" },
      { from: "n2", to: "n4" }, { from: "n3", to: "n4" }, { from: "n4", to: "n8" },
      { from: "n1", to: "n5" }, { from: "n5", to: "n6" }, { from: "n6", to: "n7" },
      { from: "n7", to: "n8" },
    ],
    writes: ["micro-lessons/", "dispatch-receipts/", "cohort-gates.jsonl"],
    n8nUrl: "https://knreddy.app.n8n.cloud/workflow/R9Gkmv5arcHrJ36x",
  },
  {
    id: "wf-cr-4-digest",
    name: "wf-cr-4-digest",
    label: "Digest & Report",
    trigger: "Schedule: 07:30 UTC + on-demand webhook",
    description: "Renders the morning digest from receipts only (≤4KB), sends via Telegram/email, and verifies the receipt chain.",
    color: "#5C564C",
    nodes: [
      { id: "n0", label: "Schedule: 07:30", type: "trigger", desc: "Fires at 07:30 UTC daily, or on-demand via webhook", x: 60, y: 200 },
      { id: "n1", label: "ReadReceipts", type: "db", desc: "Reads all receipts in the digest window from run-log.jsonl", x: 260, y: 200 },
      { id: "n2", label: "OrderSections", type: "code", desc: "Refusals first → changes → learner panel → discipline strip", x: 460, y: 200 },
      { id: "n3", label: "RenderText", type: "code", desc: "Renders ≤4096 bytes; trims oldest sections (never refusals)", x: 660, y: 200 },
      { id: "n4", label: "VerifyChain", type: "code", desc: "verify_chain(): recomputes hashes, checks chain.prev links", x: 660, y: 340 },
      { id: "n5", label: "Send: Telegram", type: "notify", desc: "Posts digest to author's Telegram channel", x: 860, y: 140 },
      { id: "n6", label: "Send: Email", type: "notify", desc: "Sends digest to author's email (fallback)", x: 860, y: 260 },
      { id: "n7", label: "Receipt", type: "receipt", desc: "Writes digest receipt; flags DIGEST FAILED if chain broken", x: 1060, y: 200 },
    ],
    edges: [
      { from: "n0", to: "n1" }, { from: "n1", to: "n2" }, { from: "n2", to: "n3" },
      { from: "n3", to: "n4" }, { from: "n3", to: "n5" }, { from: "n3", to: "n6" },
      { from: "n4", to: "n7" }, { from: "n5", to: "n7" }, { from: "n6", to: "n7" },
    ],
    writes: ["digest.txt", "digest.html", "run-log.jsonl"],
    n8nUrl: "https://knreddy.app.n8n.cloud/workflow/8obP1OOXAzK24kfa",
  },
];

const NODE_COLORS: Record<string, { bg: string; border: string; label: string }> = {
  trigger:  { bg: "rgba(63,90,42,0.12)",  border: "#3F5A2A", label: "TRIGGER" },
  apify:    { bg: "rgba(150,85,10,0.12)", border: "#96550A", label: "APIFY" },
  llm:      { bg: "rgba(107,78,46,0.12)", border: "#6B4E2E", label: "LLM" },
  code:     { bg: "rgba(92,86,76,0.10)",  border: "#5C564C", label: "CODE" },
  policy:   { bg: "rgba(155,44,31,0.12)", border: "#9B2C1F", label: "POLICY" },
  http:     { bg: "rgba(122,92,0,0.10)",  border: "#7A5C00", label: "HTTP" },
  receipt:  { bg: "rgba(28,25,21,0.06)",  border: "#1C1915", label: "RECEIPT" },
  branch:   { bg: "rgba(63,90,42,0.08)",  border: "#3F5A2A", label: "BRANCH" },
  git:      { bg: "rgba(107,78,46,0.10)", border: "#6B4E2E", label: "GIT" },
  notify:   { bg: "rgba(63,90,42,0.10)",  border: "#3F5A2A", label: "NOTIFY" },
  db:       { bg: "rgba(92,86,76,0.08)",  border: "#5C564C", label: "DB" },
  config:   { bg: "rgba(28,25,21,0.05)",  border: "#8E8160", label: "CONFIG" },
};

function WorkflowCanvas({ wf }: { wf: typeof WORKFLOWS[0] }) {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // ---- magpie-style execution replay -----------------------------------
  // Nodes animate in topological waves: a wave fires once every predecessor
  // is done — the same way n8n executes parallel branches. Borrowed from the
  // magpie1 WorkflowView replay (pulsing running node, flowing edge packets).
  const ranks = useMemo(() => {
    const indeg: Record<string, number> = {};
    const out: Record<string, string[]> = {};
    wf.nodes.forEach(n => { indeg[n.id] = 0; out[n.id] = []; });
    wf.edges.forEach(e => { if (indeg[e.to] !== undefined && out[e.from] !== undefined) { indeg[e.to]++; out[e.from].push(e.to); } });
    const rank: Record<string, number> = {};
    const rem = { ...indeg };
    let frontier = wf.nodes.filter(n => rem[n.id] === 0).map(n => n.id);
    let r = 0;
    while (frontier.length) {
      const next: string[] = [];
      frontier.forEach(id => {
        rank[id] = r;
        (out[id] || []).forEach(t => { if (rem[t] !== undefined) { rem[t]--; if (rem[t] === 0) next.push(t); } });
      });
      frontier = next;
      r++;
    }
    wf.nodes.forEach(n => { if (rank[n.id] === undefined) rank[n.id] = r; });
    return rank;
  }, [wf.id]);

  const maxRankV = useMemo(() => Math.max(-1, ...wf.nodes.map(n => ranks[n.id] ?? 0)), [wf.id, ranks]);
  const stepMs = wf.id === "wf-cr-showcase-loop" ? 420 : 600;

  const [animStep, setAnimStep] = useState(-1);
  const [playing, setPlaying] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const autoPlayedRef = useRef(false);

  const stopAnim = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setPlaying(false);
  }, []);

  const runAnim = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setAnimStep(0);
    setPlaying(true);
    let step = 0;
    timerRef.current = setInterval(() => {
      step++;
      setAnimStep(step);
      if (step >= maxRankV + 1) {
        if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
        setPlaying(false);
      }
    }, stepMs);
  }, [maxRankV, stepMs]);

  // reset on workflow switch; auto-play the combined showcase once on load
  useEffect(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setPlaying(false);
    setAnimStep(-1);
    if (wf.id === "wf-cr-showcase-loop" && !autoPlayedRef.current) {
      autoPlayedRef.current = true;
      runAnim();
    }
  }, [wf.id, runAnim]);

  useEffect(() => () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  }, []);

  const animStatus = (id: string): "idle" | "running" | "done" | null => {
    if (animStep < 0) return null;
    const r = ranks[id] ?? 0;
    if (r < animStep) return "done";
    if (r === animStep) return "running";
    return "idle";
  };

  const edgeState = (a: string, b: string): "static" | "active" | "future" => {
    if (animStep < 0) return "static";
    const ra = ranks[a] ?? 0;
    const rb = ranks[b] ?? 0;
    if (ra < animStep && rb <= animStep) return "active";
    return "future";
  };
  // -----------------------------------------------------------------------

  const minX = Math.min(...wf.nodes.map(n => n.x));
  const maxX = Math.max(...wf.nodes.map(n => n.x)) + 180;
  const minY = Math.min(...wf.nodes.map(n => n.y));
  const maxY = Math.max(...wf.nodes.map(n => n.y)) + 80;
  const svgW = maxX - minX + 40;
  const svgH = maxY - minY + 40;

  const nodeById = Object.fromEntries(wf.nodes.map(n => [n.id, n]));
  const nodeW = 160;
  const nodeH = 60;

  return (
    <div style={{ position: "relative" }}>
      {/* magpie-style replay controls */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: "var(--s3)" }}>
        <button
          onClick={playing ? stopAnim : runAnim}
          style={{
            padding: "4px 12px",
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            backgroundColor: playing ? "#8E8160" : "var(--ink)",
            color: "var(--paper)",
            border: "none",
            borderRadius: "var(--radius)",
            cursor: playing ? "wait" : "pointer",
          }}
        >
          {playing ? `▶ replaying… wave ${Math.min(animStep, maxRankV + 1)}/${maxRankV + 1}` : "▶ replay flow"}
        </button>
        {animStep >= 0 && !playing && (
          <button
            onClick={() => setAnimStep(-1)}
            style={{
              padding: "4px 12px",
              fontFamily: "var(--font-mono)",
              fontSize: 12,
              backgroundColor: "var(--paper-2)",
              color: "var(--ink-soft)",
              border: "1px solid var(--rule)",
              borderRadius: "var(--radius)",
              cursor: "pointer",
            }}
          >
            ↺ reset
          </button>
        )}
        <span style={{ fontSize: 11, fontFamily: "var(--font-sans)", color: "var(--ink-faint)" }}>
          {animStep < 0
            ? "a wave = every node whose predecessors finished — n8n runs parallel branches that way"
            : playing
              ? "running nodes pulse · executed wires carry flow packets"
              : "flow complete — every lane executed, packets keep flowing"}
        </span>
      </div>
      <svg
        width="100%"
        viewBox={`${minX - 20} ${minY - 20} ${svgW} ${svgH}`}
        style={{ overflow: "visible", display: "block" }}
      >
        {/* Edges — animated during replay: executed wires go solid and carry flow packets (magpie-style) */}
        {wf.edges.map((edge, i) => {
          const from = nodeById[edge.from];
          const to = nodeById[edge.to];
          if (!from || !to) return null;
          const x1 = from.x + nodeW;
          const y1 = from.y + nodeH / 2;
          const x2 = to.x;
          const y2 = to.y + nodeH / 2;
          const mx = (x1 + x2) / 2;
          const d = `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`;
          const st = edgeState(edge.from, edge.to);
          if (st === "active") {
            return (
              <g key={i}>
                <path d={d} stroke={wf.color} strokeWidth={2} fill="none" strokeOpacity={0.9} />
                <circle r={3} fill={wf.color}>
                  <animateMotion dur="1.4s" repeatCount="indefinite" path={d} />
                </circle>
              </g>
            );
          }
          if (st === "future") {
            return (
              <path key={i} d={d} stroke="#C9C2B4" strokeWidth={1} fill="none" strokeDasharray="4 4" strokeOpacity={0.55} />
            );
          }
          return (
            <path key={i} d={d} stroke={wf.color} strokeWidth={1.5} fill="none" strokeOpacity={0.4} markerEnd="url(#arrow)" />
          );
        })}
        {/* Arrow marker */}
        <defs>
          <marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
            <path d="M0,0 L0,6 L6,3 z" fill={wf.color} fillOpacity={0.5} />
          </marker>
        </defs>

        {/* Nodes (as foreignObject for HTML rendering) */}
        {wf.nodes.map(node => {
          const nc = NODE_COLORS[node.type] ?? NODE_COLORS.code;
          const isHovered = hoveredNode === node.id;
          const a = animStatus(node.id);
          return (
            <g key={node.id}>
              {a === "running" && (
                <rect x={node.x - 3} y={node.y - 3} width={nodeW + 6} height={nodeH + 6} fill="none" stroke="#D4A017" strokeWidth={2} rx={3} opacity={0.6}>
                  <animate attributeName="opacity" values="0.6;0.15;0.6" dur="0.8s" repeatCount="indefinite" />
                </rect>
              )}
              <foreignObject
                x={node.x}
                y={node.y}
                width={nodeW}
                height={nodeH}
                style={{ overflow: "visible" }}
              >
                <div
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  style={{
                    position: "relative",
                    width: nodeW,
                    height: nodeH,
                    background: a === "running" ? "rgba(212,160,23,0.16)" : a === "done" ? `${nc.border}22` : nc.bg,
                    border: `1px solid ${a === "running" ? "#B8860B" : nc.border}`,
                    borderRadius: 2,
                    padding: "8px 10px",
                    cursor: "pointer",
                    opacity: a === "idle" ? 0.45 : 1,
                    boxShadow: isHovered ? `0 0 0 2px ${nc.border}40` : "none",
                    transition: "box-shadow 0.15s, background 0.3s, opacity 0.3s",
                  }}
                >
                  <div style={{ fontSize: 9, letterSpacing: "0.06em", textTransform: "uppercase", color: nc.border, fontFamily: "var(--font-sans)", marginBottom: 3 }}>
                    {nc.label}
                  </div>
                  <div style={{ fontSize: 11, fontWeight: 600, fontFamily: "var(--font-mono)", color: "var(--ink)", lineHeight: 1.3 }}>
                    {a === "done" && <span style={{ float: "right", color: "#2D6A2D", fontSize: 10, fontWeight: 700 }}>✓</span>}
                    {a === "running" && <span style={{ float: "right", color: "#B8860B", fontSize: 10, fontWeight: 700 }}>▶</span>}
                    {node.label}
                  </div>
                </div>
              </foreignObject>
            </g>
          );
        })}
      </svg>

      {/* Tooltip */}
      {hoveredNode && (
        <div style={{
          position: "absolute",
          bottom: 8,
          left: 0,
          right: 0,
          background: "var(--paper-2)",
          border: "1px solid var(--rule)",
          borderRadius: "var(--radius)",
          padding: "var(--s3) var(--s4)",
          fontSize: 12,
          color: "var(--ink-soft)",
          fontFamily: "var(--font-sans)",
          zIndex: 10,
        }}>
          <strong style={{ color: "var(--ink)", fontFamily: "var(--font-mono)" }}>
            {wf.nodes.find(n => n.id === hoveredNode)?.label}:
          </strong>{" "}
          {wf.nodes.find(n => n.id === hoveredNode)?.desc}
        </div>
      )}
    </div>
  );
}

// Full loop diagram showing all 5 workflows connected
function FullLoopDiagram() {
  const phases = [
    { label: "NOTICE", wf: "wf-cr-0-scan", desc: "Apify actors fetch sources", color: "#3F5A2A", icon: "⟳" },
    { label: "VERIFY", wf: "wf-cr-1-triage", desc: "OBSERVE + JUDGE + POLICY", color: "#96550A", icon: "⚖" },
    { label: "ACT", wf: "wf-cr-2-act", desc: "Publish / revert the course", color: "#3F5A2A", icon: "✓" },
    { label: "LEARN", wf: "wf-cr-3-learn", desc: "Gate eval + micro-lessons", color: "#7A5C00", icon: "◎" },
    { label: "REPORT", wf: "wf-cr-4-digest", desc: "Morning digest · 07:30 UTC", color: "#5C564C", icon: "≡" },
  ];

  return (
    <div style={{ position: "relative", padding: "var(--s5) 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 0, flexWrap: "wrap", justifyContent: "center" }}>
        {phases.map((phase, i) => (
          <div key={phase.label} style={{ display: "flex", alignItems: "center" }}>
            <div style={{
              background: "var(--paper-2)",
              border: `1px solid ${phase.color}`,
              borderRadius: "var(--radius)",
              padding: "var(--s3) var(--s5)",
              textAlign: "center",
              minWidth: 140,
            }}>
              <div style={{ fontSize: 20, marginBottom: 4 }}>{phase.icon}</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: phase.color, fontFamily: "var(--font-sans)", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                {phase.label}
              </div>
              <div style={{ fontSize: 11, color: "var(--ink-faint)", fontFamily: "var(--font-mono)", marginTop: 3 }}>
                {phase.wf}
              </div>
              <div style={{ fontSize: 11, color: "var(--ink-soft)", fontFamily: "var(--font-sans)", marginTop: 3 }}>
                {phase.desc}
              </div>
            </div>
            {i < phases.length - 1 && (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", padding: "0 8px" }}>
                <svg width="40" height="24" viewBox="0 0 40 24">
                  <path d="M 4 12 L 36 12" stroke="var(--rule)" strokeWidth={1.5} />
                  <path d="M 28 6 L 36 12 L 28 18" stroke="var(--rule)" strokeWidth={1.5} fill="none" />
                </svg>
              </div>
            )}
          </div>
        ))}
        {/* Back arrow */}
        <div style={{ width: "100%", display: "flex", justifyContent: "center", marginTop: "var(--s3)" }}>
          <div style={{ fontSize: 11, color: "var(--ink-faint)", fontFamily: "var(--font-mono)" }}>
            ↳ loop repeats every 60 min · receipts chained · chain verified at digest · the whole loop also runs on one combined canvas → wf-cr-showcase-loop
          </div>
        </div>
      </div>
    </div>
  );
}

export default function WorkflowTab({ data }: { data: any }) {
  const [selectedWf, setSelectedWf] = useState(0);
  const wf = WORKFLOWS[selectedWf];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--s5)" }}>
      <div style={{ borderBottom: "1px solid var(--rule)", paddingBottom: "var(--s4)" }}>
        <h2 style={{ margin: 0, fontSize: 20, fontFamily: "var(--font-serif)", fontWeight: 600, color: "var(--ink)", marginBottom: 6 }}>
          n8n Workflow Visualisations
        </h2>
        <p style={{ margin: 0, fontSize: 13, color: "var(--ink-soft)", fontStyle: "italic", fontFamily: "var(--font-serif)" }}>
          Five production workflows orchestrate the notice → verify → decide → act → learn → report loop — plus a sixth, wf-cr-showcase-loop, which runs the entire loop end-to-end on a single canvas for the demo. Every decision executes inside n8n; the canvas is the accountability surface.
        </p>
      </div>

      {/* Full loop overview */}
      <div style={{ background: "var(--paper-2)", border: "1px solid var(--rule)", borderRadius: "var(--radius)", padding: "var(--s5)" }}>
        <div style={{ fontSize: 12, fontFamily: "var(--font-sans)", fontWeight: 500, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--ink-faint)", marginBottom: "var(--s4)" }}>
          The Full Loop — One Picture
        </div>
        <FullLoopDiagram />
      </div>

      {/* Workflow selector */}
      <div style={{ display: "flex", gap: "var(--s2)", flexWrap: "wrap" }}>
        {WORKFLOWS.map((w, i) => (
          <button
            key={w.id}
            onClick={() => setSelectedWf(i)}
            style={{
              padding: "var(--s2) var(--s4)",
              borderRadius: "var(--radius)",
              border: selectedWf === i ? `1px solid ${w.color}` : "1px solid var(--rule)",
              background: selectedWf === i ? `${w.color}18` : "var(--paper-2)",
              cursor: "pointer",
              fontSize: 12,
              fontFamily: "var(--font-mono)",
              color: selectedWf === i ? w.color : "var(--ink-soft)",
              fontWeight: selectedWf === i ? 600 : 400,
            }}
          >
            {w.name}
          </button>
        ))}
      </div>

      {/* Workflow detail */}
      <div style={{ border: "1px solid var(--rule)", borderRadius: "var(--radius)", overflow: "hidden" }}>
        {/* Header */}
        <div style={{ background: "var(--paper-2)", borderBottom: "1px solid var(--rule)", padding: "var(--s4) var(--s5)" }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "var(--s4)" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                <span style={{ fontSize: 16, fontFamily: "var(--font-mono)", fontWeight: 600, color: wf.color }}>{wf.name}</span>
                <span style={{ fontSize: 12, color: "var(--ink-soft)", fontFamily: "var(--font-sans)", fontStyle: "italic" }}>{wf.label}</span>
              </div>
              <div style={{ fontSize: 13, color: "var(--ink-soft)", fontFamily: "var(--font-sans)", lineHeight: 1.5 }}>
                {wf.description}
              </div>
              <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
                <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--ink-faint)" }}>
                  Trigger: {wf.trigger}
                </span>
                <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--ink-faint)" }}>
                  Writes: {wf.writes.join(", ")}
                </span>
              </div>
            </div>
            <a
              href={wf.n8nUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: 12,
                padding: "var(--s2) var(--s4)",
                border: `1px solid ${wf.color}`,
                borderRadius: "var(--radius)",
                color: wf.color,
                textDecoration: "none",
                fontFamily: "var(--font-sans)",
                whiteSpace: "nowrap",
                fontWeight: 500,
              }}
            >
              Open in n8n ↗
            </a>
          </div>
        </div>

        {/* Canvas */}
        <div style={{ padding: "var(--s5)", background: "var(--paper)", overflowX: "auto" }}>
          <div style={{ fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--ink-faint)", fontFamily: "var(--font-sans)", marginBottom: "var(--s4)" }}>
            Canvas — hover nodes for detail
          </div>
          <div style={{ minWidth: wf.id === "wf-cr-showcase-loop" ? 1800 : 900 }}>
            <WorkflowCanvas wf={wf} />
          </div>
        </div>

        {/* Node legend */}
        <div style={{ borderTop: "1px solid var(--rule)", padding: "var(--s4) var(--s5)", background: "var(--paper-2)" }}>
          <div style={{ fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--ink-faint)", fontFamily: "var(--font-sans)", marginBottom: "var(--s3)" }}>
            Node Type Legend
          </div>
          <div style={{ display: "flex", gap: "var(--s4)", flexWrap: "wrap" }}>
            {Object.entries(NODE_COLORS).map(([type, nc]) => (
              <div key={type} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span style={{ display: "inline-block", width: 10, height: 10, background: nc.bg, border: `1px solid ${nc.border}`, borderRadius: 1 }} />
                <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", color: "var(--ink-soft)" }}>{type}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Nodes table */}
        <div style={{ borderTop: "1px solid var(--rule)", padding: "var(--s4) var(--s5)" }}>
          <div style={{ fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--ink-faint)", fontFamily: "var(--font-sans)", marginBottom: "var(--s3)" }}>
            Nodes — contracts & descriptions
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--s2)" }}>
            {wf.nodes.map(node => {
              const nc = NODE_COLORS[node.type] ?? NODE_COLORS.code;
              return (
                <div key={node.id} style={{
                  display: "grid",
                  gridTemplateColumns: "80px 160px 1fr",
                  gap: "var(--s4)",
                  alignItems: "flex-start",
                  padding: "var(--s2) var(--s3)",
                  background: nc.bg,
                  border: `1px solid ${nc.border}20`,
                  borderRadius: "var(--radius)",
                }}>
                  <span style={{ fontSize: 10, letterSpacing: "0.06em", textTransform: "uppercase", color: nc.border, fontFamily: "var(--font-sans)", paddingTop: 2 }}>
                    {nc.label}
                  </span>
                  <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", fontWeight: 600, color: "var(--ink)" }}>
                    {node.label}
                  </span>
                  <span style={{ fontSize: 12, color: "var(--ink-soft)", fontFamily: "var(--font-sans)", lineHeight: 1.5 }}>
                    {node.desc}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Live workflow run data */}
      {data?.workflowRuns && (
        <div style={{ border: "1px solid var(--rule)", borderRadius: "var(--radius)", overflow: "hidden" }}>
          <div style={{ background: "var(--paper-2)", borderBottom: "1px solid var(--rule)", padding: "var(--s3) var(--s5)" }}>
            <span style={{ fontSize: 13, fontWeight: 500, fontFamily: "var(--font-sans)", color: "var(--ink)" }}>
              Recent Workflow Executions
            </span>
          </div>
          {data.workflowRuns.map((wr: any) => (
            <div key={wr.id} style={{
              display: "grid",
              gridTemplateColumns: "160px 140px 80px 80px 1fr 80px",
              gap: "var(--s4)",
              alignItems: "center",
              padding: "var(--s3) var(--s5)",
              borderBottom: "1px solid var(--rule)",
              fontSize: 12,
            }}>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 600, color: "var(--accent)" }}>{wr.workflowName}</span>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--ink-faint)" }}>{wr.runId}</span>
              <StatusBadge status={wr.status === "success" ? "PUBLISH" : "ESCALATE"} size="sm" />
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--ink-faint)" }}>{wr.durationMs}ms</span>
              <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                {Array.isArray(wr.nodesExecuted) && wr.nodesExecuted.slice(0, 5).map((n: string) => (
                  <span key={n} style={{
                    fontSize: 10, padding: "1px 5px",
                    background: "var(--paper)", border: "1px solid var(--rule)",
                    borderRadius: 1, fontFamily: "var(--font-mono)", color: "var(--ink-soft)",
                  }}>
                    {n}
                  </span>
                ))}
                {Array.isArray(wr.nodesExecuted) && wr.nodesExecuted.length > 5 && (
                  <span style={{ fontSize: 10, color: "var(--ink-faint)" }}>+{wr.nodesExecuted.length - 5}</span>
                )}
              </div>
              <span style={{ fontFamily: "var(--font-mono)", fontSize: 11, color: "var(--ink-faint)" }}>
                {wr.receiptsWritten} receipts
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
