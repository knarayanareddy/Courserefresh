const statusConfig: Record<string, { label: string; color: string; bg: string; border: string }> = {
  // Machine actions — the closed set the POLICY node emits (receipts.jsonl decision.action)
  PUBLISH:   { label: 'PUBLISH',    color: '#3F5A2A', bg: '#EBF2E2', border: '#3F5A2A' },
  REVERT:    { label: 'REVERT',     color: '#9B2C1F', bg: '#F5E8E6', border: '#9B2C1F' },
  ESCALATE:  { label: 'ESCALATE',   color: '#9B2C1F', bg: '#F5E8E6', border: '#9B2C1F' },
  NO_CHANGE: { label: 'NO CHANGE',  color: '#5C564C', bg: '#EEEBE4', border: '#8E8160' },
  DISPATCH:  { label: 'DISPATCH',   color: '#96550A', bg: '#F7EFE4', border: '#96550A' },
  // Lesson-file states (what a lesson version is, not what the machine did)
  PUBLISHED: { label: 'PUBLISHED',  color: '#3F5A2A', bg: '#EBF2E2', border: '#3F5A2A' },
  REVERTED:  { label: 'REVERTED',   color: '#9B2C1F', bg: '#F5E8E6', border: '#9B2C1F' },
  DRAFT:     { label: 'DRAFT',      color: '#5C564C', bg: '#EEEBE4', border: '#8E8160' },
};

interface Props {
  status: string;
  size?: 'sm' | 'md';
}

export default function StatusBadge({ status, size = 'sm' }: Props) {
  const cfg = statusConfig[status] || statusConfig['NO_CHANGE'];
  const px = size === 'sm' ? 'px-2 py-0.5' : 'px-3 py-1';
  const text = size === 'sm' ? 'text-[10px]' : 'text-[11px]';
  return (
    <span
      className={`inline-block ${px} ${text} font-mono font-semibold tracking-widest uppercase rounded-sm border`}
      style={{ color: cfg.color, backgroundColor: cfg.bg, borderColor: cfg.border }}
    >
      {cfg.label}
    </span>
  );
}

export function AuthorityBadge({ level }: { level: string }) {
  const colors: Record<string, { color: string; bg: string }> = {
    PA0: { color: '#5C564C', bg: '#EEEBE4' },
    PA1: { color: '#96550A', bg: '#F7EFE4' },
    PA2: { color: '#3F5A2A', bg: '#EBF2E2' },
    PA3: { color: '#9B2C1F', bg: '#F5E8E6' },
  };
  const cfg = colors[level] || colors.PA0;
  return (
    <span
      className="inline-block px-2 py-0.5 text-[10px] font-mono font-semibold tracking-widest uppercase rounded-sm border"
      style={{ color: cfg.color, backgroundColor: cfg.bg, borderColor: cfg.color }}
    >
      {level}
    </span>
  );
}
