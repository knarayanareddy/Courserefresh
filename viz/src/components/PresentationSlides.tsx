import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';

// The 4-slide narrative: the teacher's problem, not an AI-churn story.
// Every number is either receipt-backed or explicitly labeled as metaphor.
// Slides are loosely typed on purpose: shapes differ per slide type.

const slides: any[] = [
  {
    id: 1,
    type: 'title',
    bg: 'from-[#F3EFE7] to-[#EAE4D8]',
    label: '01 / 05',
    eyebrow: 'CourseRefresh',
    title: 'A course that keeps itself true.',
    body:
      'AI changes every week, but the courses teaching the next generation are updated once a year — students learn yesterday\u2019s truth from lecturers who have no time to keep up.',
  },
  {
    id: 3,
    type: 'who-pays',
    bg: 'from-[#EAE4D8] to-[#F3EFE7]',
    label: '02 / 05',
    eyebrow: 'Who pays for the drift',
    title: 'Everyone in the room pays — in a different currency.',
    body: 'Stale material is not a victimless lag. Each seat in the lecture hall pays for it differently.',
    payers: [
      { who: 'The lecturer', pays: 'Unpaid upkeep: tracking releases, verifying claims, rewriting lessons on top of teaching, research, and admin. The work never shows up in a workload model.' },
      { who: 'The student', pays: 'Yesterday\u2019s truth: settings that were renamed, APIs that were removed, practices already flagged as unsafe — discovered in the lab, or on the job.' },
      { who: 'The institution', pays: 'Erosion: course reviews flag stale material every cycle; accreditation asks for currency; employers quietly discount the degree.' },
    ],
  },
  {
    id: 4,
    type: 'why',
    bg: 'from-[#F3EFE7] to-[#EAE4D8]',
    label: '03 / 05',
    eyebrow: 'Why this solution',
    title: 'A chatbot watches. An alert feed watches. This acts.',
    body: 'Everything else on the shelf observes; none of it takes responsibility for the course being correct. The gap is not awareness — it is accountable, evidenced action.',
    rivals: [
      { who: 'A chatbot', gap: 'passive', sees: 'Answers questions when asked.', does: 'Retells the course as written — including its mistakes. Rewrites nothing.' },
      { who: 'An alert feed', gap: 'delegates back', sees: 'Pings the lecturer when something looks relevant.', does: 'Adds one more notification to an overloaded human. The queue grows; the course still rots.' },
      { who: 'CourseRefresh', gap: 'accountable action', sees: 'Watches the sources itself, every hour.', does: 'Verifies, decides by rulebook, rewrites the lesson and quiz, notifies learners, measures the effect, and undoes its own bad edits.' },
    ],
    kicker: 'Only the last one closes the loop — and every action carries a receipt.',
  },
  {
    id: 5,
    type: 'how',
    bg: 'from-[#EAE4D8] to-[#F3EFE7]',
    label: '04 / 05',
    eyebrow: 'How it works',
    title: 'Five steps, closing hourly. Each step is a real tool.',
    body: 'The loop is small enough to explain in one breath and specific enough to audit in one afternoon.',
    phases: [
      { name: 'WATCH', tool: 'Apify', color: '#6B4E2E', desc: 'Actors fetch the sources the course teaches — releases, docs, changelogs — every 60 minutes. Snapshots are hashed; unchanged sources produce no event.' },
      { name: 'FIND LEADS', tool: 'Tavily', color: '#96550A', desc: 'Search finds leads when a watched source is quiet. A lead is a candidate, never proof: its page must be fetched from its own publisher before it can count.' },
      { name: 'JUDGE', tool: 'LLM + rulebook', color: '#7A5C00', desc: 'A judge model scores each candidate against the closed rubric: relevance, agreement, quote support, injection risk. The judge proposes; the rulebook decides.' },
      { name: 'DECIDE + ACT', tool: 'n8n', color: '#3F5A2A', desc: 'The POLICY node — deterministic, one screen — returns one action with reason codes, then writes the versioned lesson, diff, quiz, and CHANGELOG commit.' },
      { name: 'REPORT', tool: 'digest', color: '#5C564C', desc: 'The teacher gets one digest: refusals first, then what changed, with receipts and undo. Consenting learners get a card with one-click opt-out.' },
    ],
  },
  {
    id: 10,
    type: 'close',
    bg: 'from-[#F3EFE7] to-[#EAE4D8]',
    label: '05 / 05',
    eyebrow: 'The close',
    title: 'Students learn what\u2019s true today. Teachers stay in charge.',
    body: 'CourseRefresh takes the untracked labour off the lecturer\u2019s desk and puts receipts in its place. Teachers keep the authority that matters: what is taught, to whom, and when to say stop.',
    quiet: [
      { icon: '\u00a7', text: 'Assessments, learner records, and grade-affecting changes are human-only. Permanently. PA3 in the authority ladder.' },
      { icon: '\u25ce', text: 'Learners hear nothing without recorded consent, capped at 1/day and 3/week — and every card carries opt-out.' },
      { icon: '\u21ba', text: 'Every publish is reversible; the revert gate does not care whose edit it was — including a human\u2019s signoff.' },
    ],
  },
];

