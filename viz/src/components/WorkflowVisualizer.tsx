import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { workflowRuns } from '../data/mockData';
import type { WorkflowRun, WorkflowEvent } from '../data/mockData';
import StatusBadge from './StatusBadge';

const phaseColors: Record<string, { color: string; bg: string; label: string }> = {
  notice:  { color: '#6B4E2E', bg: '#F5EDE3', label: 'NOTICE' },
  verify:  { color: '#96550A', bg: '#F7EFE4', label: 'VERIFY' },
  decide:  { color: '#3F5A2A', bg: '#EBF2E2', label: 'DECIDE' },
  act:     { color: '#1C1915', bg: '#EEEBE4', label: 'ACT' },
  learn:   { color: '#7A5C00', bg: '#F5F0E0', label: 'LEARN' },
  report:  { color: '#5C564C', bg: '#EEEBE4', label: 'REPORT' },
};

const eventStatusIcon: Record<string, string> = {
  ok: '✓',
  warn: '△',
  refused: '⊘',
  publish: '↑',
  revert: '↺',
  stuck: '◎',
};

function EventRow({ event, index, active }: { event: WorkflowEvent; index: number; active: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const ph = phaseColors[event.phase];
  const icon = eventStatusIcon[event.status] || '·';

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: active ? 1 : 0.4, y: 0 }}
      transition={{ delay: index * 0.06, duration: 0.3 }}
      className="border-b last:border-b-0 cursor-pointer"
      style={{ borderColor: '#C9C0AE' }}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-start gap-3 px-4 py-3 hover:bg-white/30 transition-colors">
        {/* Phase tag */}
        <div className="flex-shrink-0 mt-0.5">
          <span
            className="inline-block px-2 py-0.5 text-[9px] font-mono font-bold tracking-widest uppercase rounded-sm"
            style={{ color: ph.color, backgroundColor: ph.bg, border: `1px solid ${ph.color}` }}
          >
            {ph.label}
          </span>
        </div>
        {/* Time */}
        <div className="flex-shrink-0 text-[11px] font-mono mt-0.5" style={{ color: '#8E8160' }}>
          {event.ts}
        </div>
        {/* Icon */}
        <div className="flex-shrink-0 text-sm font-mono font-bold mt-0.5" style={{ color: ph.color }}>
          {icon}
        </div>
        {/* Description */}
        <div className="flex-1 min-w-0">
          <div className="text-sm" style={{ color: '#1C1915' }}>{event.description}</div>
          {event.reasonCode && (
            <div className="text-[11px] font-mono mt-0.5" style={{ color: '#68604F' }}>
              [{event.reasonCode}]
            </div>
          )}
        </div>
        <div className="flex-shrink-0 text-xs font-mono" style={{ color: '#8E8160' }}>
          {expanded ? '▲' : '▼'}
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-3 pt-1">
              <div
                className="text-xs leading-relaxed p-3 rounded-sm border font-mono"
                style={{
                  color: '#4A443A',
                  backgroundColor: 'rgba(197,162,2,.08)',
                  borderColor: '#C9C0AE',
                  borderLeft: `3px solid ${ph.color}`,
                }}
              >
                {event.detail}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function PhaseTimeline({ run }: { run: WorkflowRun }) {
  const phases = ['notice', 'verify', 'decide', 'act', 'learn', 'report'];
  const usedPhases = new Set<string>(run.events.map(e => e.phase));

  return (
    <div className="flex items-center gap-0 mb-6 overflow-x-auto pb-1">
      {phases.map((phase, i) => {
        const active = usedPhases.has(phase);
        const ph = phaseColors[phase];
        const events = run.events.filter(e => (e.phase as string) === phase);
        const hasRefusal = events.some(e => e.status === 'refused');
        const hasPublish = events.some(e => e.status === 'publish');
        const hasRevert = events.some(e => e.status === 'revert');

        return (
          <div key={phase} className="flex items-center">
            <div className="flex flex-col items-center">
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center text-lg font-mono font-bold border-2 transition-all"
                style={{
                  backgroundColor: active ? ph.bg : '#EAE4D8',
                  borderColor: active ? ph.color : '#C9C0AE',
                  color: active ? ph.color : '#8E8160',
                  opacity: active ? 1 : 0.4,
                }}
              >
                {hasRefusal ? '⊘' : hasPublish ? '↑' : hasRevert ? '↺' : eventStatusIcon[events[0]?.status] || '·'}
              </div>
              <div className="text-[9px] font-mono font-bold tracking-widest mt-1 uppercase" style={{ color: active ? ph.color : '#8E8160' }}>
                {ph.label}
              </div>
            </div>
            {i < phases.length - 1 && (
              <div className="w-6 h-0.5 -mt-4 flex-shrink-0" style={{ backgroundColor: active && usedPhases.has(phases[i + 1] as string) ? '#6B4E2E' : '#C9C0AE' }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default function WorkflowVisualizer() {
  const [selectedRun, setSelectedRun] = useState(0);
  const [playIndex, setPlayIndex] = useState<number | null>(null);
  const [playing, setPlaying] = useState(false);
  const run = workflowRuns[selectedRun];

  const startPlayback = () => {
    setPlayIndex(0);
    setPlaying(true);
    let idx = 0;
    const interval = setInterval(() => {
      idx++;
      if (idx >= run.events.length) {
        setPlayIndex(null);
        setPlaying(false);
        clearInterval(interval);
      } else {
        setPlayIndex(idx);
      }
    }, 900);
  };

  const outcomeMap: Record<string, string> = {
    PUBLISH: 'PUBLISH',
    ESCALATE: 'ESCALATE',
    DISPATCH: 'DISPATCH',
    REVERT: 'REVERT',
    NO_CHANGE: 'NO_CHANGE',
    PUBLISHED: 'PUBLISHED',
    REVERTED: 'REVERTED',
    REFUSED: 'REFUSED',
    QUEUED: 'QUEUED',
  };

  return (
    <div className="space-y-6">
      {/* Run selector */}
      <div className="flex flex-wrap gap-2">
        {workflowRuns.map((r, i) => (
          <button
            key={r.id}
            onClick={() => { setSelectedRun(i); setPlayIndex(null); setPlaying(false); }}
            className="text-left p-3 rounded-sm border text-xs transition-all"
            style={{
              borderColor: selectedRun === i ? '#6B4E2E' : '#C9C0AE',
              backgroundColor: selectedRun === i ? '#EDE6D8' : '#F3EFE7',
              color: '#1C1915',
              fontFamily: "'IBM Plex Sans', system-ui, sans-serif",
            }}
          >
            <div className="font-semibold mb-1">{r.label.split('—')[0].trim()}</div>
            <div className="text-[11px] font-mono" style={{ color: '#68604F' }}>{r.label.split('—')[1]?.trim()}</div>
          </button>
        ))}
      </div>

      {/* Main panel */}
      <motion.div
        key={run.id}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="border rounded-sm overflow-hidden"
        style={{ borderColor: '#8E8160', backgroundColor: '#F3EFE7' }}
      >
        {/* Run header */}
        <div className="px-5 py-4 border-b" style={{ borderColor: '#C9C0AE', backgroundColor: '#EAE4D8' }}>
          <div className="flex flex-wrap items-start gap-3 mb-1">
            <span className="text-[11px] font-mono" style={{ color: '#8E8160' }}>{run.runId}</span>
            <span className="text-[11px] font-mono" style={{ color: '#8E8160' }}>{run.ts} UTC</span>
            <span className="text-[11px] font-mono px-1.5 py-0.5 border rounded-sm" style={{ color: '#3F5A2A', borderColor: '#3F5A2A', backgroundColor: '#EBF2E2' }}>
              mode: {run.mode}
            </span>
          </div>
          <h3 className="text-base font-semibold" style={{ color: '#1C1915' }}>{run.label}</h3>
          <div className="flex flex-wrap gap-4 mt-2 text-xs" style={{ color: '#68604F' }}>
            <span><span className="font-mono">course:</span> {run.course}</span>
            <span><span className="font-mono">lesson:</span> {run.lesson}</span>
            <span><span className="font-mono">cadence:</span> {run.cadence}</span>
          </div>
          <div className="flex items-center gap-3 mt-3">
            <span className="text-xs" style={{ color: '#4A443A' }}>Outcome:</span>
            <StatusBadge status={outcomeMap[run.outcome] || run.outcome} size="md" />
            <button
              onClick={startPlayback}
              disabled={playing}
              className="ml-auto px-4 py-1.5 text-xs font-mono border rounded-sm transition-opacity disabled:opacity-40"
              style={{ borderColor: '#6B4E2E', color: '#6B4E2E', backgroundColor: 'transparent' }}
            >
              {playing ? '▶ Playing...' : '▶ Replay loop'}
            </button>
          </div>
        </div>

        {/* Phase timeline */}
        <div className="px-5 pt-5 pb-2">
          <PhaseTimeline run={run} />
        </div>

        {/* Events */}
        <div className="border-t" style={{ borderColor: '#C9C0AE' }}>
          <div className="px-4 py-2 text-[11px] font-mono uppercase tracking-widest" style={{ color: '#8E8160', backgroundColor: '#EAE4D8' }}>
            Event log — click any row to expand
          </div>
          {run.events.map((event, i) => (
            <EventRow
              key={event.id}
              event={event}
              index={i}
              active={playIndex === null || i <= playIndex}
            />
          ))}
        </div>

        {/* Digest block */}
        {run.digest && (
          <div className="border-t" style={{ borderColor: '#C9C0AE' }}>
            <div className="px-4 py-2 text-[11px] font-mono uppercase tracking-widest" style={{ color: '#8E8160', backgroundColor: '#EAE4D8' }}>
              Digest — as shipped (run.cr-20260926-1726-793 digest.md, verbatim)
            </div>
            <pre className="px-4 py-3 text-xs font-mono leading-relaxed overflow-x-auto" style={{ color: '#4A443A', backgroundColor: '#F3EFE7' }}>
              {run.digest}
            </pre>
          </div>
        )}

        {/* Learner card */}
        {run.learnerCard && (
          <div className="border-t" style={{ borderColor: '#C9C0AE' }}>
            <div className="px-4 py-2 text-[11px] font-mono uppercase tracking-widest" style={{ color: '#8E8160', backgroundColor: '#EAE4D8' }}>
              Learner card (consented cohort)
            </div>
            <div className="px-4 py-4" style={{ backgroundColor: '#F3EFE7' }}>
              <div className="max-w-lg border rounded-sm p-4" style={{ borderColor: '#8E8160', backgroundColor: '#EAE4D8' }}>
                <pre className="text-xs font-mono leading-relaxed whitespace-pre-wrap" style={{ color: '#1C1915' }}>
                  {run.learnerCard}
                </pre>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </div>
  );
}
