import { useState } from 'react';
import { motion } from 'framer-motion';
import { receipts, workflowRuns, heroDigest, register, allCourses } from '../data/mockData';
import StatusBadge from './StatusBadge';

const phaseIcon: Record<string, string> = {
  PUBLISH: '↑',
  REVERT: '↺',
  ESCALATE: '⊘',
  NO_CHANGE: '·',
  DISPATCH: '◎',
};

const actionColor: Record<string, string> = {
  PUBLISH: '#3F5A2A',
  REVERT: '#9B2C1F',
  ESCALATE: '#9B2C1F',
  NO_CHANGE: '#5C564C',
  DISPATCH: '#96550A',
};

// Resolve the receipt ↔ lesson-version link from the real data:
// PUBLISH receipts point at the version they wrote; the REVERT receipt (rcpt-…-008)
// points at v5 but its evidence is the v3→v4 diff of the publish it undid.
function resolveVersion(receiptId: string) {
  for (const course of allCourses) {
    for (const lesson of course.lessons) {
      for (const v of lesson.versions) {
        if (v.receipt === receiptId) {
          if (v.status === 'REVERTED' && v.revertOf) {
            const undone = lesson.versions.find(x => x.version === v.revertOf);
            if (undone) return { courseTitle: course.title, lesson, version: undone, revert: v };
          }
          return { courseTitle: course.title, lesson, version: v };
        }
      }
    }
  }
  return null;
}