export default function PresentationSlides() {
  const [current, setCurrent] = useState(0);
  const [direction, setDirection] = useState(1);

  const go = (dir: number) => {
    setDirection(dir);
    setCurrent((c) => Math.max(0, Math.min(slides.length - 1, c + dir)));
  };

  const slide = slides[current];

  return (
    <div className="relative w-full" style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
      {/* Slide container */}
      <div className="relative overflow-hidden rounded-sm border" style={{ borderColor: '#8E8160', minHeight: 520 }}>
        <AnimatePresence mode="wait" custom={direction}>
          <motion.div
            key={slide.id}
            custom={direction}
            initial={{ opacity: 0, x: direction * 60 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: direction * -60 }}
            transition={{ duration: 0.35, ease: 'easeInOut' }}
            className={`w-full bg-gradient-to-br ${slide.bg} p-8 md:p-12`}
            style={{ minHeight: 520 }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-6">
              <div>
                <span className="text-[11px] font-mono tracking-widest uppercase" style={{ color: '#8E8160' }}>
                  {slide.eyebrow}
                </span>
                <div className="mt-1 text-[11px] font-mono" style={{ color: '#68604F' }}>CourseRefresh · {slide.label}</div>
              </div>
              <span className="text-[10px] font-mono tracking-widest uppercase px-2 py-1 border rounded-sm" style={{ color: '#8E8160', borderColor: '#8E8160' }}>
                UNIVERSITY DEMO
              </span>
            </div>

            {/* Title + body */}
            <h2 className="text-2xl md:text-3xl font-semibold leading-tight mb-4" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif", maxWidth: '52ch' }}>
              {slide.title}
            </h2>
            <p className="text-base leading-relaxed mb-8" style={{ color: '#4A443A', maxWidth: '68ch' }}>
              {slide.body}
            </p>

            {/* Slide-specific content */}
            {slide.type === 'who-pays' && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {slide.payers.map((p: any, i: number) => (
                  <div key={i} className="p-4 rounded-sm border" style={{ borderColor: '#8E8160', backgroundColor: 'rgba(255,255,255,0.4)' }}>
                    <div className="text-sm font-semibold mb-1" style={{ color: '#1C1915' }}>{p.who}</div>
                    <div className="text-xs leading-relaxed" style={{ color: '#4A443A' }}>{p.pays}</div>
                  </div>
                ))}
              </div>
            )}

            {slide.type === 'why' && (
              <div className="space-y-3">
                {slide.rivals.map((r: any, i: number) => (
                  <div
                    key={i}
                    className="flex gap-3 items-start p-3 rounded-sm border"
                    style={{
                      borderColor: r.who === 'CourseRefresh' ? '#6B4E2E' : '#C9C0AE',
                      backgroundColor: r.who === 'CourseRefresh' ? 'rgba(235,242,226,0.6)' : 'rgba(255,255,255,0.35)',
                    }}
                  >
                    <div className="w-36 flex-shrink-0">
                      <div className="text-xs font-semibold font-mono" style={{ color: r.who === 'CourseRefresh' ? '#3F5A2A' : '#4A443A' }}>{r.who}</div>
                      <div className="text-[10px] font-mono uppercase" style={{ color: '#8E8160' }}>{r.gap}</div>
                    </div>
                    <div>
                      <div className="text-xs" style={{ color: '#4A443A' }}>{r.sees}</div>
                      <div className="text-xs mt-0.5" style={{ color: '#68604F' }}>{r.does}</div>
                    </div>
                  </div>
                ))}
                <div className="text-xs font-mono px-3 py-2 border-l-2" style={{ borderColor: '#96550A', color: '#96550A' }}>
                  {slide.kicker}
                </div>
              </div>
            )}

            {slide.type === 'how' && (
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {slide.phases.map((ph: any, i: number) => (
                  <div key={i} className="p-3 rounded-sm border" style={{ borderColor: '#8E8160', backgroundColor: 'rgba(255,255,255,0.4)' }}>
                    <div className="text-[11px] font-mono font-semibold tracking-widest uppercase mb-1" style={{ color: ph.color }}>{ph.name}</div>
                    <div className="text-[10px] font-mono mb-1" style={{ color: '#96550A' }}>{ph.tool}</div>
                    <div className="text-xs leading-relaxed" style={{ color: '#4A443A' }}>{ph.desc}</div>
                  </div>
                ))}
              </div>
            )}

            {slide.type === 'close' && (
              <div className="space-y-3">
                {slide.quiet.map((p: any, i: number) => (
                  <div key={i} className="flex gap-3 items-start">
                    <span className="mt-0.5 text-xs font-mono flex-shrink-0" style={{ color: '#6B4E2E' }}>{p.icon}</span>
                    <span className="text-sm leading-relaxed" style={{ color: '#4A443A' }}>{p.text}</span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between mt-4">
        <button
          onClick={() => go(-1)}
          disabled={current === 0}
          className="flex items-center gap-1 px-4 py-2 text-sm font-mono border rounded-sm transition-opacity disabled:opacity-30"
          style={{ borderColor: '#8E8160', color: '#4A443A', backgroundColor: '#F3EFE7' }}
        >
          <ChevronLeft size={14} /> Prev
        </button>

        <div className="flex gap-2 flex-wrap justify-center">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => { setDirection(i > current ? 1 : -1); setCurrent(i); }}
              className="w-2 h-2 rounded-full transition-all"
              style={{ backgroundColor: i === current ? '#6B4E2E' : '#C9C0AE' }}
            />
          ))}
        </div>

        <button
          onClick={() => go(1)}
          disabled={current === slides.length - 1}
          className="flex items-center gap-1 px-4 py-2 text-sm font-mono border rounded-sm transition-opacity disabled:opacity-30"
          style={{ borderColor: '#8E8160', color: '#4A443A', backgroundColor: '#F3EFE7' }}
        >
          Next <ChevronRight size={14} />
        </button>
      </div>
    </div>
  );
}
