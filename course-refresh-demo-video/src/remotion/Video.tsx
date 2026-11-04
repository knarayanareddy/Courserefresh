import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type { ComponentType, CSSProperties, ReactNode } from "react";
import { NARRATION } from "./narration";
import timing from "./narration-timing.json";

const FPS = 24;
const TOTAL_SECONDS = 180;
const TOTAL_FRAMES = TOTAL_SECONDS * FPS;
const COLORS = {
  ink: "#080b13",
  panel: "rgba(17, 23, 36, .82)",
  line: "rgba(202, 218, 255, .13)",
  white: "#f5f7fc",
  muted: "#8b96aa",
  cyan: "#70e1d4",
  blue: "#87a9ff",
  violet: "#c5a4ff",
  green: "#85e2b4",
  amber: "#f0c27a",
  red: "#ff9296",
};

const easing = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };
const reveal = (frame: number, delay = 0, duration = 20) =>
  interpolate(frame, [delay, delay + duration], [0, 1], easing);
const rise = (frame: number, delay = 0, distance = 30) =>
  interpolate(frame, [delay, delay + 24], [distance, 0], easing);

const label: CSSProperties = {
  color: COLORS.cyan,
  fontSize: 17,
  fontWeight: 700,
  letterSpacing: "0.2em",
  textTransform: "uppercase",
};
const text: CSSProperties = {
  color: COLORS.white,
  fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif",
};
const panel: CSSProperties = {
  background: COLORS.panel,
  border: `1px solid ${COLORS.line}`,
  borderRadius: 26,
  boxShadow: "0 28px 90px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.035)",
  backdropFilter: "blur(18px)",
};

function Wordmark({ small = false }: { small?: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: small ? 11 : 15 }}>
      <div style={{
        width: small ? 31 : 42,
        height: small ? 31 : 42,
        borderRadius: small ? 10 : 13,
        display: "grid",
        placeItems: "center",
        background: "linear-gradient(145deg, #8ff0df, #859cff 72%, #c5a4ff)",
        boxShadow: "0 0 32px rgba(112,225,212,.2)",
      }}>
        <svg width={small ? 19 : 25} height={small ? 19 : 25} viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M5 12.4 9.1 16.5 19.3 6.8" stroke="#101827" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <span style={{ ...text, fontSize: small ? 20 : 26, fontWeight: 650, letterSpacing: "-.035em" }}>courserefresh</span>
    </div>
  );
}

function Chip({ children, color = COLORS.cyan }: { children: ReactNode; color?: string }) {
  return <span style={{
    color,
    border: `1px solid ${color}42`,
    background: `${color}12`,
    borderRadius: 999,
    padding: "10px 15px",
    fontSize: 16,
    fontWeight: 600,
    letterSpacing: ".01em",
    whiteSpace: "nowrap",
  }}>{children}</span>;
}

function Dot({ color = COLORS.green }: { color?: string }) {
  return <span style={{ display: "inline-block", width: 9, height: 9, borderRadius: 99, background: color, boxShadow: `0 0 14px ${color}88` }} />;
}

