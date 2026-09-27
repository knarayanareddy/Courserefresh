import { motion } from 'framer-motion';

// Real data, from the repo's own artifacts:
//   hero run cr-20260926-1726-793 (specs/evidence/.../receipts.jsonl, digest.md)
//   lesson files under course/agent-ops/ (v3→v4→v5 on lesson-04, v1→v2 on lesson-03)
interface DataPoint {
  version: number;
  date: string;
  status: string;        // machine action on that version: PUBLISHED / REFUSED / REVERTED / DRAFT / UNCHANGED
  event?: string;        // reason code / one-line story
  baseline?: boolean;    // authored pre-run (PA3, human-written) — not loop output
}

interface CourseRow { refusals?: boolean; id: string; title: string; color: string; data: DataPoint[] }

const courses: CourseRow[] = [
  {
    id: 'lesson-03-apify-inputs',
    title: 'lesson-03 — Apify inputs (v1 → v2)',
    color: '#3F5A2A',
    data: [
      { version: 1, date: 'pre-run', status: 'PUBLISHED', event: 'authored by the author (PA3) — baseline', baseline: true },
      { version: 2, date: '2026.09.26', status: 'PUBLISHED', event: 'PUBLISH [material_new_capability] — corroborated, within budget' },
    ] as DataPoint[],
  },
  {
    id: 'lesson-04-tool-permissions',
    title: 'lesson-04 — Tool permissions (v3 → v4 → v5)',
    color: '#96550A',
    data: [
      { version: 3, date: 'pre-run', status: 'PUBLISHED', event: 'authored baseline (PA3) — teaches tool_permissions.tools', baseline: true },
      { version: 4, date: '2026.09.26', status: 'PUBLISHED', event: 'PUBLISH [material_breaking] — n8n 1.85 renames tool_permissions → permissions.mode; quiz q2 regenerated' },
      { version: 5, date: '2026.09.26', status: 'REVERTED', event: 'REVERT [revert_gate_satisfied] — quiz_delta −0.04 at n=6 after 60h; v3 restored' },
    ] as DataPoint[],
  },
  {
    refusals: true,
    id: 'run-cr-20260926-1726-793',
    title: 'hero run — refusals and walls (no version written)',
    color: '#9B2C1F',
    data: [
      { version: 0, date: '2026.09.26', status: 'REFUSED', event: 'ESCALATE [injection_or_jailbreak] — “IGNORE ALL PREVIOUS INSTRUCTIONS…” scored 0.93' },
      { version: 0, date: '2026.09.26', status: 'REFUSED', event: 'ESCALATE [insufficient_corroboration] — single source; second publisher would unblock' },
      { version:  0, date: '2026.09.26', status: 'REFUSED', event: 'ESCALATE [source_conflict] — publishers disagree; human decides' },
      { version: 0, date: '2026.09.26', status: 'REFUSED',  event: 'ESCALATE [over_budget] — change arrived after the publish cap was spent (2/6)' },
    ] as DataPoint[],
  },
];

