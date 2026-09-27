import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Lesson, LessonVersion } from '../data/mockData';
import StatusBadge, { AuthorityBadge } from './StatusBadge';

function DiffBlock({ version }: { version: LessonVersion }) {
  if (!version.diffAdded?.length && !version.diffRemoved?.length) return null;
  return (
    <div className="border rounded-sm overflow-hidden mt-3" style={{ borderColor: '#8E8160' }}>
      <div className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-widest" style={{ color: '#8E8160', backgroundColor: '#EAE4D8' }}>
        diff — v{version.version - 1} → v{version.version}
      </div>
      <div className="p-3 font-mono text-xs leading-relaxed space-y-1" style={{ backgroundColor: '#F3EFE7' }}>
        {version.diffRemoved?.map((line, i) => (
          <div key={`r-${i}`} className="flex gap-2">
            <span className="flex-shrink-0 select-none font-bold" style={{ color: '#9B2C1F' }}>−</span>
            <span style={{ color: '#9B2C1F', textDecoration: 'line-through', opacity: 0.8 }}>{line}</span>
          </div>
        ))}
        {version.diffAdded?.map((line, i) => (
          <div key={`a-${i}`} className="flex gap-2">
            <span className="flex-shrink-0 select-none font-bold" style={{ color: '#3F5A2A' }}>+</span>
            <span style={{ color: '#3F5A2A' }}>{line}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function VersionCard({ version, isCurrent }: { version: LessonVersion; isCurrent: boolean }) {
  const [open, setOpen] = useState(isCurrent);

  return (
    <div
      className="border rounded-sm overflow-hidden"
      style={{
        borderColor: isCurrent ? '#6B4E2E' : '#C9C0AE',
        backgroundColor: isCurrent ? '#EDE6D8' : '#F3EFE7',
      }}
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-white/20"
      >
        <span className="text-sm font-mono font-semibold" style={{ color: '#1C1915' }}>v{version.version}</span>
        <span className="text-[11px] font-mono" style={{ color: '#8E8160' }}>{version.date}</span>
        <div className="ml-auto flex items-center gap-2">
          <AuthorityBadge level={version.authority} />
          <StatusBadge status={version.status} />
          {isCurrent && (
            <span className="text-[10px] font-mono px-2 py-0.5 border rounded-sm" style={{ color: '#6B4E2E', borderColor: '#6B4E2E', backgroundColor: '#EBF2E2' }}>
              CURRENT
            </span>
          )}
          <span className="text-xs font-mono" style={{ color: '#8E8160' }}>{open ? '▲' : '▼'}</span>
        </div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 border-t" style={{ borderColor: '#C9C0AE' }}>
              {version.changeReason && (
                <div className="mt-3 px-3 py-2 rounded-sm text-xs leading-relaxed border-l-2"
                  style={{ backgroundColor: 'rgba(197,162,2,.12)', borderColor: '#96550A', color: '#4A443A', fontFamily: "'Source Serif 4', Georgia, serif" }}>
                  <span className="text-[10px] font-mono font-semibold uppercase tracking-wide block mb-1" style={{ color: '#96550A', fontFamily: "'IBM Plex Sans', sans-serif" }}>Why this changed</span>
                  {version.changeReason}
                </div>
              )}

              <div className="mt-3 text-sm leading-relaxed" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif", maxWidth: '68ch' }}>
                {version.body}
              </div>

              <DiffBlock version={version} />

              {(version.quizScoreBefore !== undefined || version.quizScoreAfter !== undefined) && (
                <div className="mt-3 flex gap-6">
                  {version.quizScoreBefore !== undefined && (
                    <div>
                      <div className="text-[10px] font-mono uppercase tracking-wide" style={{ color: '#9B2C1F' }}>Before</div>
                      <div className="text-lg font-semibold font-mono" style={{ color: '#9B2C1F' }}>{version.quizScoreBefore}%</div>
                    </div>
                  )}
                  {version.quizScoreAfter !== undefined && (
                    <>
                      <div className="flex items-end pb-1 font-mono text-lg" style={{ color: '#8E8160' }}>→</div>
                      <div>
                        <div className="text-[10px] font-mono uppercase tracking-wide" style={{ color: '#3F5A2A' }}>After</div>
                        <div className="text-lg font-semibold font-mono" style={{ color: '#3F5A2A' }}>{version.quizScoreAfter}%</div>
                      </div>
                      <div className="flex items-end pb-1">
                        <span className="text-sm font-mono font-semibold px-2 py-0.5 rounded-sm" style={{ color: '#3F5A2A', backgroundColor: '#EBF2E2' }}>
                          +{version.quizScoreAfter - version.quizScoreBefore!}pp
                        </span>
                      </div>
                    </>
                  )}
                </div>
              )}

              {version.sources && (
                <div className="mt-3 text-[11px] font-sans" style={{ color: '#68604F' }}>
                  <span className="font-mono uppercase tracking-wide">sources: </span>
                  {version.sources.join(' · ')}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function QuizCard({ q }: { q: { id: string; question: string; options: string[]; correct: number; version: number; changedReason?: string } }) {
  const [selected, setSelected] = useState<number | null>(null);

  return (
    <div className="border rounded-sm overflow-hidden" style={{ borderColor: '#C9C0AE', backgroundColor: '#F3EFE7' }}>
      <div className="px-4 py-3">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[10px] font-mono uppercase tracking-wide" style={{ color: '#8E8160' }}>v{q.version}</span>
          {q.changedReason && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 border rounded-sm" style={{ color: '#96550A', borderColor: '#96550A', backgroundColor: '#F7EFE4' }}>
              UPDATED
            </span>
          )}
        </div>
        <p className="text-sm font-semibold mb-3" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>{q.question}</p>
        <div className="space-y-2">
          {q.options.map((opt, i) => {
            const isCorrect = i === q.correct;
            const isSelected = selected === i;
            let bg = 'transparent';
            let border = '#C9C0AE';
            let color = '#4A443A';
            if (isSelected && isCorrect) { bg = '#EBF2E2'; border = '#3F5A2A'; color = '#3F5A2A'; }
            else if (isSelected && !isCorrect) { bg = '#F5E8E6'; border = '#9B2C1F'; color = '#9B2C1F'; }
            return (
              <button
                key={i}
                onClick={() => setSelected(i)}
                className="w-full text-left px-3 py-2 rounded-sm border text-xs transition-all hover:bg-white/40"
                style={{ backgroundColor: bg, borderColor: border, color }}
              >
                <span className="font-mono mr-2" style={{ color: '#8E8160' }}>{String.fromCharCode(65 + i)}.</span>
                {opt}
              </button>
            );
          })}
        </div>
        {selected !== null && q.changedReason && (
          <div className="mt-2 text-[11px] leading-relaxed px-2 py-1.5 rounded-sm border-l-2" style={{ borderColor: '#96550A', backgroundColor: 'rgba(197,162,2,.10)', color: '#68604F' }}>
            Why this changed: {q.changedReason}
          </div>
        )}
      </div>
    </div>
  );
}

export default function LessonViewer({ lesson }: { lesson: Lesson }) {
  const [tab, setTab] = useState<'lesson' | 'history' | 'quiz' | 'compare'>('lesson');

  const current = lesson.versions[lesson.versions.length - 1]; // real version histories are sparse (e.g. v3,v4,v5)
  const progressPct = Math.round((lesson.totalLearners - lesson.stuckLearners) / lesson.totalLearners * 100);

  return (
    <div className="border rounded-sm overflow-hidden" style={{ borderColor: '#8E8160', backgroundColor: '#F3EFE7', fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
      {/* Header */}
      <div className="px-5 py-4 border-b" style={{ borderColor: '#C9C0AE', backgroundColor: '#EAE4D8' }}>
        <div className="flex flex-wrap items-start gap-3 justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-mono px-2 py-0.5 border rounded-sm" style={{ color: '#6B4E2E', borderColor: '#6B4E2E', backgroundColor: '#F3EFE7' }}>
                {lesson.id}
              </span>
              <span className="text-[11px] font-mono" style={{ color: '#8E8160' }}>{lesson.duration}</span>
              <StatusBadge status={current?.status || 'PUBLISHED'} />
            </div>
            <h3 className="text-lg font-semibold" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
              {lesson.number}. {lesson.title}
            </h3>
            <p className="text-xs mt-0.5" style={{ color: '#68604F' }}>{lesson.subtitle}</p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <div className="text-sm font-mono font-semibold" style={{ color: '#1C1915' }}>v{lesson.currentVersion}</div>
            <div className="text-[11px] font-mono" style={{ color: '#68604F' }}>{lesson.versions.length} version{lesson.versions.length !== 1 ? 's' : ''} kept</div>
          </div>
        </div>

        {/* Learner stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div>
            <div className="text-[11px] font-mono uppercase tracking-wide" style={{ color: '#8E8160' }}>Learners</div>
            <div className="text-base font-semibold font-mono" style={{ color: '#1C1915' }}>{lesson.totalLearners}</div>
          </div>
          <div>
            <div className="text-[11px] font-mono uppercase tracking-wide" style={{ color: '#8E8160' }}>Stuck</div>
            <div className="text-base font-semibold font-mono" style={{ color: lesson.stuckLearners > 0 ? '#9B2C1F' : '#5C564C' }}>{lesson.stuckLearners}</div>
          </div>
          <div>
            <div className="text-[11px] font-mono uppercase tracking-wide" style={{ color: '#8E8160' }}>Cohort quiz delta</div>
            <div className="text-base font-semibold font-mono" style={{ color: '#7A5C00' }}>
              {lesson.avgQuizScore !== undefined ? `${lesson.avgQuizScore}%` : 'unmeasured'}
            </div>
          </div>
        </div>

        {/* Consent/privacy note */}
        <div className="mt-2 text-[10px] font-mono" style={{ color: '#8E8160' }}>
          cohort is the consented fixture cohort (7/8) — quiz_delta prints unmeasured until a consented live cohort runs (spec §6, Art. VII legal degrade)
        </div>

        {/* Progress bar */}
        <div className="mt-3">
          <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: '#C9C0AE' }}>
            <div className="h-full rounded-full transition-all" style={{ width: `${progressPct}%`, backgroundColor: '#3F5A2A' }} />
          </div>
          <div className="text-[10px] font-mono mt-0.5" style={{ color: '#8E8160' }}>{progressPct}% learners not stuck</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b" style={{ borderColor: '#C9C0AE' }}>
        {(['lesson', 'history', 'quiz', 'compare'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="flex-1 px-4 py-2.5 text-[11px] font-mono uppercase tracking-widest transition-all"
            style={{
              color: tab === t ? '#6B4E2E' : '#8E8160',
              backgroundColor: tab === t ? '#F3EFE7' : '#EAE4D8',
              borderBottom: tab === t ? '2px solid #6B4E2E' : '2px solid transparent',
            }}
          >
            {t === 'lesson' ? 'Current lesson' : t === 'history' ? `History (${lesson.versions.length})` : t === 'quiz' ? `Quiz (${lesson.quiz.length})` : 'Before vs After'}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-5">
        <AnimatePresence mode="wait">
          {tab === 'lesson' && (
            <motion.div key="lesson" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {/* Objectives */}
              <div className="mb-5">
                <div className="text-[11px] font-mono uppercase tracking-widest mb-2" style={{ color: '#8E8160' }}>Learning objectives</div>
                <ul className="space-y-1">
                  {lesson.objectives.map((obj, i) => (
                    <li key={i} className="flex gap-2 items-start text-sm" style={{ color: '#4A443A' }}>
                      <span className="flex-shrink-0 font-mono text-xs mt-0.5" style={{ color: '#6B4E2E' }}>○</span>
                      {obj}
                    </li>
                  ))}
                </ul>
              </div>
              {/* Current version body */}
              <div className="text-sm leading-relaxed p-4 rounded-sm border" style={{ fontFamily: "'Source Serif 4', Georgia, serif", color: '#1C1915', borderColor: '#C9C0AE', backgroundColor: '#EAE4D8', maxWidth: '68ch' }}>
                {current?.body}
              </div>
              {/* Sources */}
              {current?.sources && (
                <div className="mt-3 text-[11px]" style={{ color: '#68604F' }}>
                  <span className="font-mono uppercase tracking-wide">sources: </span>
                  {current.sources.join(' · ')}
                </div>
              )}
            </motion.div>
          )}

          {tab === 'history' && (
            <motion.div key="history" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
              {[...lesson.versions].reverse().map((v) => (
                <VersionCard key={v.version} version={v} isCurrent={v.version === lesson.currentVersion} />
              ))}
            </motion.div>
          )}

          {tab === 'quiz' && (
            <motion.div key="quiz" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
              {lesson.quiz.map((q) => (
                <QuizCard key={q.id} q={q} />
              ))}
            </motion.div>
          )}

          {tab === 'compare' && (
            <motion.div key="compare" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {lesson.versions.length < 2 ? (
                <div className="text-sm" style={{ color: '#68604F' }}>Only one version — no comparison available yet.</div>
              ) : (
                <div className="space-y-4">
                  <div className="text-[11px] font-mono uppercase tracking-widest mb-3" style={{ color: '#8E8160' }}>
                    Side-by-side — v{lesson.versions[0].version} (original) vs v{lesson.currentVersion} (current)
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Before */}
                    <div className="border rounded-sm overflow-hidden" style={{ borderColor: '#9B2C1F' }}>
                      <div className="px-3 py-2 text-[10px] font-mono font-bold uppercase tracking-widest" style={{ color: '#9B2C1F', backgroundColor: '#F5E8E6' }}>
                        v{lesson.versions[0].version} — {lesson.versions[0].date}
                      </div>
                      <div className="p-3 text-xs leading-relaxed" style={{ color: '#4A443A', fontFamily: "'Source Serif 4', Georgia, serif", backgroundColor: '#F3EFE7' }}>
                        {lesson.versions[0].body}
                      </div>
                      <div className="px-3 py-2 border-t text-[10px] font-mono" style={{ borderColor: '#C9C0AE', color: '#68604F' }}>
                        sources: {lesson.versions[0].sources?.join(' · ') || 'n/a'}
                      </div>
                    </div>
                    {/* After */}
                    <div className="border rounded-sm overflow-hidden" style={{ borderColor: '#3F5A2A' }}>
                      <div className="px-3 py-2 text-[10px] font-mono font-bold uppercase tracking-widest" style={{ color: '#3F5A2A', backgroundColor: '#EBF2E2' }}>
                        v{current?.version} — {current?.date} (current)
                      </div>
                      <div className="p-3 text-xs leading-relaxed" style={{ color: '#4A443A', fontFamily: "'Source Serif 4', Georgia, serif", backgroundColor: '#F3EFE7' }}>
                        {current?.body}
                      </div>
                      <div className="px-3 py-2 border-t text-[10px] font-mono" style={{ borderColor: '#C9C0AE', color: '#68604F' }}>
                        sources: {current?.sources?.join(' · ') || 'n/a'}
                      </div>
                    </div>
                  </div>
                  {/* Score delta */}
                  {lesson.versions.some(v => v.quizScoreAfter) && (
                    <div className="p-4 border rounded-sm" style={{ borderColor: '#C9C0AE', backgroundColor: '#EAE4D8' }}>
                      <div className="text-[11px] font-mono uppercase tracking-widest mb-3" style={{ color: '#8E8160' }}>
                        Quiz score trajectory
                      </div>
                      <div className="flex items-center gap-4 flex-wrap">
                        {lesson.versions.filter(v => v.quizScoreAfter).map((v, i) => (
                          <div key={i} className="flex items-center gap-2">
                            <span className="text-xs font-mono" style={{ color: '#8E8160' }}>v{v.version}</span>
                            <span className="text-lg font-semibold font-mono" style={{ color: v.status === 'REVERTED' ? '#9B2C1F' : '#1C1915' }}>
                              {v.quizScoreAfter}%
                            </span>
                            {i < lesson.versions.filter(v => v.quizScoreAfter).length - 1 && (
                              <span className="font-mono" style={{ color: '#8E8160' }}>→</span>
                            )}
                          </div>
                        ))}
                        {(() => {
                          const withScores = lesson.versions.filter(v => v.quizScoreAfter);
                          if (withScores.length < 2) return null;
                          const first = withScores[0].quizScoreAfter!;
                          const last = withScores[withScores.length - 1].quizScoreAfter!;
                          const delta = last - first;
                          return (
                            <div className="ml-4 px-3 py-1 rounded-sm text-sm font-mono font-semibold" style={{ backgroundColor: delta >= 0 ? '#EBF2E2' : '#F5E8E6', color: delta >= 0 ? '#3F5A2A' : '#9B2C1F' }}>
                              {delta >= 0 ? '+' : ''}{delta}pp net
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
