import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ArrowRight, ArrowLeft, Check, Target, Link as LinkIcon, CheckCircle, AlertTriangle,
} from 'lucide-react';
import StatusBadge from './StatusBadge';
import { catalogCourses, type Course, type Lesson, type LessonVersion } from '../data/coursesData';

// ─── markdown renderer (ported from the Next.js variant) ──────────────────────
function renderMarkdown(md: string): string {
  return md
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/^\| (.+) \|$/gm, (match) => {
      const cells = match.split('|').filter(c => c.trim());
      const isHeader = cells.every(c => /^[-:]+$/.test(c.trim()));
      if (isHeader) return '';
      return `<tr>${cells.map(c => `<td>${c.trim()}</td>`).join('')}</tr>`;
    })
    .replace(/(<tr>[\s\S]*?<\/tr>\n?)+/g, (match) => `<table>${match}</table>`)
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?![<])(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '');
}

interface DiffLine { type: 'add' | 'del' | 'ctx' | 'header'; text: string; }
function parseDiff(diffText: string): DiffLine[] {
  return diffText.split('\n').map((line) => {
    if (line.startsWith('+++') || line.startsWith('---')) return { type: 'header', text: line };
    if (line.startsWith('@@')) return { type: 'header', text: line };
    if (line.startsWith('+')) return { type: 'add', text: line };
    if (line.startsWith('-')) return { type: 'del', text: line };
    return { type: 'ctx', text: line };
  });
}

const authorityColors: Record<string, string> = {
  PA0: 'var(--ink-faint)',
  PA1: 'var(--status-unknown)',
  PA2: 'var(--status-queue)',
  PA3: 'var(--status-revert)',
};

const actionColors: Record<string, string> = {
  PUBLISH: 'var(--status-publish)',
  REVERT: 'var(--status-revert)',
  ESCALATE: 'var(--status-revert)',
  NO_CHANGE: 'var(--status-nochange)',
  DRAFT: 'var(--status-unknown)',
};

type View =
  | { level: 'catalogue' }
  | { level: 'course'; course: Course }
  | { level: 'lesson'; course: Course; lesson: Lesson };