function Frame({ index, title, kicker, children }: { index: string; title: string; kicker: string; children: ReactNode }) {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const fade = interpolate(frame, [0, 14, durationInFrames - 16, durationInFrames], [0, 1, 1, 0], easing);
  return (
    <AbsoluteFill style={{ opacity: fade, padding: "68px 112px 54px", color: COLORS.white }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", opacity: .88 }}>
        <Wordmark small />
        <div style={{ ...label, color: COLORS.muted, fontSize: 13 }}>{index} <span style={{ color: COLORS.line, padding: "0 8px" }}>/</span> {kicker}</div>
      </div>
      <div style={{ marginTop: 74, ...label }}>{kicker}</div>
      <h2 style={{ ...text, fontSize: 72, fontWeight: 560, lineHeight: 1.07, letterSpacing: "-.055em", margin: "17px 0 0", maxWidth: 1140 }}>{title}</h2>
      {children}
      <div style={{ position: "absolute", left: 112, right: 112, bottom: 29, display: "flex", alignItems: "center", gap: 20 }}>
        <div style={{ height: 2, flex: 1, background: "rgba(255,255,255,.08)", borderRadius: 99, overflow: "hidden" }}>
          <div style={{ height: "100%", width: `${Math.min(100, (frame / durationInFrames) * 100)}%`, background: "linear-gradient(90deg,#70e1d4,#87a9ff,#c5a4ff)" }} />
        </div>
        <span style={{ ...text, color: COLORS.muted, fontSize: 14, letterSpacing: ".12em" }}>{index} — 06</span>
      </div>
    </AbsoluteFill>
  );
}

function SourceIcon({ children, tint }: { children: ReactNode; tint: string }) {
  return <div style={{ width: 47, height: 47, borderRadius: 14, display: "grid", placeItems: "center", color: tint, background: `${tint}18`, fontSize: 20, fontWeight: 800 }}>{children}</div>;
}

function HeroScene() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const hero = spring({ frame, fps, config: { damping: 18, mass: .82, stiffness: 75 } });
  return (
    <AbsoluteFill style={{ justifyContent: "center", padding: "0 150px", color: COLORS.white }}>
      <div style={{ position: "absolute", right: 165, top: 155, width: 520, height: 520, borderRadius: "50%", background: "radial-gradient(circle, rgba(91,116,214,.23), rgba(33,174,170,.08) 46%, transparent 72%)", filter: "blur(28px)" }} />
      <div style={{ opacity: hero, transform: `translateY(${(1 - hero) * 42}px)` }}>
        <Wordmark />
        <div style={{ ...label, marginTop: 82 }}>A learning loop for a moving world</div>
        <h1 style={{ ...text, fontSize: 120, lineHeight: .98, letterSpacing: "-.075em", fontWeight: 570, maxWidth: 1120, margin: "25px 0 26px" }}>
          Your course<br />can keep up.
        </h1>
        <p style={{ ...text, color: COLORS.muted, fontSize: 28, lineHeight: 1.5, maxWidth: 700, margin: 0 }}>
          Courserefresh keeps lessons aligned with the subject they teach.
        </p>
      </div>
      <div style={{ ...panel, position: "absolute", right: 160, bottom: 240, width: 430, padding: 27, opacity: reveal(frame, 20, 24), transform: `translateY(${rise(frame, 20, 38)}px) rotate(-3deg)` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><Chip>AGENT OPS</Chip><span style={{ ...text, color: COLORS.muted, fontSize: 14 }}>6 lessons</span></div>
        <div style={{ ...text, fontSize: 28, fontWeight: 600, marginTop: 25 }}>Tool permissions</div>
        <div style={{ color: COLORS.muted, fontSize: 16, marginTop: 7 }}>Lesson 04 · current version v5</div>
        <div style={{ height: 1, background: COLORS.line, margin: "22px 0 18px" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 11, color: COLORS.green, fontSize: 15 }}><Dot /> Course health monitored</div>
      </div>
    </AbsoluteFill>
  );
}

function WatchScene() {
  const frame = useCurrentFrame();
  const sources = [
    { name: "n8n release notes", sub: "Permissions API", icon: "n8n", color: COLORS.violet, time: "09:14" },
    { name: "n8n documentation", sub: "Tool settings", icon: "↗", color: COLORS.cyan, time: "09:14" },
    { name: "Package registry", sub: "Version signal", icon: "npm", color: COLORS.amber, time: "09:15" },
  ];
  return <Frame index="01" kicker="Notice" title="The subject moves. The course notices.">
    <div style={{ display: "grid", gridTemplateColumns: "1fr 450px", gap: 34, marginTop: 48, alignItems: "stretch" }}>
      <div style={{ ...panel, padding: 31 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 22 }}>
          <div style={{ ...text, fontSize: 18, fontWeight: 600 }}>Sources watched</div><Chip>Scheduled checks</Chip>
        </div>
        {sources.map((source, i) => {
          const alpha = reveal(frame, 10 + i * 8, 15);
          return <div key={source.name} style={{ display: "flex", alignItems: "center", gap: 17, padding: "19px 0", borderTop: `1px solid ${COLORS.line}`, opacity: alpha, transform: `translateX(${(1 - alpha) * 25}px)` }}>
            <SourceIcon tint={source.color}>{source.icon}</SourceIcon>
            <div style={{ flex: 1 }}><div style={{ ...text, fontSize: 19, fontWeight: 550 }}>{source.name}</div><div style={{ color: COLORS.muted, fontSize: 15, marginTop: 5 }}>{source.sub}</div></div>
            <div style={{ textAlign: "right" }}><div style={{ color: COLORS.green, fontSize: 15, fontWeight: 600 }}>Changed</div><div style={{ color: COLORS.muted, fontSize: 13, marginTop: 4 }}>{source.time}</div></div>
          </div>;
        })}
        <div style={{ borderTop: `1px solid ${COLORS.line}`, paddingTop: 18, color: COLORS.muted, fontSize: 15 }}>Page snapshots fingerprinted and compared with the last scan.</div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        <div style={{ ...panel, padding: 27, flex: 1, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div><div style={{ ...label, fontSize: 13 }}>Evidence pattern</div><div style={{ ...text, fontSize: 26, lineHeight: 1.3, marginTop: 18, fontWeight: 550 }}>One change.<br />Independent sources.</div></div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}><Dot /><span style={{ color: COLORS.green, fontSize: 16 }}>Corroboration found</span></div>
        </div>
        <div style={{ ...panel, padding: 25, background: "linear-gradient(140deg,rgba(112,225,212,.11),rgba(17,23,36,.86) 60%)" }}>
          <div style={{ color: COLORS.muted, fontSize: 14, letterSpacing: ".08em", textTransform: "uppercase" }}>Course in scope</div>
          <div style={{ ...text, fontSize: 22, fontWeight: 600, marginTop: 11 }}>Agent Ops · Lesson 04</div>
          <div style={{ color: COLORS.muted, fontSize: 15, marginTop: 6 }}>Tool permissions and the human exit</div>
        </div>
      </div>
    </div>
  </Frame>;
}

function DecideScene() {
  const frame = useCurrentFrame();
  const decision = spring({ frame: Math.max(0, frame - 23), fps: FPS, config: { damping: 15, stiffness: 90 } });
  return <Frame index="02" kicker="Decide" title="Evidence earns action. A rulebook sets the boundary.">
    <div style={{ display: "grid", gridTemplateColumns: "1fr 160px 1fr", gap: 25, alignItems: "center", marginTop: 57 }}>
      <div style={{ ...panel, padding: 28 }}>
        <div style={{ ...label, color: COLORS.muted, fontSize: 13 }}>Corroboration</div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 24 }}><SourceIcon tint={COLORS.violet}>n8n</SourceIcon><div><div style={{ ...text, fontSize: 18 }}>Release notes</div><div style={{ color: COLORS.muted, fontSize: 14, marginTop: 5 }}>Permissions renamed</div></div></div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 20 }}><SourceIcon tint={COLORS.cyan}>↗</SourceIcon><div><div style={{ ...text, fontSize: 18 }}>Documentation</div><div style={{ color: COLORS.muted, fontSize: 14, marginTop: 5 }}>New field confirmed</div></div></div>
      </div>
      <div style={{ textAlign: "center", color: COLORS.cyan, fontSize: 49, opacity: reveal(frame, 9, 18) }}>→</div>
      <div style={{ ...panel, padding: 30, borderColor: "rgba(112,225,212,.3)", background: "linear-gradient(135deg,rgba(112,225,212,.10),rgba(17,23,36,.87) 65%)", opacity: decision, transform: `scale(${.94 + decision * .06})` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><div style={{ ...label, fontSize: 13 }}>Policy decision</div><Chip color={COLORS.green}>PUBLISH</Chip></div>
        <div style={{ ...text, fontSize: 27, fontWeight: 600, marginTop: 31 }}>Update lesson 04</div>
        <div style={{ color: COLORS.muted, fontSize: 16, marginTop: 8 }}>Two-source evidence · lesson content</div>
        <div style={{ height: 1, background: COLORS.line, margin: "25px 0 18px" }} />
        <div style={{ display: "flex", justifyContent: "space-between", color: COLORS.muted, fontSize: 15 }}><span>Assessment edits</span><span style={{ color: COLORS.amber }}>Human review</span></div>
      </div>
    </div>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginTop: 23 }}>
      <div style={{ ...panel, padding: "19px 24px", display: "flex", alignItems: "center", gap: 15 }}><span style={{ color: COLORS.amber, fontSize: 22 }}>Ⅱ</span><div><div style={{ ...text, fontSize: 17, fontWeight: 550 }}>One source?</div><div style={{ color: COLORS.muted, fontSize: 14, marginTop: 4 }}>Hold for corroboration.</div></div></div>
      <div style={{ ...panel, padding: "19px 24px", display: "flex", alignItems: "center", gap: 15 }}><span style={{ color: COLORS.red, fontSize: 22 }}>×</span><div><div style={{ ...text, fontSize: 17, fontWeight: 550 }}>Unsafe instruction?</div><div style={{ color: COLORS.muted, fontSize: 14, marginTop: 4 }}>Refuse, record, and surface it.</div></div></div>
    </div>
  </Frame>;
}

