import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Course } from '../data/mockData';
import LessonViewer from './LessonViewer';
import StatusBadge from './StatusBadge';

function StatPill({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="flex flex-col items-center px-4 py-3 border-r last:border-r-0" style={{ borderColor: '#C9C0AE' }}>
      <div className="text-xl font-semibold font-mono" style={{ color }}>{value}</div>
      <div className="text-[10px] font-mono uppercase tracking-widest mt-0.5" style={{ color: '#8E8160' }}>{label}</div>
    </div>
  );
}

export default function CourseView({ course }: { course: Course }) {
  const [selectedLesson, setSelectedLesson] = useState(0);
  const lesson = course.lessons[selectedLesson];

  const totalChanges = course.publishedChanges + course.refusedChanges + course.revertedChanges
    + course.dispatchedChanges + course.unchangedChanges;

  return (
    <div style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
      {/* Course header */}
      <div className="border rounded-sm mb-6" style={{ borderColor: '#8E8160', backgroundColor: '#EAE4D8' }}>
        <div className="p-5 border-b" style={{ borderColor: '#C9C0AE' }}>
          <div className="flex flex-wrap items-start gap-3 justify-between mb-2">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[11px] font-mono px-2 py-0.5 border rounded-sm font-semibold" style={{ color: '#6B4E2E', borderColor: '#6B4E2E' }}>
                  {course.code}
                </span>
                <span className="text-[11px] font-mono" style={{ color: '#8E8160' }}>{course.department}</span>
              </div>
              <h2 className="text-xl font-semibold" style={{ color: '#1C1915', fontFamily: "'Source Serif 4', Georgia, serif" }}>
                {course.title}
              </h2>
              <p className="text-sm mt-0.5" style={{ color: '#68604F' }}>{course.subtitle}</p>
            </div>
            <div className="text-right">
              <div className="text-xs" style={{ color: '#68604F' }}>
                <div>{course.instructor}</div>
                <div className="font-mono">{course.semester}</div>
                <div className="font-mono text-[11px] mt-1">Last updated: {course.lastUpdated}</div>
              </div>
            </div>
          </div>
          <p className="text-sm leading-relaxed" style={{ color: '#4A443A', maxWidth: '72ch' }}>{course.description}</p>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-2 md:grid-cols-6 divide-x" style={{ borderColor: '#C9C0AE' }}>
          <StatPill label="Consented" value={`${course.consentedLearners}/${course.enrolledLearners}`} color="#1C1915" />
          <StatPill label="Lessons" value={course.lessons.length} color="#1C1915" />
          <StatPill label="Published" value={course.publishedChanges} color="#3F5A2A" />
          <StatPill label="Refused" value={course.refusedChanges} color="#9B2C1F" />
          <StatPill label="Reverted" value={course.revertedChanges} color="#9B2C1F" />
          <StatPill label="Recorded runs" value={course.loopRuns} color="#6B4E2E" />
        </div>

        {/* Loop health bar */}
        <div className="px-5 py-3 border-t" style={{ borderColor: '#C9C0AE' }}>
          <div className="flex items-center gap-3">
            <div className="text-[11px] font-mono uppercase tracking-widest" style={{ color: '#8E8160' }}>
              Autonomy health — {totalChanges} decisions
            </div>
            <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: '#C9C0AE' }}>
              <div style={{ display: 'flex', height: '100%' }}>
                <div style={{ width: `${course.publishedChanges / totalChanges * 100}%`, backgroundColor: '#3F5A2A' }} />
                <div style={{ width: `${course.revertedChanges / totalChanges * 100}%`, backgroundColor: '#96550A' }} />
                <div style={{ width: `${course.refusedChanges / totalChanges * 100}%`, backgroundColor: '#9B2C1F' }} />
              </div>
            </div>
            <div className="flex gap-3 text-[10px] font-mono" style={{ color: '#68604F' }}>
              <span style={{ color: '#3F5A2A' }}>■ published</span>
              <span style={{ color: '#96550A' }}>■ reverted</span>
              <span style={{ color: '#9B2C1F' }}>■ refused</span>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 mt-2">
            <span className="text-[11px] font-mono" style={{ color: '#8E8160' }}>sources:</span>
            {course.sources.map(s => (
              <span key={s} className="text-[11px] font-mono px-1.5 py-0.5 border rounded-sm" style={{ color: '#4A443A', borderColor: '#C9C0AE' }}>{s}</span>
            ))}
            <span className="text-[11px] font-mono" style={{ color: '#8E8160' }}>· cadence: {course.updateCadence}</span>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-4">
        {/* Lesson list */}
        <div className="space-y-2">
          <div className="text-[11px] font-mono uppercase tracking-widest mb-3" style={{ color: '#8E8160' }}>
            Lessons ({course.lessons.length})
          </div>
          {course.lessons.map((l, i) => {
            const latestV = l.versions[l.versions.length - 1];
            const isSelected = i === selectedLesson;
            return (
              <button
                key={l.id}
                onClick={() => setSelectedLesson(i)}
                className="w-full text-left p-3 rounded-sm border transition-all"
                style={{
                  borderColor: isSelected ? '#6B4E2E' : '#C9C0AE',
                  backgroundColor: isSelected ? '#EDE6D8' : '#F3EFE7',
                }}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-[11px] font-mono mb-0.5" style={{ color: '#8E8160' }}>{l.id} · {l.duration}</div>
                    <div className="text-sm font-semibold leading-tight" style={{ color: '#1C1915' }}>{l.number}. {l.title}</div>
                    <div className="text-[11px] mt-0.5 truncate" style={{ color: '#68604F' }}>{l.subtitle}</div>
                  </div>
                  <div className="flex flex-col items-end gap-1 flex-shrink-0">
                    <StatusBadge status={latestV?.status || 'PUBLISHED'} />
                    <span className="text-[10px] font-mono" style={{ color: '#8E8160' }}>v{l.currentVersion}</span>
                  </div>
                </div>
                {/* Mini progress — real cohort metric is quiz_delta; unmeasured in sim */}
                <div className="flex items-center gap-2 mt-2">
                  <div className="flex-1 h-1 rounded-full overflow-hidden" style={{ backgroundColor: '#C9C0AE' }}>
                    <div className="h-full" style={{ width: l.avgQuizScore !== undefined ? `${l.avgQuizScore}%` : '100%', backgroundColor: l.avgQuizScore === undefined ? '#C9C0AE' : (l.avgQuizScore >= 80 ? '#3F5A2A' : '#96550A') }} />
                  </div>
                  <span className="text-[10px] font-mono" style={{ color: '#8E8160' }}>
                    {l.avgQuizScore !== undefined ? `${l.avgQuizScore}%` : 'unmeasured'}
                  </span>
                </div>
                {l.stuckLearners > 0 && (
                  <div className="mt-1.5 text-[10px] font-mono" style={{ color: '#9B2C1F' }}>
                    ◎ {l.stuckLearners} stuck learner{l.stuckLearners !== 1 ? 's' : ''}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Lesson detail */}
        <AnimatePresence mode="wait">
          <motion.div
            key={`${course.id}-${selectedLesson}`}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.25 }}
          >
            {lesson && <LessonViewer lesson={lesson} />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
