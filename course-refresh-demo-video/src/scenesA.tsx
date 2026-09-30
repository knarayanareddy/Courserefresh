import {
  BookOpen,
  Building2,
  Clock,
  Eye,
  FlaskConical,
  Mail,
  PenLine,
  Presentation,
  RefreshCw,
  ShieldCheck,
  Bell,
  TrendingUp,
  Users,
  GitBranch,
  Check,
  X,
  Loader2,
  FileText,
} from "lucide-react";
import { Eyebrow, Pill, Reveal, Window, useDelayed, type SceneProps } from "./ui";

/* ───────────────────────── 1 · The promise ───────────────────────── */
export function Opening({ step }: SceneProps) {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center text-center">
      <div style={{ opacity: step >= 1 ? 0.32 : 1, transition: "opacity 1200ms var(--ease)" }}>
        <Reveal show={step >= 0} y={36} blur={18} duration={1400}>
          <h1 className="max-w-[1500px] text-[112px] font-semibold leading-[1.04] tracking-[-0.035em]">
            Every semester, a professor makes a quiet promise.
          </h1>
        </Reveal>
      </div>
      <Reveal show={step >= 1} y={36} blur={18} duration={1400} className="mt-10">
        <h2 className="grad-text max-w-[1500px] text-[112px] font-semibold leading-[1.04] tracking-[-0.035em]">
          That what they teach is still true.
        </h2>
      </Reveal>
    </div>
  );
}

/* ───────────────────────── 2 · The overload ───────────────────────── */
const TILES = [
  { label: "Lectures", icon: Presentation, from: "#0a84ff", to: "#5e5ce6", badge: "" },
  { label: "Grading", icon: PenLine, from: "#ff9f0a", to: "#ff6a00", badge: "48" },
  { label: "Office hours", icon: Users, from: "#30d158", to: "#00a86b", badge: "7" },
  { label: "Committees", icon: Building2, from: "#bf5af2", to: "#8944ab", badge: "3" },
  { label: "Research", icon: FlaskConical, from: "#64d2ff", to: "#0a84ff", badge: "" },
  { label: "Inbox", icon: Mail, from: "#3a8dff", to: "#0a5bd8", badge: "99+" },
];

const OVERLOAD_HEADLINES = [
  "Professors juggle more than anyone sees.",
  "Meanwhile, the subject keeps moving.",
  "Refreshing the course is the first thing to slip.",
];

export function Overload({ step }: SceneProps) {
  return (
    <div className="flex h-full w-full items-center gap-[90px]">
      <div className="relative h-full w-[760px]">
        {OVERLOAD_HEADLINES.map((h, i) => (
          <Reveal
            key={h}
            show={step === i}
            y={step > i ? -30 : 30}
            className="absolute inset-0 flex items-center"
          >
            <h2
              className={`text-[84px] font-semibold leading-[1.06] tracking-[-0.03em] ${
                i === 1 ? "grad-text" : ""
              }`}
            >
              {h}
            </h2>
          </Reveal>
        ))}
      </div>

      <div className="relative flex h-full flex-1 flex-col items-center justify-center">
        <div
          className="grid grid-cols-3 gap-x-12 gap-y-9"
          style={{
            opacity: step >= 2 ? 0.28 : 1,
            transition: "opacity 1400ms var(--ease)",
          }}
        >
          {TILES.map((t, i) => {
            const Icon = t.icon;
            return (
              <Reveal key={t.label} show={step >= 0} delay={200 + i * 140} y={40} scale={0.85}>
                <div
                  className="floaty flex flex-col items-center gap-4"
                  style={{ animationDelay: `${i * 0.7}s`, animationDuration: `${5 + (i % 3)}s` }}
                >
                  <div
                    className="relative flex h-[180px] w-[180px] items-center justify-center rounded-[42px]"
                    style={{
                      background: `linear-gradient(160deg, ${t.from}, ${t.to})`,
                      boxShadow: `0 30px 60px -20px ${t.to}99, inset 0 1px 0 rgba(255,255,255,.35)`,
                    }}
                  >
                    <Icon size={84} strokeWidth={1.7} color="#fff" />
                    {t.badge && (
                      <div className="absolute -right-4 -top-4 flex h-[58px] min-w-[58px] items-center justify-center rounded-full bg-[#ff3b30] px-3 text-[30px] font-semibold shadow-[0_8px_24px_rgba(255,59,48,.5)] ring-4 ring-black">
                        {t.badge}
                      </div>
                    )}
                  </div>
                  <span className="text-[28px] font-medium text-[var(--ink-2)]">{t.label}</span>
                </div>
              </Reveal>
            );
          })}
        </div>

        <Reveal show={step >= 2} delay={300} y={30} className="absolute bottom-[10px] w-[700px]">
          <div
            className="glass flex items-center gap-6 rounded-[32px] px-8 py-6"
            style={{ borderStyle: "dashed", borderColor: "rgba(255,255,255,.28)" }}
          >
            <div className="flex h-[84px] w-[84px] items-center justify-center rounded-[22px] bg-white/10">
              <RefreshCw size={44} color="#fff" />
            </div>
            <div className="flex-1">
              <div className="text-[34px] font-semibold">Refresh CS 101</div>
              <div className="text-[24px] text-[var(--ink-2)]">Always next week’s task</div>
            </div>
            <Clock size={44} color="var(--orange)" />
            <span className="text-[30px] font-semibold text-[var(--orange)]">Someday</span>
          </div>
        </Reveal>
      </div>
    </div>
  );
}