function UpdateScene() {
  const frame = useCurrentFrame();
  return <Frame index="03" kicker="Improve" title="The lesson updates. The history stays visible.">
    <div style={{ display: "grid", gridTemplateColumns: "1fr 70px 1fr", gap: 21, marginTop: 49, alignItems: "center" }}>
      <div style={{ ...panel, padding: 27, minHeight: 280, opacity: reveal(frame, 5) }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ ...label, color: COLORS.muted, fontSize: 13 }}>Lesson 04 · v3</div><Chip color={COLORS.red}>Previous</Chip></div>
        <div style={{ ...text, fontSize: 22, fontWeight: 600, marginTop: 27 }}>Tool permissions</div>
        <div style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", color: "#ffb3b5", background: "rgba(255,146,150,.08)", borderRadius: 10, padding: "14px 16px", fontSize: 16, marginTop: 20 }}>− tool_permissions.tools</div>
        <div style={{ color: COLORS.muted, fontSize: 15, marginTop: 15 }}>Setting name from the earlier release</div>
      </div>
      <div style={{ ...text, color: COLORS.muted, fontSize: 32, textAlign: "center", opacity: reveal(frame, 14) }}>→</div>
      <div style={{ ...panel, padding: 27, minHeight: 280, borderColor: "rgba(133,226,180,.26)", opacity: reveal(frame, 19), transform: `translateY(${rise(frame, 19)}px)` }}>
        <div style={{ display: "flex", justifyContent: "space-between" }}><div style={{ ...label, color: COLORS.green, fontSize: 13 }}>Lesson 04 · v4</div><Chip color={COLORS.green}>Published</Chip></div>
        <div style={{ ...text, fontSize: 22, fontWeight: 600, marginTop: 27 }}>Tool permissions</div>
        <div style={{ fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", color: "#a9f0ca", background: "rgba(133,226,180,.08)", borderRadius: 10, padding: "14px 16px", fontSize: 16, marginTop: 20 }}>+ permissions.mode.tools</div>
        <div style={{ color: COLORS.muted, fontSize: 15, marginTop: 15 }}>Updated explanation · source-linked diff</div>
      </div>
    </div>
    <div style={{ ...panel, marginTop: 21, padding: "20px 26px", display: "flex", alignItems: "center", justifyContent: "space-between", opacity: reveal(frame, 35) }}>
      <div style={{ display: "flex", alignItems: "center", gap: 17 }}><div style={{ width: 42, height: 42, borderRadius: 13, display: "grid", placeItems: "center", color: COLORS.violet, background: `${COLORS.violet}18`, fontSize: 22 }}>✓</div><div><div style={{ ...text, fontSize: 18, fontWeight: 600 }}>Matching quiz item regenerated</div><div style={{ color: COLORS.muted, fontSize: 14, marginTop: 4 }}>Question follows the new setting name; assessment change remains with the author.</div></div></div>
      <Chip color={COLORS.violet}>Review required</Chip>
    </div>
  </Frame>;
}

function LearnScene() {
  const frame = useCurrentFrame();
  return <Frame index="04" kicker="Learn" title="Support reaches learners before they have to ask.">
    <div style={{ display: "grid", gridTemplateColumns: "1.05fr .95fr", gap: 30, marginTop: 52 }}>
      <div style={{ ...panel, padding: 29 }}>
        <div style={{ ...label, fontSize: 13 }}>Learning signal</div>
        <div style={{ ...text, fontSize: 27, fontWeight: 600, marginTop: 19 }}>A concept is causing friction.</div>
        <div style={{ color: COLORS.muted, fontSize: 16, marginTop: 9 }}>Repeated attempts on tool permissions</div>
        <div style={{ display: "flex", alignItems: "end", gap: 11, height: 125, marginTop: 24, borderBottom: `1px solid ${COLORS.line}`, padding: "0 9px" }}>
          {[44, 63, 54, 82, 68, 105, 92, 114, 88, 125, 103, 136, 111, 126].map((height, i) => {
            const visible = reveal(frame, 8 + i * 2, 10);
            return <div key={i} style={{ flex: 1, height: `${height * visible}px`, borderRadius: "6px 6px 0 0", background: i > 10 ? "linear-gradient(0deg,rgba(255,194,122,.16),#f0c27a)" : "linear-gradient(0deg,rgba(112,225,212,.1),#70e1d4)" }} />;
          })}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", color: COLORS.muted, fontSize: 13, marginTop: 12 }}><span>Practice attempts</span><span>Consented cohort only</span></div>
      </div>
      <div style={{ ...panel, padding: 29, background: "linear-gradient(145deg,rgba(197,164,255,.12),rgba(17,23,36,.88) 68%)", opacity: reveal(frame, 25), transform: `translateY(${rise(frame, 25)}px)` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><div style={{ ...label, color: COLORS.violet, fontSize: 13 }}>A short nudge</div><Chip color={COLORS.violet}>2 min</Chip></div>
        <div style={{ ...text, fontSize: 29, fontWeight: 600, lineHeight: 1.2, marginTop: 26 }}>Permission scopes,<br />made clear.</div>
        <div style={{ color: COLORS.muted, fontSize: 16, lineHeight: 1.55, marginTop: 17 }}>One idea. One worked example. One practice question.</div>
        <div style={{ marginTop: 24, borderRadius: 14, border: `1px solid ${COLORS.line}`, padding: "14px 17px", color: COLORS.white, fontSize: 15, background: "rgba(255,255,255,.025)" }}><span style={{ color: COLORS.violet, marginRight: 10 }}>01</span> What should this tool be allowed to touch?</div>
        <div style={{ color: COLORS.muted, fontSize: 13, marginTop: 19 }}>Opt-in delivery · clear way to stop</div>
      </div>
    </div>
    <div style={{ display: "flex", gap: 12, marginTop: 22, opacity: reveal(frame, 34) }}><Chip color={COLORS.green}>Consent respected</Chip><Chip color={COLORS.cyan}>Learning signal informs the next cycle</Chip></div>
  </Frame>;
}

function TrustScene() {
  const frame = useCurrentFrame();
  const restore = spring({ frame: Math.max(frame - 53, 0), fps: FPS, config: { damping: 17, stiffness: 85 } });
  return <Frame index="05" kicker="Stay in control" title="Every change carries its own undo condition.">
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 27, marginTop: 50 }}>
      <div style={{ ...panel, padding: 29 }}>
        <div style={{ ...label, fontSize: 13 }}>Authority ladder</div>
        <div style={{ marginTop: 23, display: "flex", flexDirection: "column", gap: 12 }}>
          {[
            ["PA0", "Observe", "No writes"],
            ["PA1", "Draft", "Human approval"],
            ["PA2", "Publish", "Within declared policy"],
            ["PA3", "Author decides", "Assessments & exceptions"],
          ].map(([step, name, description], i) => {
            const alpha = reveal(frame, 7 + i * 8, 13);
            return <div key={step} style={{ display: "flex", alignItems: "center", gap: 17, padding: "13px 15px", borderRadius: 13, background: i === 2 ? "rgba(112,225,212,.085)" : "rgba(255,255,255,.025)", border: `1px solid ${i === 2 ? "rgba(112,225,212,.22)" : COLORS.line}`, opacity: alpha }}>
              <span style={{ color: i === 2 ? COLORS.cyan : COLORS.muted, fontFamily: "ui-monospace,monospace", fontSize: 14, fontWeight: 700, width: 42 }}>{step}</span>
              <div style={{ flex: 1 }}><div style={{ ...text, fontSize: 16, fontWeight: 600 }}>{name}</div><div style={{ color: COLORS.muted, fontSize: 13, marginTop: 3 }}>{description}</div></div>
              {i === 2 && <Dot />}
            </div>;
          })}
        </div>
      </div>
      <div style={{ ...panel, padding: 29, position: "relative", overflow: "hidden" }}>
        <div style={{ ...label, fontSize: 13 }}>A promise at publish time</div>
        <div style={{ ...text, fontSize: 25, fontWeight: 600, marginTop: 22 }}>Evaluate the change.<br />Keep the undo visible.</div>
        <div style={{ marginTop: 23, padding: 19, borderRadius: 16, border: `1px solid ${COLORS.line}`, background: "rgba(0,0,0,.15)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: COLORS.muted, fontSize: 14 }}><span>Revert gate</span><span style={{ color: COLORS.amber }}>48-hour window</span></div>
          <div style={{ ...text, fontSize: 21, marginTop: 13 }}>Quiz outcome fails to improve</div>
          <div style={{ color: COLORS.muted, fontSize: 14, marginTop: 7 }}>Minimum cohort: 5 learners</div>
        </div>
        <div style={{ position: "absolute", left: 29, right: 29, bottom: 27, opacity: restore, transform: `translateY(${(1 - restore) * 14}px)` }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderRadius: 15, border: "1px solid rgba(255,146,150,.26)", background: "rgba(255,146,150,.08)", padding: "15px 17px" }}>
            <div><div style={{ color: COLORS.red, fontSize: 12, letterSpacing: ".15em", fontWeight: 700 }}>REVERTED AS A NEW VERSION</div><div style={{ ...text, fontSize: 17, marginTop: 6 }}>v5 restores v3 · history preserved</div></div>
            <span style={{ color: COLORS.red, fontSize: 26 }}>↶</span>
          </div>
        </div>
      </div>
    </div>
  </Frame>;
}

function DigestScene() {
  const frame = useCurrentFrame();
  const rows = [
    { action: "ESCALATE", title: "Single-source change held", detail: "insufficient_corroboration", color: COLORS.amber },
    { action: "PUBLISH", title: "Lesson 04 · v3 to v4", detail: "permissions setting updated", color: COLORS.green },
    { action: "REVERT", title: "Lesson 04 · v5", detail: "prior version restored · gate recorded", color: COLORS.red },
  ];
  return <Frame index="06" kicker="Report" title="A morning digest makes the whole cycle inspectable.">
    <div style={{ ...panel, maxWidth: 1180, margin: "43px auto 0", padding: 30 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: 21, borderBottom: `1px solid ${COLORS.line}` }}>
        <div><div style={{ ...label, fontSize: 13 }}>Courserefresh · daily digest</div><div style={{ ...text, fontSize: 25, fontWeight: 600, marginTop: 8 }}>Good morning. Here’s what needs your attention.</div></div>
        <Chip color={COLORS.cyan}>07:30</Chip>
      </div>
      {rows.map((row, i) => {
        const alpha = reveal(frame, 8 + i * 11, 16);
        return <div key={row.action} style={{ display: "flex", alignItems: "center", gap: 18, padding: "19px 3px", borderBottom: `1px solid ${COLORS.line}`, opacity: alpha, transform: `translateX(${(1-alpha)*20}px)` }}>
          <Chip color={row.color}>{row.action}</Chip>
          <div style={{ flex: 1 }}><div style={{ ...text, fontSize: 19, fontWeight: 600 }}>{row.title}</div><div style={{ color: COLORS.muted, fontSize: 15, marginTop: 5 }}>{row.detail}</div></div>
          <span style={{ color: COLORS.muted, fontSize: 20 }}>↗</span>
        </div>;
      })}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11, color: COLORS.green, fontSize: 16 }}><Dot /> Receipt chain verified</div>
        <div style={{ color: COLORS.muted, fontFamily: "ui-monospace,monospace", fontSize: 14 }}>evidence · decision · version · outcome</div>
      </div>
    </div>
  </Frame>;
}

