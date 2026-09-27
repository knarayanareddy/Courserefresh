import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { stagedCard } from './data/mockData';
import PresentationSlides from './components/PresentationSlides';
import WorkflowVisualizer from './components/WorkflowVisualizer';
import AuthorConsole from './components/AuthorConsole';
import LiveLoopBadge from './components/LiveLoopBadge';
import CoursesSection from './components/CoursesSection';

// ─── Navigation ───────────────────────────────────────────────────────────────
type Section = 'overview' | 'slides' | 'workflow' | 'courses' | 'console';

const nav: { id: Section; label: string; sub: string }[] = [
  { id: 'overview',  label: 'Overview',         sub: 'What & why' },
  { id: 'slides',   label: 'Deck (10 slides)',   sub: 'Problem · Loop · Safeguards · Proof' },
  { id: 'workflow', label: 'Workflow Runs',      sub: '5 views of the recorded runs' },
  { id: 'courses',  label: 'Course',             sub: 'agent-ops · 6 lessons' },
  { id: 'console',  label: 'Author Console',     sub: 'Receipts · digest · chain' },
];

// ─── Overview page ────────────────────────────────────────────────────────────
function OverviewPage({ onNavigate }: { onNavigate: (s: Section) => void }) {
  return (
    <div className="max-w-4xl" style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
      {/* Presentation-layer banner (the honest label) */}
      <div className="mb-6 px-4 py-2.5 border rounded-sm flex flex-wrap items-center gap-2"
        style={{ borderColor: '#96550A', backgroundColor: '#F7EFE4' }}>
        <span className="text-xs font-mono font-bold" style={{ color: '#96550A' }}>DEMO VIEW</span>
        <span className="text-xs leading-relaxed" style={{ color: '#4A443A' }}>
          This React app is a presentation layer over the real artifacts. The shipped console is <span className="font-mono">app/serve.py</span> — one page, no scripts. Data here is generated from the repo’s own receipts and lesson files (see <span className="font-mono">specs/evidence/</span>).
        </span>
      </div>

      {/* Hero */}
      <div className="mb-10 pb-8 border-b" style={{ borderColor: '#C9C0AE' }}>
        <div className="text-[11px] font-mono uppercase tracking-widest mb-2" style={{ color: '#8E8160' }}>
          Build Weekend · Autonomy 25% · Proven in real use 25% · Apify &amp; n8n 20%
        </div>
        <h1 className="text-4xl md:text-5xl font-semibold leading-tight mb-4" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
          CourseRefresh
        </h1>
        <p className="text-xl leading-relaxed mb-2" style={{ color: '#4A443A', fontFamily: "'Source Serif 4', Georgia, serif", maxWidth: '60ch' }}>
          A course that keeps itself true: it watches the sources the course teaches, notices when the world has moved, rewrites the affected lessons and quizzes when the evidence is corroborated, and puts a receipt in the teacher&#39;s inbox instead of another chore on their desk.
        </p>
        <p className="text-sm leading-relaxed mt-4" style={{ color: '#68604F', maxWidth: '72ch' }}>
          <em style={{ fontFamily: "'Source Serif 4', Georgia, serif" }}>
            Built for the hackathon brief: "Build a course that updates as its subject changes. Spot when a learner is stuck before they ask."
          </em>
        </p>
      </div>

      {/* The loop */}
      <div className="mb-10">
        <div className="text-[11px] font-mono uppercase tracking-widest mb-4" style={{ color: '#8E8160' }}>
          The loop — notice → verify → decide → act → learn → report
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { phase: 'NOTICE', icon: '◉', desc: 'Apify actors fetch release notes, changelogs, and docs on a schedule. Snapshots hashed and cached. Unchanged sources produce no event.' },
            { phase: 'VERIFY', icon: '⊛', desc: '≥2 independent sources required before any claim moves forward. Verbatim quotes anchored in snapshots. One source → ESCALATE, not a quiet draft.' },
            { phase: 'DECIDE', icon: '⊕', desc: 'The POLICY node — deterministic, one screen — returns one action and one or more reason codes from a closed taxonomy. Models propose; code decides.' },
            { phase: 'ACT',    icon: '↑', desc: 'A new versioned lesson body, a diff, a regenerated quiz, and a CHANGELOG commit on bot/courserefresh. Consented learners receive a four-line card: what changed, where the diff is, how to stop.' },
            { phase: 'LEARN',  icon: '◎', desc: 'Cohort window evaluated every 15 min. Stuck learners (consecutive_wrong ≥ 2) receive a micro-lesson. The revert gate checks quiz_delta at 48h.' },
            { phase: 'REPORT', icon: '§', desc: 'Digest at 07:30 UTC. Refusals listed first. Every number links to a receipt. Chain verified. Budget printed. Mode (live/sim/degraded) always named.' },
          ].map(p => (
            <div key={p.phase} className="p-4 border rounded-sm" style={{ borderColor: '#C9C0AE', backgroundColor: '#F3EFE7' }}>
              <div className="flex items-center gap-2 mb-2">
                <span className="text-lg font-mono" style={{ color: '#6B4E2E' }}>{p.icon}</span>
                <span className="text-[11px] font-mono font-bold uppercase tracking-widest" style={{ color: '#6B4E2E' }}>{p.phase}</span>
              </div>
              <p className="text-xs leading-relaxed" style={{ color: '#4A443A' }}>{p.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* The three questions */}
      <div className="mb-10 p-5 border rounded-sm" style={{ borderColor: '#8E8160', backgroundColor: '#EAE4D8' }}>
        <div className="text-[11px] font-mono uppercase tracking-widest mb-4" style={{ color: '#8E8160' }}>
          The three questions the judges ask — answered
        </div>
        <div className="space-y-4">
          {[
            {
              q: 'Where are the rules?',
              a: 'skin/policy.py + app/n8n/policy_node.js — identical runtimes, parity-tested on 59 rows. Visible on the n8n canvas at 100% zoom. No rule lives in a model\'s opinion.',
            },
            {
              q: 'What did it do while nobody was watching?',
              a: 'EVIDENCE.md, chained receipts, the frozen evidence bundles. The hero run cr-20260926-1726-793 (9 chained receipts: 2 publishes, 4 escalations, 1 revert, 1 dispatch, 1 consent wall) and the first scan cr-20260926-1726-054 are shipped whole in specs/evidence/ with their MANIFEST.sha256.',
            },
            {
              q: 'When does it stop?',
              a: 'Authority ladder PA0–PA3, revert gates, kill switch. Constitution.md Art. II, XI, XIV. hostile→publish: 0 is a build-breaking invariant. Assessment changes are PA3 — human-only, permanently.',
            },
          ].map((item, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center rounded-full border text-xs font-mono mt-0.5" style={{ color: '#6B4E2E', borderColor: '#6B4E2E' }}>
                {i + 1}
              </div>
              <div>
                <div className="text-sm font-semibold italic mb-1" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
                  "{item.q}"
                </div>
                <div className="text-sm leading-relaxed" style={{ color: '#4A443A' }}>{item.a}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

          {/* Sources & cadence — what the loop actually watches */}
          <div className="mb-10 p-5 border rounded-sm" style={{ borderColor: '#8E8160', backgroundColor: '#EAE4D8' }}>
            <div className="text-[11px] font-mono uppercase tracking-widest mb-4" style={{ color: '#8E8160' }}>
              The subject course — specs/courserefresh/spec.md §1
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <div className="text-sm leading-relaxed" style={{ color: '#4A443A' }}>
                  The subject taught is <strong>Agent Ops</strong> — a six-lesson course
                  (n8n + Apify + agents in production), chosen because its sources move
                  during any build window: n8n and Apify ship releases on a weekly
                  cadence, and their docs and changelogs are public, fetchable, and
                  independent of each other.
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {['n8n GitHub releases', 'docs.n8n.io', 'npmjs n8n-nodes-base', 'apify.com/changelog', 'npmjs apify-client'].map(s => (
                    <span key={s} className="text-[11px] font-mono px-1.5 py-0.5 border rounded-sm" style={{ color: '#4A443A', borderColor: '#C9C0AE' }}>{s}</span>
                  ))}
                </div>
                <div className="mt-2 text-[11px] font-mono" style={{ color: '#8E8160' }}>
                  cadence: scan 60 min · learn 15 min · digest 07:30 UTC
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: '1', label: 'course', sub: 'agent-ops' },
                  { value: '6', label: 'lessons', sub: 'full version history' },
                  { value: '7/8', label: 'consented', sub: 'fixture cohort, labelled' },
                  { value: 'sim', label: 'hero run mode', sub: 'fixtures · no model calls · no mail' },
                ].map(s => (
                  <div key={s.label} className="p-3 border rounded-sm text-center" style={{ borderColor: '#C9C0AE', backgroundColor: '#F3EFE7' }}>
                    <div className="text-xl font-semibold font-mono" style={{ color: '#1C1915' }}>{s.value}</div>
                    <div className="text-[10px] font-mono uppercase tracking-wide mt-0.5" style={{ color: '#6B4E2E' }}>{s.label}</div>
                    <div className="text-[9px] mt-0.5" style={{ color: '#68604F' }}>{s.sub}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Quick stats — register numbers (RECEIPTS.md), receipts only */}
          <div className="mb-10">
            <div className="text-[11px] font-mono uppercase tracking-widest mb-4" style={{ color: '#8E8160' }}>
              Live numbers (receipts only, not assertions)
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { value: '274', label: 'checks green', sub: '13 stages · audit 32/32 · no credentials' },
                { value: '1', label: 'course live', sub: 'agent-ops · 6 lessons' },
                { value: '7/8', label: 'consented cohort', sub: 'fixture cohort, one declined by design' },
                { value: '59', label: 'parity rows', sub: 'oracle ↔ n8n node · action match 1.000' },
              ].map(s => (
                <div key={s.label} className="p-4 border rounded-sm text-center" style={{ borderColor: '#C9C0AE', backgroundColor: '#F3EFE7' }}>
                  <div className="text-3xl font-semibold font-mono mb-1" style={{ color: '#1C1915' }}>{s.value}</div>
                  <div className="text-[11px] font-mono uppercase tracking-wide" style={{ color: '#6B4E2E' }}>{s.label}</div>
                  <div className="text-[10px] mt-1" style={{ color: '#68604F' }}>{s.sub}</div>
                </div>
              ))}
            </div>
          </div>

      {/* Live loop status + learner card side by side */}
      <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <div className="text-[11px] font-mono uppercase tracking-widest mb-2" style={{ color: '#8E8160' }}>Loop status — the recorded cycle</div>
          <LiveLoopBadge />
        </div>
        <div>
          <div className="text-[11px] font-mono uppercase tracking-widest mb-2" style={{ color: '#8E8160' }}>Learner card — staged, consented fixture cohort</div>
          <div className="border rounded-sm p-4" style={{ borderColor: '#8E8160', backgroundColor: '#EAE4D8' }}>
            <pre className="text-xs font-mono leading-relaxed whitespace-pre-wrap" style={{ color: '#1C1915' }}>
{stagedCard}
            </pre>
            <div className="flex gap-3 mt-3">
              <button className="text-[11px] font-mono px-3 py-1.5 border rounded-sm" style={{ borderColor: '#6B4E2E', color: '#6B4E2E' }}>
                See the diff
              </button>
              <button className="text-[11px] font-mono px-3 py-1.5 border rounded-sm" style={{ borderColor: '#8E8160', color: '#8E8160' }}>
                Stop these messages
              </button>
            </div>
            <div className="text-[10px] font-mono mt-2" style={{ color: '#68604F' }}>
              staged, not sent (mode: sim — no mail leaves the box). Cards carry opt-out in every copy.
            </div>
          </div>
        </div>
      </div>

          {/* CTA row */}
      <div className="flex flex-wrap gap-3">
        {[
          { id: 'slides' as Section, label: '→ Read the 4-slide deck', sub: 'Why · How · Safeguards · Vision' },
          { id: 'workflow' as Section, label: '→ Walk the 5 run views', sub: 'Publish · First scan · Hostile · Stuck · Human signoff + revert' },
          { id: 'courses' as Section, label: '→ Browse agent-ops', sub: '6 lessons · real diffs · real quizzes' },
          { id: 'console' as Section, label: '→ Open author console', sub: 'Real receipts · verbatim digest · chain integrity' },
        ].map(btn => (
          <button
            key={btn.id}
            onClick={() => onNavigate(btn.id)}
            className="flex-1 min-w-[200px] text-left p-4 border rounded-sm transition-all hover:bg-white/40"
            style={{ borderColor: '#8E8160', backgroundColor: '#F3EFE7', color: '#1C1915' }}
          >
            <div className="text-sm font-semibold" style={{ color: '#6B4E2E' }}>{btn.label}</div>
            <div className="text-xs mt-0.5" style={{ color: '#68604F' }}>{btn.sub}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Courses page ─────────────────────────────────────────────────────────────
// (former CoursesPage — course tabs + ProgressionChart + CourseView — replaced by the
//  three-level CoursesSection adapted from the Next.js variant; see components/CoursesSection.tsx)

// ─── App ───────────────────────────────────────────────────────────────────────
export default function App() {
  const [section, setSection] = useState<Section>('overview');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const sectionTitles: Record<Section, string> = {
    overview: 'Overview',
    slides: 'Deck — 4 slides',
    workflow: 'Workflow Runs (5 live)',
    courses: 'Courses & Lessons',
    console: 'Author Console',
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#F3EFE7', fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
      {/* Top bar */}
      <div className="sticky top-0 z-40 border-b" style={{ borderColor: '#8E8160', backgroundColor: '#EAE4D8' }}>
        <div className="max-w-[1400px] mx-auto px-4 py-3 flex items-center gap-4">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-sm font-mono p-1 rounded-sm hover:bg-white/30 transition-colors"
            style={{ color: '#6B4E2E' }}
            aria-label="Toggle sidebar"
          >
            ☰
          </button>
          <div className="flex items-center gap-3">
            <span className="text-base font-semibold" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
              CourseRefresh
            </span>
            <span className="text-[11px] font-mono hidden md:block" style={{ color: '#8E8160' }}>
              The course that rewrites itself
            </span>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[10px] font-mono px-2 py-1 border rounded-sm" style={{ color: '#96550A', borderColor: '#96550A', backgroundColor: '#F7EFE4' }}>
              hero run: sim
            </span>
            <span className="text-[10px] font-mono px-2 py-1 border rounded-sm" style={{ color: '#3F5A2A', borderColor: '#3F5A2A', backgroundColor: '#EBF2E2' }}>
              chain ✓ 9 rows
            </span>
            <span className="text-[10px] font-mono px-2 py-1 border rounded-sm hidden md:block" style={{ color: '#5C564C', borderColor: '#8E8160' }}>
              hostile→publish: 0
            </span>
          </div>
        </div>
        {/* Section breadcrumb */}
        <div className="max-w-[1400px] mx-auto px-4 py-1.5 flex items-center gap-2">
          <span className="text-[11px] font-mono" style={{ color: '#8E8160' }}>
            courserefresh / {sectionTitles[section]}
          </span>
        </div>
      </div>

      <div className="max-w-[1400px] mx-auto px-4 py-6 flex gap-6">
        {/* Sidebar nav */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.aside
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 220, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex-shrink-0 overflow-hidden"
            >
              <div className="w-[220px]">
                <div className="text-[10px] font-mono uppercase tracking-widest mb-3" style={{ color: '#8E8160' }}>
                  Navigation
                </div>
                <nav className="space-y-1">
                  {nav.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setSection(item.id)}
                      className="w-full text-left px-3 py-2.5 rounded-sm border transition-all"
                      style={{
                        borderColor: section === item.id ? '#6B4E2E' : 'transparent',
                        backgroundColor: section === item.id ? '#EDE6D8' : 'transparent',
                        borderLeft: section === item.id ? '3px solid #6B4E2E' : '3px solid transparent',
                      }}
                    >
                      <div className="text-sm font-semibold" style={{ color: section === item.id ? '#6B4E2E' : '#1C1915' }}>
                        {item.label}
                      </div>
                      <div className="text-[11px] mt-0.5" style={{ color: '#8E8160' }}>{item.sub}</div>
                    </button>
                  ))}
                </nav>

                {/* Authority ladder */}
                <div className="mt-6 pt-4 border-t" style={{ borderColor: '#C9C0AE' }}>
                  <div className="text-[10px] font-mono uppercase tracking-widest mb-3" style={{ color: '#8E8160' }}>
                    Authority ladder
                  </div>
                  {[
                    { level: 'PA0', desc: 'Draft only', color: '#5C564C', bg: '#EEEBE4' },
                    { level: 'PA1', desc: 'Act, don’t notify', color: '#96550A', bg: '#F7EFE4' },
                    { level: 'PA2', desc: 'Act + notify affected', color: '#3F5A2A', bg: '#EBF2E2', current: true },
                    { level: 'PA3', desc: 'Human only (assessments, records)', color: '#9B2C1F', bg: '#F5E8E6' },
                  ].map(l => (
                    <div key={l.level} className="flex items-center gap-2 mb-1.5">
                      <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded-sm border" style={{ color: l.color, backgroundColor: l.bg, borderColor: l.color }}>
                        {l.level}
                      </span>
                      <span className="text-[11px]" style={{ color: '#4A443A' }}>{l.desc}</span>
                      {l.current && <span className="text-[10px] font-mono" style={{ color: '#3F5A2A' }}>← now</span>}
                    </div>
                  ))}
                </div>

                {/* Budget */}
                <div className="mt-4 pt-4 border-t" style={{ borderColor: '#C9C0AE' }}>
                  <div className="text-[10px] font-mono uppercase tracking-widest mb-2" style={{ color: '#8E8160' }}>
                    Budget today
                  </div>
                  <div className="space-y-2">
                    {[
                      { label: 'Apify units', used: 0, max: 25, note: 'unmeasured (sim)' },
                      { label: 'Publishes', used: 2, max: 6 },
                      { label: 'Tokens', used: 0, max: 500, note: 'unmeasured (sim)' },
                    ].map(b => (
                      <div key={b.label}>
                        <div className="flex justify-between text-[10px] font-mono mb-0.5" style={{ color: '#8E8160' }}>
                          <span>{b.label}</span>
                          <span>{b.used}/{b.max}{b.note ? ` · ${b.note}` : ''}</span>
                        </div>
                        <div className="h-1 rounded-full overflow-hidden" style={{ backgroundColor: '#C9C0AE' }}>
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${b.used / b.max * 100}%`,
                              backgroundColor: b.used / b.max > 0.8 ? '#9B2C1F' : '#3F5A2A',
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={section}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -16 }}
              transition={{ duration: 0.25 }}
            >
              {section === 'overview' && <OverviewPage onNavigate={setSection} />}
              {section === 'slides' && (
                <div>
                  <div className="mb-4">
                    <h2 className="text-2xl font-semibold" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
                      Four-slide deck
                    </h2>
                    <p className="text-sm mt-1" style={{ color: '#68604F' }}>
                      Why CourseRefresh matters · How it works · Why you can trust it · The university of the future
                    </p>
                  </div>
                  <PresentationSlides />
                </div>
              )}
              {section === 'workflow' && (
                <div>
                  <div className="mb-4">
                    <h2 className="text-2xl font-semibold" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
                      Workflow runs — 5 views of the recorded cycle
                    </h2>
                    <p className="text-sm mt-1" style={{ color: '#68604F' }}>
                      Each view animates the recorded Notice → Verify → Decide → Act → Learn → Report cycle from the real receipts and run logs. Click any event row to expand. “Replay loop” animates the presentation; the runs themselves are recorded artifacts, not a live feed.
                    </p>
                  </div>
                  <WorkflowVisualizer />
                </div>
              )}
              {section === 'courses' && (
                <div>
                  <div className="mb-4">
                    <h2 className="text-2xl font-semibold" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
                      Course Catalogue
                    </h2>
                    <p className="text-sm mt-1" style={{ color: '#68604F' }}>
                      Course catalogue → course → lesson, each with its version history, real diffs and the quizzes as shipped. The agent-ops course is the repo's real six-lesson course; ml-engineering and web-security are demo catalog entries. Cohort scores are <span className="font-mono">unmeasured</span> until a consented live cohort runs; the system prints <span className="font-mono">unmeasured</span> rather than guessing.
                    </p>
                  </div>
                  <CoursesSection />
                </div>
              )}
              {section === 'console' && (
                <div>
                  <div className="mb-4">
                    <h2 className="text-2xl font-semibold" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
                      Author console
                    </h2>
                    <p className="text-sm mt-1" style={{ color: '#68604F' }}>
                      Instrument view — digest, receipts, chain integrity. Refusals listed first. Every number links to a receipt. Paper and ink, not dashboard.
                    </p>
                  </div>
                  <AuthorConsole />
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* Footer */}
      <footer className="border-t mt-12 px-6 py-6" style={{ borderColor: '#C9C0AE', backgroundColor: '#EAE4D8' }}>
        <div className="max-w-[1400px] mx-auto flex flex-wrap justify-between gap-4 text-[11px] font-mono" style={{ color: '#8E8160' }}>
          <div>
            CourseRefresh · <em style={{ fontFamily: "'Source Serif 4', Georgia, serif" }}>The course that rewrites itself</em> · presentation layer over real artifacts
          </div>
          <div className="flex gap-4 flex-wrap">
            <span>specs/constitution.md Art. II, III, VIII, XI</span>
            <span>design/MASTER.md — paper and ink</span>
            <span>hostile→publish: 0 (build-breaking)</span>
          </div>
          <div>
            Dates in YYYY.MM.DD · Times UTC · Numbers sourced from receipts only
          </div>
        </div>
      </footer>
    </div>
  );
}