export default function CoursesSection() {
  const [view, setView] = useState<View>({ level: 'catalogue' });

  return (
    <div style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
      <AnimatePresence mode="wait">
        <motion.div
          key={view.level === 'catalogue' ? 'catalogue' : view.level === 'course' ? `course-${view.course.slug}` : `lesson-${view.lesson.slug}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.22 }}
        >
          {view.level === 'catalogue' && <CatalogueView onOpenCourse={(c) => setView({ level: 'course', course: c })} />}
          {view.level === 'course' && (
            <CourseDetailView
              course={view.course}
              onBack={() => setView({ level: 'catalogue' })}
              onOpenLesson={(l) => setView({ level: 'lesson', course: view.course, lesson: l })}
            />
          )}
          {view.level === 'lesson' && (
            <LessonPage
              lesson={view.lesson}
              onBack={() => setView({ level: 'course', course: view.course })}
            />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ─── Level 1: Catalogue ────────────────────────────────────────────────────────
function CatalogueView({ onOpenCourse }: { onOpenCourse: (c: Course) => void }) {
  return (
    <div>
      <div style={{ marginBottom: 36 }}>
        <div className="text-[11px] font-mono uppercase tracking-widest mb-2" style={{ color: 'var(--ink-faint)' }}>
          University of Agent Operations
        </div>
        <h1 className="text-2xl font-semibold" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)', marginBottom: 12 }}>
          Course Catalogue
        </h1>
        <p style={{ color: 'var(--ink-soft)', fontSize: 15, lineHeight: 1.6, maxWidth: 620 }}>
          Each course monitors its own subject and updates its lessons when the upstream world changes.
          Authority levels show how much autonomy the system has earned for each course.
        </p>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 32 }}>
        {[
          { level: 'PA0', label: 'Observe only' },
          { level: 'PA1', label: 'Auto-publish' },
          { level: 'PA2', label: 'Publish + notify cohort' },
          { level: 'PA3', label: 'Human-only' },
        ].map((l) => (
          <div key={l.level} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
            <span
              className="font-mono font-semibold"
              style={{ fontSize: 11, color: authorityColors[l.level], background: `${authorityColors[l.level]}20`, padding: '2px 8px', borderRadius: 'var(--radius)' }}
            >
              {l.level}
            </span>
            <span style={{ color: 'var(--ink-soft)' }}>{l.label}</span>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
        {catalogCourses.map((course) => (
          <div
            key={course.id}
            className="border rounded-sm overflow-hidden"
            style={{ borderColor: 'var(--rule)', background: 'var(--paper)' }}
          >
            <div className="border-b p-6 flex justify-between items-start gap-4" style={{ borderColor: 'var(--rule)', background: 'var(--paper-2)' }}>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2.5 mb-2 flex-wrap">
                  <span className="text-[11px] font-mono uppercase tracking-widest" style={{ color: 'var(--ink-faint)' }}>
                    {course.subject}
                  </span>
                  <span className="font-mono font-semibold text-[11px] px-2 py-0.5 rounded-sm"
                    style={{ color: authorityColors[course.authority], background: `${authorityColors[course.authority]}18` }}>
                    {course.authority}
                  </span>
                  {!course.real && (
                    <span className="text-[10px] font-mono uppercase tracking-widest px-1.5 py-0.5 border rounded-sm"
                      style={{ color: 'var(--status-queue)', borderColor: 'var(--status-queue)' }}>
                      demo course
                    </span>
                  )}
                </div>
                <h2 className="text-lg font-semibold" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)', marginBottom: 8 }}>
                  {course.title}
                </h2>
                <p className="text-sm leading-relaxed" style={{ color: 'var(--ink-soft)', maxWidth: 600 }}>
                  {course.description}
                </p>
              </div>
              <div className="text-right shrink-0">
                <div className="font-mono text-xl font-medium" style={{ color: 'var(--ink)' }}>
                  {course.totalLessons}
                </div>
                <div className="text-[11px] uppercase tracking-widest" style={{ color: 'var(--ink-faint)' }}>
                  Lessons
                </div>
                <div className="mt-2 text-xs flex items-center justify-end gap-1" style={{ color: 'var(--status-publish)' }}>
                  <Check size={10} /> {course.consecutiveAcceptedPublishes} accepted
                </div>
              </div>
            </div>

            <div>
              {course.lessons.map((lesson, idx) => (
                <button
                  key={lesson.id}
                  onClick={() => onOpenCourse(course)}
                  className="w-full text-left px-6 py-4 flex items-center gap-4 transition-colors hover:bg-[#EDE6D8]"
                  style={{ borderBottom: idx < course.lessons.length - 1 ? '1px solid var(--paper-2)' : 'none', background: 'transparent', cursor: 'pointer' }}
                >
                  <span className="font-mono text-xs" style={{ color: 'var(--ink-faint)', minWidth: 32 }}>
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold" style={{ color: 'var(--ink)' }}>{lesson.title}</div>
                    <div className="text-xs" style={{ color: 'var(--ink-faint)' }}>
                      {(lesson.objectives ?? []).length} objectives · v{lesson.version}
                    </div>
                  </div>
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded-sm" style={{ color: 'var(--ink-faint)', background: 'var(--paper-2)' }}>
                    v{lesson.version}
                  </span>
                  <ArrowRight size={14} style={{ color: 'var(--ink-faint)' }} />
                </button>
              ))}
            </div>

            <div className="px-6 py-3 border-t" style={{ borderColor: 'var(--rule)', background: 'var(--paper-2)' }}>
              <button
                onClick={() => onOpenCourse(course)}
                className="flex items-center gap-1.5"
                style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13 }}
              >
                View course <ArrowRight size={12} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Level 2: Course detail ────────────────────────────────────────────────────
function CourseDetailView({ course, onBack, onOpenLesson }: {
  course: Course; onBack: () => void; onOpenLesson: (l: Lesson) => void;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-6" style={{ fontSize: 13, color: 'var(--ink-faint)' }}>
        <button onClick={onBack} className="flex items-center gap-1" style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13 }}>
          <ArrowLeft size={12} /> Courses
        </button>
        <span>/</span>
        <span>{course.title}</span>
      </div>

      <div className="border-b mb-9 pb-7" style={{ borderColor: 'var(--rule)' }}>
        <div className="flex justify-between items-start gap-4 flex-wrap">
          <div>
            <div className="text-[11px] font-mono uppercase tracking-widest mb-2.5" style={{ color: 'var(--ink-faint)' }}>
              {course.subject}
            </div>
            <h1 className="text-3xl font-semibold" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)', marginBottom: 12 }}>
              {course.title}
            </h1>
            <p style={{ fontSize: 15, color: 'var(--ink-soft)', lineHeight: 1.65, maxWidth: 650, marginBottom: 16 }}>
              {course.description}
            </p>
            {!course.real && (
              <div className="inline-block text-xs px-2.5 py-1 border rounded-sm" style={{ color: 'var(--status-queue)', borderColor: 'var(--status-queue)' }}>
                Demo course — the repo ships one real course (agent-ops); this one illustrates the catalogue.
              </div>
            )}
          </div>
          <div className="border rounded-sm p-4 shrink-0" style={{ borderColor: 'var(--rule)', background: 'var(--paper-2)', minWidth: 180 }}>
            <div className="mb-3">
              <div className="text-[11px] uppercase tracking-widest mb-1" style={{ color: 'var(--ink-faint)' }}>Authority</div>
              <div className="font-mono text-lg font-semibold" style={{ color: authorityColors[course.authority] }}>
                {course.authority}
              </div>
            </div>
            <div>
              <div className="text-[11px] uppercase tracking-widest mb-1" style={{ color: 'var(--ink-faint)' }}>Accepted publishes</div>
              <div className="font-mono text-lg" style={{ color: 'var(--status-publish)' }}>
                {course.consecutiveAcceptedPublishes}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-8">
        {course.lessons.map((lesson, idx) => (
          <div key={lesson.id} className="border rounded-sm overflow-hidden" style={{ borderColor: 'var(--rule)' }}>
            <div className="border-b p-5 flex justify-between items-start gap-4" style={{ borderColor: 'var(--rule)', background: 'var(--paper-2)' }}>
              <div>
                <div className="flex items-center gap-2.5 mb-1.5">
                  <span className="font-mono text-xs" style={{ color: 'var(--ink-faint)' }}>
                    {String(idx + 1).padStart(2, '0')}
                  </span>
                  <span className="font-mono text-[11px] px-2 py-0.5 rounded-sm" style={{ color: 'var(--ink-faint)', background: 'var(--paper)' }}>
                    v{lesson.version}
                  </span>
                  <StatusBadge status={lesson.status} />
                </div>
                <h2 className="text-lg font-semibold" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)' }}>
                  {lesson.title}
                </h2>
              </div>
              <button
                onClick={() => onOpenLesson(lesson)}
                className="flex items-center gap-1 shrink-0"
                style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13 }}
              >
                Open lesson <ArrowRight size={12} />
              </button>
            </div>

            <div className="p-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="flex items-center gap-1.5 mb-2.5">
                    <Target size={13} style={{ color: 'var(--accent)' }} />
                    <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--ink-soft)' }}>
                      Objectives
                    </span>
                  </div>
                  <ul className="list-none p-0 m-0">
                    {lesson.objectives.map((obj, i) => (
                      <li key={i} className="flex gap-2 mb-1.5" style={{ fontSize: 13, color: 'var(--ink-soft)', lineHeight: 1.4 }}>
                        <Check size={12} style={{ color: 'var(--status-publish)', marginTop: 2, flexShrink: 0 }} />
                        {obj}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <div className="text-xs font-semibold uppercase tracking-widest mb-2.5" style={{ color: 'var(--ink-soft)' }}>
                    Version history
                  </div>
                  <div className="flex flex-col gap-1">
                    {lesson.versions.slice(-4).map((v) => (
                      <div key={v.id} className="flex items-center gap-2" style={{ fontSize: 12 }}>
                        <span className="font-mono" style={{ color: 'var(--ink-faint)', minWidth: 24 }}>v{v.version}</span>
                        <StatusBadge status={v.action} />
                        <span className="flex-1 truncate" style={{ color: 'var(--ink-soft)' }}>
                          {v.changeLog?.slice(0, 45) ?? '—'}
                        </span>
                      </div>
                    ))}
                    {lesson.versions.length === 0 && (
                      <div style={{ fontSize: 12, color: 'var(--ink-faint)', fontStyle: 'italic' }}>
                        No version history recorded (demo course data).
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {lesson.sources.length > 0 && (
                <div className="mt-4 pt-4 border-t" style={{ borderColor: 'var(--paper-2)' }}>
                  <div className="flex items-center gap-1.5 mb-2">
                    <LinkIcon size={12} style={{ color: 'var(--ink-faint)' }} />
                    <span className="text-[11px] uppercase tracking-widest" style={{ color: 'var(--ink-faint)' }}>
                      Sources verified
                    </span>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    {lesson.sources.map((src, i) => (
                      <span key={i} className="font-mono px-2 py-0.5 border rounded-sm"
                        style={{ fontSize: 11, color: 'var(--ink-soft)', background: 'var(--paper-2)', borderColor: 'var(--rule)' }}>
                        {src.publisher} · {src.captured_at}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {lesson.quizzes.length > 0 && (
                <div className="mt-3" style={{ fontSize: 13, color: 'var(--ink-faint)' }}>
                  {lesson.quizzes.length} quiz item{lesson.quizzes.length !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Level 3: Lesson page — Lesson / Diff / Quiz / History ─────────────────────
function LessonPage({ lesson, onBack }: { lesson: Lesson; onBack: () => void }) {
  const versions = [...lesson.versions].sort((a, b) => a.version - b.version);
  const [tab, setTab] = useState<'lesson' | 'diff' | 'quiz' | 'history'>('lesson');
  const [selectedVersion, setSelectedVersion] = useState(Math.max(0, versions.length - 1));
  const [compareVersion, setCompareVersion] = useState(Math.max(0, versions.length - 2));
  const [quizAnswers, setQuizAnswers] = useState<Record<number, number>>({});
  const [quizSubmitted, setQuizSubmitted] = useState(false);

  const currentV = versions[selectedVersion];
  const compareV = versions[compareVersion];
  const score = quizSubmitted
    ? lesson.quizzes.filter((q, i) => quizAnswers[i] === q.correctIndex).length
    : 0;

  if (versions.length > 1) {
    /* version selectors are only meaningful with history */
  }

  return (
    <div className="max-w-[1000px]">
      <div className="flex items-center gap-2 mb-6" style={{ fontSize: 13, color: 'var(--ink-faint)' }}>
        <button onClick={onBack} className="flex items-center gap-1" style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13 }}>
          <ArrowLeft size={12} /> Back to course
        </button>
        <span>/</span>
        <span style={{ color: 'var(--ink-soft)' }}>{lesson.title}</span>
      </div>

      <div className="mb-6">
        <div className="flex items-center gap-2.5 mb-2">
          <span className="font-mono text-[11px] px-2 py-0.5 rounded-sm" style={{ color: 'var(--ink-faint)', background: 'var(--paper-2)' }}>
            v{lesson.version}
          </span>
          <StatusBadge status={lesson.status} />
        </div>
        <h1 className="text-2xl font-semibold" style={{ fontFamily: 'var(--font-serif)', color: 'var(--ink)', marginBottom: 12 }}>
          {lesson.title}
        </h1>
        <div className="flex gap-2 flex-wrap">
          {lesson.objectives.map((obj, i) => (
            <span key={i} className="flex items-center gap-1.5 border rounded-sm px-2.5 py-1"
              style={{ fontSize: 12, color: 'var(--ink-soft)', background: 'var(--paper-2)', borderColor: 'var(--rule)' }}>
              <Target size={10} style={{ color: 'var(--accent)' }} />
              {obj}
            </span>
          ))}
        </div>
      </div>

      <div className="flex border-b mb-7" style={{ borderColor: 'var(--rule)' }}>
        {(['lesson', 'diff', 'quiz', 'history'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: tab === t ? '2px solid var(--ink)' : '2px solid transparent',
              padding: '10px 20px',
              cursor: 'pointer',
              fontFamily: 'inherit',
              fontSize: 13,
              fontWeight: tab === t ? 600 : 400,
              color: tab === t ? 'var(--ink)' : 'var(--ink-soft)',
              marginBottom: -1,
              textTransform: 'capitalize',
            }}
          >
            {t === 'diff' ? `Diff (${versions.length})` : t === 'quiz' ? `Quiz (${lesson.quizzes.length})` : t === 'history' ? 'History' : 'Lesson'}
          </button>
        ))}
      </div>

      {tab === 'lesson' && (
        <div>
          <div className="lesson-body" dangerouslySetInnerHTML={{ __html: renderMarkdown(lesson.body) }} />
          {lesson.sources.length > 0 && (
            <div className="mt-8 pt-6 border-t" style={{ borderColor: 'var(--rule)', maxWidth: 'var(--measure)' }}>
              <div className="flex items-center gap-1.5 mb-3">
                <LinkIcon size={12} style={{ color: 'var(--ink-faint)' }} />
                <span className="text-[11px] uppercase tracking-widest" style={{ color: 'var(--ink-faint)' }}>
                  Sources
                </span>
              </div>
              <div className="flex flex-col gap-2">
                {lesson.sources.map((src, i) => (
                  <div key={i} className="flex items-center gap-3 flex-wrap">
                    <span className="font-mono text-[11px]" style={{ color: 'var(--accent)', minWidth: 120 }}>{src.publisher}</span>
                    <span className="text-[11px]" style={{ color: 'var(--ink-faint)' }}>{src.captured_at}</span>
                    <a href={src.url} target="_blank" rel="noreferrer" className="text-[11px] underline" style={{ color: 'var(--ink-soft)' }}>
                      {src.url.replace(/^https?:\/\//, '').slice(0, 60)}
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'diff' && (
        <div>
          {versions.length < 2 ? (
            <p style={{ color: 'var(--ink-faint)', fontStyle: 'italic' }}>No diff available — only one version exists.</p>
          ) : (
            <div>
              <div style={{ display: 'flex', gap: 16, alignItems: 'center', marginBottom: 20, flexWrap: 'wrap' }}>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--ink-faint)', display: 'block', marginBottom: 4 }}>Compare (before)</label>
                  <select
                    value={compareVersion}
                    onChange={(e) => setCompareVersion(Number(e.target.value))}
                    className="font-mono"
                    style={{ fontSize: 13, background: 'var(--paper-2)', border: '1px solid var(--rule)', borderRadius: 'var(--radius)', padding: '6px 12px', color: 'var(--ink)', cursor: 'pointer' }}
                  >
                    {versions.map((v, i) => (
                      <option key={v.id} value={i}>v{v.version} — {v.action}</option>
                    ))}
                  </select>
                </div>
                <span style={{ color: 'var(--ink-faint)', marginTop: 16 }}>→</span>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--ink-faint)', display: 'block', marginBottom: 4 }}>Current (after)</label>
                  <select
                    value={selectedVersion}
                    onChange={(e) => setSelectedVersion(Number(e.target.value))}
                    className="font-mono"
                    style={{ fontSize: 13, background: 'var(--paper-2)', border: '1px solid var(--rule)', borderRadius: 'var(--radius)', padding: '6px 12px', color: 'var(--ink)', cursor: 'pointer' }}
                  >
                    {versions.map((v, i) => (
                      <option key={v.id} value={i}>v{v.version} — {v.action}</option>
                    ))}
                  </select>
                </div>
              </div>

              {currentV && (
                <div style={{ background: 'var(--paper-2)', border: '1px solid var(--rule)', borderRadius: 'var(--radius)', padding: '16px 20px', marginBottom: 20 }}>
                  <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
                    <StatusBadge status={currentV.action} />
                    <span className="font-mono" style={{ fontSize: 12, color: 'var(--ink-faint)' }}>{currentV.authority}</span>
                    {(currentV.confidence ?? 0) > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 12, color: 'var(--ink-faint)' }}>Confidence</span>
                        <div className="confidence-bar" style={{ width: 80 }}>
                          <div className="confidence-fill" style={{ width: `${(currentV.confidence ?? 0) * 100}%` }} />
                        </div>
                        <span className="font-mono" style={{ fontSize: 12, color: 'var(--status-publish)' }}>
                          {((currentV.confidence ?? 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--ink-soft)', marginBottom: 10 }}>
                    <strong>Change:</strong> {currentV.changeLog ?? '—'}
                  </div>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {(currentV.reasonCodes ?? []).map((rc) => (
                      <span key={rc} className="font-mono" style={{ fontSize: 11, color: 'var(--accent)', background: 'rgba(107,78,46,0.1)', padding: '2px 8px', borderRadius: 'var(--radius)' }}>
                        {rc}
                      </span>
                    ))}
                  </div>
                  {(currentV.sources ?? []).length > 0 && (
                    <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--rule)' }}>
                      <div style={{ fontSize: 11, color: 'var(--ink-faint)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>Sources</div>
                      {currentV.sources.map((src, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                          <span className="font-mono" style={{ fontSize: 11, color: 'var(--accent)', minWidth: 120 }}>{src.publisher}</span>
                          <div className="confidence-bar" style={{ width: 60 }}>
                            <div className="confidence-fill" style={{ width: `${(src.confidence ?? 0) * 100}%` }} />
                          </div>
                          <span className="font-mono" style={{ fontSize: 11, color: 'var(--status-publish)' }}>
                            {((src.confidence ?? 0) * 100).toFixed(0)}%
                          </span>
                          <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>{src.captured_at}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 20 }}>
                <div>
                  <div className="font-mono" style={{ fontSize: 12, color: 'var(--status-revert)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>−</span> Before: v{compareV?.version ?? '?'}
                  </div>
                  <div
                    style={{
                      background: 'rgba(155,44,31,0.04)', border: '1px solid rgba(155,44,31,0.2)', borderRadius: 'var(--radius)',
                      padding: 16, fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.6, color: 'var(--ink-soft)',
                      maxHeight: 400, overflowY: 'auto', whiteSpace: 'pre-wrap',
                    }}
                  >
                    {compareV?.body ?? '—'}
                  </div>
                </div>
                <div>
                  <div className="font-mono" style={{ fontSize: 12, color: 'var(--status-publish)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>+</span> After: v{currentV?.version ?? '?'}
                  </div>
                  <div
                    style={{
                      background: 'rgba(63,90,42,0.04)', border: '1px solid rgba(63,90,42,0.2)', borderRadius: 'var(--radius)',
                      padding: 16, fontFamily: 'var(--font-mono)', fontSize: 12, lineHeight: 1.6, color: 'var(--ink-soft)',
                      maxHeight: 400, overflowY: 'auto', whiteSpace: 'pre-wrap',
                    }}
                  >
                    {currentV?.body ?? '—'}
                  </div>
                </div>
              </div>

              {currentV?.diffText && (
                <div>
                  <div style={{ fontSize: 12, color: 'var(--ink-faint)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
                    Unified Diff
                  </div>
                  <div style={{ border: '1px solid var(--rule)', borderRadius: 'var(--radius)', overflow: 'hidden', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
                    {parseDiff(currentV.diffText).map((line, i) => (
                      <div
                        key={i}
                        className={line.type === 'add' ? 'diff-add' : line.type === 'del' ? 'diff-del' : ''}
                        style={{
                          padding: '2px 12px',
                          background: line.type === 'header' ? 'var(--paper-2)' : undefined,
                          color: line.type === 'header' ? 'var(--ink-faint)' : undefined,
                          whiteSpace: 'pre-wrap',
                        }}
                      >
                        {line.text || '\u00A0'}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {tab === 'quiz' && (
        <div style={{ maxWidth: 'var(--measure)' }}>
          {lesson.quizzes.length === 0 ? (
            <p style={{ color: 'var(--ink-faint)', fontStyle: 'italic' }}>No quiz items for this lesson.</p>
          ) : (
            <div>
              {quizSubmitted && (
                <div
                  style={{
                    background: score === lesson.quizzes.length ? 'rgba(63,90,42,0.08)' : 'rgba(150,85,10,0.08)',
                    border: `1px solid ${score === lesson.quizzes.length ? 'var(--status-publish)' : 'var(--status-queue)'}`,
                    borderRadius: 'var(--radius)', padding: '16px 20px', marginBottom: 24,
                    display: 'flex', alignItems: 'center', gap: 12,
                  }}
                >
                  {score === lesson.quizzes.length
                    ? <CheckCircle size={20} style={{ color: 'var(--status-publish)' }} />
                    : <AlertTriangle size={20} style={{ color: 'var(--status-queue)' }} />}
                  <div>
                    <div style={{ fontWeight: 600, color: 'var(--ink)', marginBottom: 2 }}>
                      {score}/{lesson.quizzes.length} correct
                    </div>
                    <div style={{ fontSize: 13, color: 'var(--ink-soft)' }}>
                      {score === lesson.quizzes.length ? 'All objectives demonstrated.' : 'Review the explanations below.'}
                    </div>
                  </div>
                  <button
                    onClick={() => { setQuizSubmitted(false); setQuizAnswers({}); }}
                    style={{ marginLeft: 'auto', background: 'none', border: '1px solid var(--rule)', padding: '6px 12px', borderRadius: 'var(--radius)', cursor: 'pointer', fontSize: 13, color: 'var(--ink-soft)', fontFamily: 'inherit' }}
                  >
                    Retake
                  </button>
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                {lesson.quizzes.map((q, qi) => {
                  return (
                    <div key={q.id} style={{ border: '1px solid var(--rule)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
                      <div style={{ background: 'var(--paper-2)', padding: '14px 20px', borderBottom: '1px solid var(--rule)' }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                          <span className="font-mono" style={{ fontSize: 11, color: 'var(--ink-faint)', minWidth: 24, marginTop: 2 }}>Q{qi + 1}</span>
                          <div>
                            <p style={{ fontFamily: 'var(--font-serif)', fontSize: 15, color: 'var(--ink)', lineHeight: 1.55, marginBottom: 4 }}>
                              {q.question}
                            </p>
                            {q.objectiveRef && (
                              <span style={{ fontSize: 11, color: 'var(--ink-faint)' }}>
                                <Target size={9} style={{ display: 'inline', marginRight: 3 }} />
                                {q.objectiveRef}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div style={{ padding: '16px 20px' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                          {q.options.map((opt, oi) => {
                            const optSelected = quizAnswers[qi] === oi;
                            const optCorrect = oi === q.correctIndex;
                            let bg = 'var(--paper)';
                            let border = '1px solid var(--rule)';
                            let color = 'var(--ink-soft)';
                            if (quizSubmitted) {
                              if (optCorrect) { bg = 'rgba(63,90,42,0.08)'; border = '1px solid var(--status-publish)'; color = 'var(--status-publish)'; }
                              else if (optSelected && !optCorrect) { bg = 'rgba(155,44,31,0.08)'; border = '1px solid var(--status-revert)'; color = 'var(--status-revert)'; }
                            } else if (optSelected) {
                              bg = 'var(--paper-2)'; border = '1px solid var(--ink-soft)'; color = 'var(--ink)';
                            }
                            return (
                              <button
                                key={oi}
                                onClick={() => !quizSubmitted && setQuizAnswers(prev => ({ ...prev, [qi]: oi }))}
                                style={{ background: bg, border, borderRadius: 'var(--radius)', padding: '10px 14px', textAlign: 'left', cursor: quizSubmitted ? 'default' : 'pointer', fontSize: 14, color, fontFamily: 'inherit', display: 'flex', alignItems: 'center', gap: 8 }}
                              >
                                <span className="font-mono" style={{ fontSize: 11, color: 'var(--ink-faint)' }}>
                                  {String.fromCharCode(65 + oi)}
                                </span>
                                {opt}
                                {quizSubmitted && optCorrect && <Check size={13} style={{ marginLeft: 'auto' }} />}
                                {quizSubmitted && optSelected && !optCorrect && <AlertTriangle size={13} style={{ marginLeft: 'auto' }} />}
                              </button>
                            );
                          })}
                        </div>
                        {quizSubmitted && (
                          <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--paper-2)', borderRadius: 'var(--radius)', fontSize: 13, color: 'var(--ink-soft)', lineHeight: 1.5 }}>
                            <strong>Why:</strong> {q.explanation}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {!quizSubmitted && (
                <button
                  onClick={() => setQuizSubmitted(true)}
                  disabled={Object.keys(quizAnswers).length < lesson.quizzes.length}
                  style={{
                    marginTop: 20, padding: '10px 24px', background: Object.keys(quizAnswers).length < lesson.quizzes.length ? 'var(--paper-2)' : 'var(--accent)',
                    color: Object.keys(quizAnswers).length < lesson.quizzes.length ? 'var(--ink-faint)' : 'var(--paper)',
                    border: '1px solid var(--rule)', borderRadius: 'var(--radius)', cursor: 'pointer', fontSize: 14, fontFamily: 'inherit', fontWeight: 600,
                  }}
                >
                  Check answers ({Object.keys(quizAnswers).length}/{lesson.quizzes.length})
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {tab === 'history' && (
        <div style={{ maxWidth: 900 }}>
          {versions.length === 0 ? (
            <p style={{ color: 'var(--ink-faint)', fontStyle: 'italic' }}>No version history recorded for this lesson.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {versions.map((v, i) => (
                <div
                  key={v.id}
                  style={{
                    border: '1px solid var(--rule)', borderRadius: 'var(--radius)', overflow: 'hidden',
                    background: i === versions.length - 1 ? 'var(--paper)' : 'var(--paper-2)',
                  }}
                >
                  <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--rule)', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                    <span className="font-mono" style={{ fontSize: 14, fontWeight: 600, color: actionColors[v.action] ?? 'var(--ink)', minWidth: 28 }}>
                      v{v.version}
                    </span>
                    <StatusBadge status={v.action} />
                    <span className="font-mono" style={{ fontSize: 11, color: 'var(--ink-faint)', background: 'var(--paper-2)', padding: '2px 6px', borderRadius: 'var(--radius)' }}>
                      {v.authority}
                    </span>
                    {(v.confidence ?? 0) > 0 && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 'auto' }}>
                        <span style={{ fontSize: 12, color: 'var(--ink-faint)' }}>Confidence</span>
                        <div className="confidence-bar" style={{ width: 60 }}>
                          <div className="confidence-fill" style={{ width: `${(v.confidence ?? 0) * 100}%` }} />
                        </div>
                        <span className="font-mono" style={{ fontSize: 12, color: 'var(--status-publish)' }}>
                          {((v.confidence ?? 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                    {i === versions.length - 1 && (
                      <span style={{ marginLeft: (v.confidence ?? 0) > 0 ? 0 : 'auto', fontSize: 11, color: 'var(--status-publish)', fontWeight: 600 }}>CURRENT</span>
                    )}
                  </div>
                  <div style={{ padding: '14px 20px' }}>
                    <div style={{ fontSize: 13, color: 'var(--ink-soft)', marginBottom: 10, lineHeight: 1.5 }}>
                      {v.changeLog ?? 'Initial version'}
                    </div>
                    {(v.reasonCodes ?? []).length > 0 && (
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
                        {(v.reasonCodes ?? []).map((rc) => (
                          <span key={rc} className="font-mono" style={{ fontSize: 10, color: 'var(--accent)', background: 'rgba(107,78,46,0.1)', padding: '1px 6px', borderRadius: 'var(--radius)' }}>
                            {rc}
                          </span>
                        ))}
                      </div>
                    )}
                    {(v.sources ?? []).length > 0 && (
                      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                        {v.sources.map((src, si) => (
                          <span key={si} className="font-mono" style={{ fontSize: 11, color: 'var(--ink-faint)', background: 'var(--paper-2)', border: '1px solid var(--rule)', padding: '1px 6px', borderRadius: 'var(--radius)' }}>
                            {src.publisher} {((src.confidence ?? 0) * 100).toFixed(0)}%
                          </span>
                        ))}
                      </div>
                    )}
                    {v.diffText && (
                      <button
                        onClick={() => { setSelectedVersion(i); setCompareVersion(Math.max(0, i - 1)); setTab('diff'); }}
                        style={{ marginTop: 10, background: 'none', border: '1px solid var(--rule)', padding: '4px 12px', borderRadius: 'var(--radius)', cursor: 'pointer', fontSize: 12, color: 'var(--accent)', fontFamily: 'inherit' }}
                      >
                        View diff →
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Unused-import guard: LessonVersion is used via the `versions` typing above.
export type { LessonVersion };