function NarrationCaption({ value }: { value: string }) {
  const frame = useCurrentFrame();
  const alpha = interpolate(frame, [0, 14], [0, 1], easing);
  return <div style={{ position: "absolute", left: 135, right: 135, bottom: 78, opacity: alpha, transform: `translateY(${(1-alpha)*12}px)`, borderRadius: 15, border: "1px solid rgba(185,205,235,.16)", background: "rgba(7,10,17,.92)", boxShadow: "0 12px 36px rgba(0,0,0,.28)", padding: "19px 28px", color: "#eef2fa", fontSize: 22, lineHeight: 1.42, fontWeight: 450, textAlign: "center", letterSpacing: ".003em" }}>{value}</div>;
}

function NarratedChapter({ Scene, narration }: { Scene: ComponentType; narration: string }) {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const opacity = interpolate(frame, [0, 16, durationInFrames-15, durationInFrames], [0, 1, 1, 0], easing);
  const scale = interpolate(frame, [0, durationInFrames], [1.005, 1.024], easing);
  return <AbsoluteFill>
    <div style={{ position: "absolute", inset: 0, opacity, transform: `scale(${scale})`, transformOrigin: "center" }}><Scene /></div>
    <NarrationCaption value={narration} />
  </AbsoluteFill>;
}

