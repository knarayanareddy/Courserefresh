import { useState, useEffect } from 'react';

const phases = [
  { name: 'NOTICE', icon: '◉', color: '#6B4E2E' },
  { name: 'VERIFY', icon: '⊛', color: '#96550A' },
  { name: 'DECIDE', icon: '⊕', color: '#3F5A2A' },
  { name: 'ACT', icon: '↑', color: '#3F5A2A' },
  { name: 'LEARN', icon: '◎', color: '#7A5C00' },
  { name: 'REPORT', icon: '§', color: '#5C564C' },
];

const events = [
  'Scan: n8n releases · docs.n8n.io · npmjs — 2 new snapshots',
  'Quote anchored: “permissions.mode (was tool_permissions)”',
  'POLICY node: PUBLISH [material_breaking] · PA2 · fixture-judge',
  'lesson-04 v3→v4 written · quiz q2 regenerated · diff hashed',
  'DISPATCH [stuck_signals_met] · consent wall: 1 blocked (consent_missing)',
  'Digest: refusals first · chain ok (9 rows) · ≤ 4096 bytes',
];

export default function LiveLoopBadge() {
  const [activePhase, setActivePhase] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActivePhase(p => (p + 1) % phases.length);
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  const phase = phases[activePhase];

  return (
    <div className="border rounded-sm p-4 flex items-start gap-4" style={{ borderColor: '#8E8160', backgroundColor: '#EAE4D8' }}>
      <div className="flex-shrink-0">
        <div className="w-12 h-12 rounded-full flex items-center justify-center border-2 text-xl font-mono transition-all"
          style={{ borderColor: phase.color, color: phase.color, backgroundColor: '#F3EFE7' }}>
          {phase.icon}
        </div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] font-mono font-bold uppercase tracking-widest" style={{ color: phase.color }}>{phase.name}</span>
          <span className="inline-block w-1.5 h-1.5 rounded-full animate-pulse" style={{ backgroundColor: phase.color }} />
        </div>
        <div className="text-xs font-mono truncate" style={{ color: '#4A443A' }}>{events[activePhase]}</div>
        {/* Phase dots */}
        <div className="flex gap-1.5 mt-2">
          {phases.map((p, i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full transition-all duration-300"
              style={{ backgroundColor: i === activePhase ? p.color : '#C9C0AE' }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