function Sparkline({ data, color, isRefusalRow = false }: { data: DataPoint[]; color: string; isRefusalRow?: boolean }) {
  const width = 380;
  const height = 80;
  const padding = { left: 30, right: 20, top: 10, bottom: 20 };
  const innerW = width - padding.left - padding.right;
  const innerH = height - padding.top - padding.bottom;

  // no percentages invented: refusal rows keep a flat dashed baseline;
  // published/reverted rows slot points evenly along the timeline
  const points = data.map((d, i) => {
    const x = padding.left + (i / Math.max(1, data.length - 1)) * innerW;
    const y = padding.top + (1 - 0.5) * innerH; // mid-line
    return { x, y, d };
  });

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ');

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: 'visible' }}>
      {/* Grid lines */}
      {[0, 0.5, 1].map((t) => {
        const y = padding.top + t * innerH;
        return (
          <g key={t}>
            <line x1={padding.left} y1={y} x2={width - padding.right} y2={y} stroke="#C9C0AE" strokeWidth={0.5} strokeDasharray="2,2" />
          </g>
        );
      })}

      {/* Line */}
      <motion.path
        d={pathD}
        fill="none"
        stroke={color}
        strokeWidth={isRefusalRow ? 1 : 2}
        strokeDasharray={isRefusalRow ? '4,3' : undefined}
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.2, ease: 'easeInOut' }}
      />

      {/* Points */}
      {points.map((p, i) => {
        const isRevert = p.d.status === 'REVERTED';
        const isRefused = p.d.status === 'REFUSED';
        const pointColor = isRevert ? '#9B2C1F' : isRefused ? '#8E8160' : color;
        return (
          <g key={i}>
            <motion.circle
              cx={p.x}
              cy={p.y}
              r={5}
              fill={isRefused ? '#EAE4D8' : pointColor}
              stroke={pointColor}
              strokeWidth={1.5}
              initial={{ scale:  0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.8 + i * 0.1 }}
            />
            {/* Version label above the point (refusal rows wrote no version) */}
            {!isRefusalRow && (
              <text x={p.x} y={p.y - 9} textAnchor="middle" fontSize={8} fontFamily="'IBM Plex Mono', monospace" fill={pointColor} fontWeight="600">
                v{p.d.version}
              </text>
            )}
            {isRefusalRow && (
              <text x={p.x} y={p.y - 9} textAnchor="middle" fontSize={8} fontFamily="'IBM Plex Mono', monospace" fill={pointColor} fontWeight="600">
                ⊘
              </text>
            )}
            {/* Date label */}
            <text x={p.x} y={height - 2} textAnchor="middle" fontSize={7} fontFamily="'IBM Plex Mono', monospace" fill="#8E8160">
              {p.d.date}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

export default function ProgressionChart() {
  return (
    <div className="border rounded-sm overflow-hidden" style={{ borderColor: '#8E8160', backgroundColor: '#F3EFE7' }}>
      <div className="px-4 py-3 border-b" style={{ borderColor: '#C9C0AE', backgroundColor: '#EAE4D8' }}>
        <div className="text-[11px] font-mono uppercase tracking-widest mb-0.5" style={{ color: '#8E8160' }}>
          Version progression — the real written history
        </div>
        <div className="text-xs" style={{ color: '#68604F' }}>
          Every version the loop actually wrote, and every refusal that wrote none. No invented scores: cohort quiz_delta prints <span className="font-mono">unmeasured</span> until a consented live cohort runs (sim data: quiz_delta −0.04 @ n=6, labeled).
 </div>
      </div>
      <div className="p-4 space-y-6">
        {courses.map((c) => (
          <div key={c.id}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[11px] font-mono font-semibold" style={{ color: c.color }}>{c.title}</span>
              {c.refusals && (
                <span className="text-[10px] font-mono px-1.5 py-0.5 border rounded-sm" style={{ color: '#9B2C1F', borderColor: '#9B2C1F' }}>
                  no version written
                </span>
              )}
            </div>
            <div className="overflow-x-auto">
              <Sparkline data={c.data} color={c.color} isRefusalRow={!!c.refusals} />
            </div>
            {/* Event timeline */}
            <div className="mt-2 space-y-1">
              {c.data.map((d, i) => (
                <div key={i} className="flex items-start gap-2 text-[10px] font-mono" style={{ color: '#68604F' }}>
                  <span style={{ color: d.status === 'REVERTED' ? '#9B2C1F' : d.status === 'REFUSED' ? '#8E8160' : c.color }}>
                    {d.status === 'REVERTED' ? '↺' : d.status === 'REFUSED' ? '⊘' : '↑'}
                  </span>
                  <span className="flex-shrink-0">{d.date}</span>
                  <span className="text-[10px]">{d.event}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="px-4 py-2 border-t text-[10px] font-mono" style={{ borderColor: '#C9C0AE', color: '#8E8160' }}>
        sources: specs/evidence/cr-20260926-1726-793 (receipts.jsonl, digest.md) · course/agent-ops diffs · quiz_delta −0.04 @ n=6 labeled as the hero run’s only measured learner metric
      </div>
    </div>
  );
}