function CloseScene() {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mark = spring({ frame: Math.max(0, frame - 20), fps, config: { damping: 13, stiffness: 95 } });
  return <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", textAlign: "center", color: COLORS.white }}>
    <div style={{ position: "absolute", width: 700, height: 700, borderRadius: "50%", background: "radial-gradient(circle,rgba(112,225,212,.16),rgba(110,126,255,.07) 42%,transparent 72%)", filter: "blur(30px)" }} />
    <div style={{ position: "relative", opacity: reveal(frame, 0, 20) }}>
      <div style={{ transform: `scale(${.75 + mark * .25})`, marginBottom: 29 }}><div style={{ display: "inline-flex" }}><Wordmark /></div></div>
      <div style={{ ...label, marginTop: 57 }}>A course that stays true.</div>
      <h2 style={{ ...text, fontSize: 79, fontWeight: 560, letterSpacing: "-.06em", margin: "18px 0 18px" }}>Back to teaching.</h2>
      <p style={{ ...text, color: COLORS.muted, fontSize: 22, margin: 0 }}>Courserefresh · Notice what changed. Keep what works.</p>
    </div>
  </AbsoluteFill>;
}

const SCENES: ComponentType[] = [HeroScene, WatchScene, DecideScene, UpdateScene, LearnScene, TrustScene, DigestScene, CloseScene];