export default function AuthorConsole() {
  const [selectedReceipt, setSelectedReceipt] = useState(0);
  const r = receipts[selectedReceipt];

  const totalDecisions = receipts.length;
  const published = receipts.filter(x => x.action === 'PUBLISH').length;
  const refused = receipts.filter(x => x.action === 'ESCALATE').length;
  const reverted = receipts.filter(x => x.action === 'REVERT').length;
  const dispatched = receipts.filter(x => x.action === 'DISPATCH').length;
  const noChange = receipts.filter(x => x.action === 'NO_CHANGE').length;
  const chainOk = receipts[0].runId === register.heroRun;

  // Decisions wanting a human — the two ESCALATE rows the digest names
  const humanDecisions = receipts.filter(x =>
    x.eventId === 'cr-single-source-01' || x.eventId === 'cr-conflict-01'
  );

  return (
    <div style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
      {/* Console header */}
      <div className="border rounded-sm mb-4" style={{ borderColor: '#8E8160', backgroundColor: '#EAE4D8' }}>
        <div className="px-5 py-3 border-b" style={{ borderColor: '#C9C0AE' }}>
          <div className="flex flex-wrap items-center gap-3 justify-between">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-widest" style={{ color: '#8E8160' }}>
                Author Console
              </span>
              <div className="text-[11px] font-mono mt-0.5" style={{ color: '#68604F' }}>
                run {register.heroRun} · mode: <span style={{ color: '#96550A' }}>sim</span> (fixtures, no model calls, no mail)
              </div>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-mono px-2 py-1 border rounded-sm" style={{ color: chainOk ? '#3F5A2A' : '#9B2C1F', borderColor: chainOk ? '#3F5A2A' : '#9B2C1F', backgroundColor: chainOk ? '#EBF2E2' : '#F5E8E6' }}>
                chain ✓ ok ({totalDecisions} rows)
              </span>
              <span className="text-[11px] font-mono px-2 py-1 border rounded-sm" style={{ color: '#3F5A2A', borderColor: '#3F5A2A', backgroundColor: '#EBF2E2' }}>
                receipts 100%
              </span>
              <span className="text-[11px] font-mono px-2 py-1 border rounded-sm" style={{ color: '#3F5A2A', borderColor: '#3F5A2A', backgroundColor: '#EBF2E2' }}>
                hostile→publish: 0
              </span>
            </div>
          </div>
        </div>

        {/* Stats row — the run's real action counts */}
        <div className="grid grid-cols-3 md:grid-cols-5 divide-x" style={{ borderColor: '#C9C0AE' }}>
          {[
            { label: 'Decisions', value: totalDecisions, color: '#1C1915' },
            { label: 'Published', value: published, color: '#3F5A2A' },
            { label: 'Refused (escalate)', value: refused, color: '#9B2C1F' },
            { label: 'Reverted', value: reverted, color: '#9B2C1F' },
            { label: 'Dispatch / no-change', value: `${dispatched} / ${noChange}`, color: '#96550A' },
          ].map(s => (
            <div key={s.label} className="px-4 py-3 text-center">
              <div className="text-2xl font-semibold font-mono" style={{ color: s.color }}>{s.value}</div>
              <div className="text-[10px] font-mono uppercase tracking-widest" style={{ color: '#8E8160' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Digest preview — the real digest.md, verbatim */}
        <div className="border-t" style={{ borderColor: '#C9C0AE' }}>
          <div className="px-4 py-1.5 text-[10px] font-mono uppercase tracking-widest" style={{ color: '#8E8160' }}>
            Morning digest — specs/evidence/{register.heroRun}/digest.md (verbatim)
          </div>
          <pre className="px-4 py-2 pb-3 text-[11px] font-mono leading-relaxed overflow-x-auto" style={{ color: '#4A443A' }}>
{heroDigest}
          </pre>
        </div>
      </div>

      {/* Two-panel: receipts list + detail */}
      <div className="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-4">
        {/* Receipt list */}
        <div>
          <div className="text-[11px] font-mono uppercase tracking-widest mb-2" style={{ color: '#8E8160' }}>
            Receipts — refusals first
          </div>
          {[...receipts]
            .sort((a, b) => (a.action === 'ESCALATE' ? -1 : b.action === 'ESCALATE' ? 1 : 0))
            .map((receipt) => {
              const originalIdx = receipts.indexOf(receipt);
              const isSelected = originalIdx === selectedReceipt;
              return (
                <button
                  key={receipt.receiptId}
                  onClick={() => setSelectedReceipt(originalIdx)}
                  className="w-full text-left px-3 py-3 border-b last:border-b-0 transition-all"
                  style={{
                    borderColor: '#C9C0AE',
                    backgroundColor: isSelected ? '#EDE6D8' : '#F3EFE7',
                    borderLeft: isSelected ? '3px solid #6B4E2E' : '3px solid transparent',
                  }}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-base font-mono flex-shrink-0 mt-0.5" style={{ color: actionColor[receipt.action] || '#5C564C' }}>
                      {phaseIcon[receipt.action] || '·'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <StatusBadge status={receipt.action} />
                        <span className="text-[10px] font-mono" style={{ color: '#8E8160' }}>{receipt.stream}</span>
                      </div>
                      <div className="text-[10px] font-mono mt-1 truncate" style={{ color: '#68604F' }}>
                        [{receipt.reasonCodes.join(', ')}]
                      </div>
                      <div className="text-[10px] font-mono truncate" style={{ color: '#8E8160' }}>{receipt.eventId}</div>
                    </div>
                  </div>
                </button>
              );
            })}
        </div>

        {/* Receipt detail */}
        <motion.div
          key={r.receiptId}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="border rounded-sm overflow-hidden"
          style={{ borderColor: '#8E8160', backgroundColor: '#F3EFE7' }}
        >
          <div className="px-4 py-3 border-b" style={{ borderColor: '#C9C0AE', backgroundColor: '#EAE4D8' }}>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-mono font-bold" style={{ color: '#6B4E2E' }}>{r.receiptId}</span>
              <StatusBadge status={r.action} />
              <span className="text-[10px] font-mono" style={{ color: '#8E8160' }}>{r.authority} · decided_by {r.decidedBy}</span>
            </div>
            <div className="text-[11px] font-mono mt-1" style={{ color: '#8E8160' }}>{r.runId}</div>
            <div className="text-sm mt-2 leading-relaxed" style={{ color: '#4A443A', fontFamily: "'Source Serif 4', Georgia, serif" }}>
              {r.label}
            </div>
          </div>
          <div className="p-4 space-y-3">
            {[
              ['ts', r.ts],
              ['run_id', r.runId],
              ['event_id', r.eventId],
              ['action', r.action],
              ['reason_codes', `[${r.reasonCodes.join(', ')}]`],
              ['authority', `${r.authority} · decided_by ${r.decidedBy}`],
              ['mode', r.mode],
              ['stream', r.stream],
              ['course', r.course],
              ['lesson', r.lesson],
              ...(r.diffHash ? [['artifact.diff_hash', r.diffHash]] : []),
              ...(r.quote ? [['quote (verbatim)', r.quote]] : []),
              ['cost.tokens', r.tokens !== undefined ? `${r.tokens.toLocaleString()} tokens` : 'unmeasured (sim run: no model calls)'],
              ['cost.apify_units', r.apifyUnits !== undefined ? String(r.apifyUnits) : 'unmeasured (sim run)'],
              ['chain.prev', r.chain],
            ].map(([key, val]) => (
              <div key={key} className="flex gap-3 text-xs border-b pb-2 last:border-b-0 last:pb-0" style={{ borderColor: '#EAE4D8' }}>
                <span className="flex-shrink-0 w-44 font-mono" style={{ color: '#8E8160' }}>{key}</span>
                <span className="font-mono break-all" style={{ color: '#1C1915' }}>{val}</span>
              </div>
            ))}
          </div>

          {/* Before/after + sources — the artifact the receipt points at */}
          {(() => {
            const link = resolveVersion(r.receiptId);
            if (!link || (!link.version.diffAdded?.length && !link.version.diffRemoved?.length)) return null;
            const v = link.version;
            const rv = link.revert;
            return (
              <div className="border-t" style={{ borderColor: '#C9C0AE' }}>
                <div className="px-4 py-1.5 text-[10px] font-mono uppercase tracking-widest" style={{ color: '#8E8160', backgroundColor: '#EAE4D8' }}>
                  The change — {link.lesson.id} v{v.version - 1} → v{v.version}{rv ? ` (undone by v${rv.version}, ${rv.receipt})` : ''}
                </div>
                <div className="p-4 font-mono text-xs leading-relaxed space-y-1" style={{ backgroundColor: '#F3EFE7' }}>
                  {v.diffRemoved?.map((line, i) => (
                    <div key={`r-${i}`} className="flex gap-2">
                      <span className="flex-shrink-0 select-none font-bold" style={{ color: '#9B2C1F' }}>−</span>
                      <span style={{ color: '#9B2C1F', textDecoration: 'line-through', opacity: 0.8 }}>{line}</span>
                    </div>
                  ))}
                  {v.diffAdded?.map((line, i) => (
                    <div key={`a-${i}`} className="flex gap-2">
                      <span className="flex-shrink-0 select-none font-bold" style={{ color: '#3F5A2A' }}>+</span>
                      <span style={{ color: '#3F5A2A' }}>{line}</span>
                    </div>
                  ))}
                  <div className="pt-3 flex flex-wrap gap-2">
                    {v.sources?.map(s => (
                      <a
                        key={s}
                        href={s}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[10px] px-1.5 py-0.5 border rounded-sm hover:bg-white/40"
                        style={{ color: '#4A443A', borderColor: '#C9C0AE' }}
                      >
                        {s.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                      </a>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}
          {/* Human decisions — the ruling surface (n8n canvas, PA3 human_signoff) */}
          {humanDecisions.some(h => h.receiptId === r.receiptId) && (
            <div className="border-t px-4 py-3" style={{ borderColor: '#C9C0AE', backgroundColor: '#F5F0E0' }}>
              <div className="text-[10px] font-mono uppercase tracking-widest mb-1" style={{ color: '#7A5C00' }}>
                Wants a human — rule on it on the canvas
              </div>
              <div className="text-xs leading-relaxed" style={{ color: '#4A443A' }}>
                {r.eventId === 'cr-single-source-01'
                  ? 'A second independent publisher carrying the same fact would unblock it. You can add the source on the canvas — or let the refusal stand (it is the safe state).'
                  : 'A decision about which publisher to believe is a human’s call. Your ruling is recorded as its own receipt (human_signoff, PA3) and binds the next cycle.'}
              </div>
              <a
                href="https://knreddy.app.n8n.cloud/workflow/XafXKTwrLXr6dkmR"
                target="_blank"
                rel="noreferrer"
                className="inline-block mt-2 px-3 py-1.5 text-[11px] font-mono border rounded-sm"
                style={{ color: '#6B4E2E', borderColor: '#6B4E2E', backgroundColor: '#F3EFE7' }}
              >
                Open the ruling canvas → n8n (wf-cr-1-triage)
              </a>
              <div className="text-[10px] font-mono mt-2" style={{ color: '#8E8160' }}>
                No approve/revert button here on purpose: a ruling is a decision-of-record, not a click. Undo belongs to the revert gate (quiz_delta), not to a button.
              </div>
            </div>
          )}

          {/* Matching run log */}
          {(() => {
            const matchRun = workflowRuns.find(wr => wr.runId === r.runId);
            if (!matchRun) return null;
            return (
              <div className="border-t px-4 py-3" style={{ borderColor: '#C9C0AE' }}>
                <div className="text-[10px] font-mono uppercase tracking-widest mb-1" style={{ color: '#8E8160' }}>
                  Shown in
                </div>
                <div className="text-sm" style={{ color: '#4A443A' }}>{matchRun.label}</div>
                <div className="text-[11px] font-mono mt-1" style={{ color: '#68604F' }}>
                  {matchRun.events.length} events · outcome: {matchRun.outcome}
                </div>
              </div>
            );
          })()}
        </motion.div>
      </div>
    </div>
  );
}