/* ───────────────────────── 3 · CS 101 ───────────────────────── */
const LESSONS = [
  "Hello, World",
  "Variables & types",
  "Control flow",
  "Your first program & packages",
  "Functions",
  "Lists & loops",
];

export function Cs101({ step }: SceneProps) {
  const broken = step >= 2;
  return (
    <div className="flex h-full w-full items-center justify-center gap-[70px]">
      <Reveal show={step >= 0} y={40} className="w-[720px]">
        <div className="glass rounded-[40px] p-10">
          <div className="flex items-center gap-6">
            <div className="flex h-[96px] w-[96px] items-center justify-center rounded-full bg-gradient-to-br from-[#ff9f0a] to-[#ff375f] text-[44px] font-semibold">
              R
            </div>
            <div>
              <div className="text-[24px] font-medium text-[var(--ink-2)]">Prof. Rivera</div>
              <div className="text-[30px] font-semibold tracking-tight">Fall term</div>
            </div>
          </div>
          <div className="mt-8 flex items-center gap-4">
            <BookOpen size={40} color="var(--blue)" />
            <div className="text-[30px] font-semibold text-[var(--blue)]">CS 101</div>
          </div>
          <h3 className="mt-2 text-[52px] font-semibold leading-[1.08] tracking-[-0.02em]">
            Introduction to Computer Science
          </h3>
          <div className="mt-8 space-y-2">
            {LESSONS.map((l, i) => {
              const hot = i === 3 && step >= 1;
              return (
                <div
                  key={l}
                  className="flex items-center gap-5 rounded-2xl px-5 py-3 text-[27px]"
                  style={{
                    background: hot ? (broken ? "rgba(255,69,58,.16)" : "rgba(41,151,255,.18)") : "transparent",
                    color: hot ? "#fff" : "var(--ink-2)",
                    transition: "all 900ms var(--ease)",
                    boxShadow: hot
                      ? `inset 0 0 0 1.5px ${broken ? "rgba(255,69,58,.7)" : "rgba(41,151,255,.6)"}`
                      : "none",
                  }}
                >
                  <span className="mono w-8 text-[var(--ink-3)]">{i + 1}</span>
                  <span className="font-medium">{l}</span>
                  {hot && (
                    <span
                      className="ml-auto text-[22px] font-semibold"
                      style={{ color: broken ? "var(--red)" : "var(--blue)" }}
                    >
                      {broken ? "OUT OF DATE" : "LESSON 4"}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </Reveal>

      <div className="relative h-[560px] w-[800px]">
        <Reveal show={step >= 1} y={40} delay={150} className="absolute inset-0">
          <Window title="lesson-04 — Terminal" className="h-full">
            <div className="mono relative h-[450px] p-10 text-[31px] leading-[1.7]">
              <div>
                <span className="text-[var(--ink-3)]">$ </span>
                <span>pip install requests</span>
                <span className="caret ml-1 inline-block h-[34px] w-[14px] translate-y-[6px] bg-white/80" />
              </div>
              <Reveal show={step === 1} delay={500} y={10} blur={4} className="absolute left-10 right-10 top-[112px]">
                <div className="text-[var(--green)]">Successfully installed requests</div>
                <div className="mt-8 flex items-center gap-3 font-sans text-[28px] text-[var(--ink-2)]">
                  <Check size={34} color="var(--green)" /> Worked for years.
                </div>
              </Reveal>
              <Reveal show={broken} delay={250} y={10} blur={4} className="absolute left-10 right-10 top-[112px]">
                <div className="font-semibold text-[var(--red)]">error: externally-managed-environment</div>
                <div className="mt-3 text-[26px] leading-[1.5] text-[#ff8a82]">
                  × This environment is externally managed. To install packages, create a virtual environment.
                </div>
                <div className="mt-8 flex items-center gap-3 font-sans text-[28px] text-[var(--ink-2)]">
                  <X size={34} color="var(--red)" /> Lesson 4 is now wrong.
                </div>
              </Reveal>
            </div>
          </Window>
        </Reveal>
      </div>
    </div>
  );
}

/* ───────────────────────── 4 · Courserefresh ───────────────────────── */
export function LogoMark({ size = 180 }: { size?: number }) {
  return (
    <div
      className="relative flex items-center justify-center"
      style={{
        width: size,
        height: size,
        borderRadius: size * 0.235,
        background: "linear-gradient(150deg, #5ac8fa 0%, #0a84ff 45%, #bf5af2 100%)",
        boxShadow: "0 40px 90px -20px rgba(10,132,255,.7), inset 0 2px 0 rgba(255,255,255,.4)",
      }}
    >
      <RefreshCw size={size * 0.52} strokeWidth={2} color="#fff" className="spin-slow" />
    </div>
  );
}

const PIPELINE = [
  { label: "Notice", icon: Eye, c: "#64d2ff" },
  { label: "Verify", icon: ShieldCheck, c: "#30d158" },
  { label: "Decide", icon: GitBranch, c: "#ff9f0a" },
  { label: "Act", icon: PenLine, c: "#bf5af2" },
  { label: "Learn", icon: TrendingUp, c: "#ff375f" },
  { label: "Report", icon: Bell, c: "#0a84ff" },
];

export function Intro({ step }: SceneProps) {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center text-center">
      <div
        className="flex flex-col items-center"
        style={{
          transform: step >= 1 ? "translateY(-40px) scale(.82)" : "translateY(40px)",
          transition: "transform 1400ms var(--ease)",
        }}
      >
        <Reveal show={step >= 0} scale={0.7} y={20} duration={1300}>
          <LogoMark />
        </Reveal>
        <Reveal show={step >= 0} delay={250} duration={1300} className="mt-8">
          <h1 className="text-[150px] font-semibold leading-none tracking-[-0.045em]">Courserefresh</h1>
        </Reveal>
      </div>

      <Reveal show={step >= 1} y={24} className="mt-[-10px]">
        <p className="grad-text text-[52px] font-medium tracking-[-0.01em]">
          A course that monitors the thing it teaches.
        </p>
      </Reveal>

      <div className="mt-14 flex items-center gap-5">
        {PIPELINE.map((p, i) => {
          const Icon = p.icon;
          return (
            <Reveal key={p.label} show={step >= 1} delay={500 + i * 160} y={24} scale={0.9}>
              <div className="flex items-center gap-5">
                <div className="glass flex items-center gap-4 rounded-full px-7 py-4">
                  <Icon size={34} color={p.c} />
                  <span className="text-[30px] font-semibold">{p.label}</span>
                </div>
                {i < PIPELINE.length - 1 && <span className="text-[34px] text-[var(--ink-3)]">›</span>}
              </div>
            </Reveal>
          );
        })}
      </div>
    </div>
  );
}

/* ───────────────────────── 5 · Notice ───────────────────────── */
const SOURCES = [
  { name: "Debian release notes", url: "debian.org", hash: "9f2c…a41e", changed: true },
  { name: "Python Packaging User Guide", url: "packaging.python.org", hash: "c07b…5d92", changed: true },
  { name: "Python docs · tutorial", url: "docs.python.org", hash: "41ae…e0b7", changed: false },
  { name: "CS 101 textbook errata", url: "publisher.example", hash: "7d13…0c68", changed: false },
];

function SourceRow({ s, i, step }: { s: (typeof SOURCES)[number]; i: number; step: number }) {
  const fetched = useDelayed(step >= 0, 1500 + i * 650);
  const hot = step >= 1 && s.changed;
  const dim = step >= 1 && !s.changed;
  return (
    <Reveal show={step >= 0} delay={300 + i * 280} y={30}>
      <div
        className={`glass flex items-center gap-6 rounded-[28px] px-8 py-6 ${hot ? "glow-green" : ""}`}
        style={{
          opacity: dim ? 0.38 : 1,
          transition: "opacity 1000ms var(--ease)",
          background: hot ? "rgba(48,209,88,.10)" : undefined,
        }}
      >
        <div className="flex h-[72px] w-[72px] items-center justify-center rounded-[20px] bg-white/[0.08]">
          <FileText size={38} color={hot ? "var(--green)" : "var(--ink-2)"} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-[32px] font-semibold tracking-tight">{s.name}</div>
          <div className="mono text-[22px] text-[var(--ink-3)]">
            {s.url}
            <span className="ml-4">
              {fetched ? `sha256 ${s.hash}` : ""}
            </span>
          </div>
        </div>
        <div className="flex w-[230px] justify-end">
          {!fetched ? (
            <span className="flex items-center gap-3 text-[24px] text-[var(--ink-2)]">
              <Loader2 size={28} className="spin" /> Fetching
            </span>
          ) : hot ? (
            <Pill color="#30d158">CHANGED</Pill>
          ) : (
            <span className="flex items-center gap-3 text-[24px] text-[var(--ink-2)]">
              <Check size={28} color="var(--green)" /> Unchanged
            </span>
          )}
        </div>
      </div>
    </Reveal>
  );
}

export function Notice({ step }: SceneProps) {
  return (
    <div className="flex h-full w-full items-center gap-[80px]">
      <div className="w-[560px]">
        <Reveal show={step >= 0}>
          <Eyebrow>01 · Notice</Eyebrow>
          <h2 className="mt-5 text-[78px] font-semibold leading-[1.06] tracking-[-0.03em]">
            Watching the world CS&nbsp;101 teaches.
          </h2>
        </Reveal>
        <Reveal show={step >= 0} delay={900} className="mt-10">
          <div className="flex items-center gap-4 text-[28px] text-[var(--ink-2)]">
            <div className="h-4 w-4 rounded-full bg-[var(--green)] pulse-ring" />
            Real pages, fetched with Apify
          </div>
        </Reveal>
        <Reveal show={step >= 1} y={20} className="mt-12">
          <div className="glass rounded-[28px] p-7">
            <div className="mono text-[22px] text-[var(--green)]">DELTA · 2 independent sources</div>
            <div className="mt-2 text-[34px] font-semibold leading-tight">
              pip now refuses system-wide installs.
            </div>
          </div>
        </Reveal>
      </div>
      <div className="flex-1 space-y-5">
        {SOURCES.map((s, i) => (
          <SourceRow key={s.name} s={s} i={i} step={step} />
        ))}
      </div>
    </div>
  );
}