export function CourserefreshDemo() {
  let from = 0;
  const sequences = SCENES.map((Scene, index) => {
    const planned = Math.round(timing.chapterSeconds[index] * FPS);
    const duration = index === SCENES.length - 1 ? TOTAL_FRAMES - from : Math.min(planned, TOTAL_FRAMES - from);
    const sequence = <Sequence key={index} from={from} durationInFrames={duration} premountFor={12}>
      <NarratedChapter Scene={Scene} narration={NARRATION[index]} />
    </Sequence>;
    from += duration;
    return sequence;
  });
  return <AbsoluteFill style={{ background: COLORS.ink, overflow: "hidden", ...text }}>
    <AbsoluteFill style={{ opacity: .42, backgroundImage: "linear-gradient(rgba(164,183,219,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(164,183,219,.035) 1px, transparent 1px)", backgroundSize: "72px 72px", maskImage: "linear-gradient(to bottom, black, transparent 88%)" }} />
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 75% 6%,rgba(75,94,180,.13),transparent 40%), radial-gradient(ellipse at 8% 94%,rgba(27,141,132,.09),transparent 37%)" }} />
    {sequences}
  </AbsoluteFill>;
}

export const VIDEO_CONFIG = { width: 1920, height: 1080, fps: FPS, durationInFrames: TOTAL_FRAMES };
