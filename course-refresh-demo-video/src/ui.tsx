import { useEffect, useState, type CSSProperties, type ReactNode } from "react";

type RevealProps = {
  show?: boolean;
  delay?: number;
  y?: number;
  x?: number;
  blur?: number;
  scale?: number;
  duration?: number;
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
};

/** Apple-style entrance: fade + rise + de-blur, on a long ease-out. */
export function Reveal({
  show = true,
  delay = 0,
  y = 28,
  x = 0,
  blur = 12,
  scale = 1,
  duration = 900,
  className = "",
  style,
  children,
}: RevealProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setMounted(true));
    return () => cancelAnimationFrame(id);
  }, []);
  const on = show && mounted;
  return (
    <div
      className={className}
      style={{
        opacity: on ? 1 : 0,
        transform: on ? "none" : `translate(${x}px, ${y}px) scale(${scale})`,
        filter: on ? "blur(0px)" : `blur(${blur}px)`,
        transition: `opacity ${duration}ms var(--ease) ${delay}ms, transform ${duration}ms var(--ease) ${delay}ms, filter ${duration}ms var(--ease) ${delay}ms`,
        willChange: "opacity, transform, filter",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

/** Becomes true `ms` after `active` turns on. */
export function useDelayed(active: boolean, ms: number) {
  const [v, setV] = useState(false);
  useEffect(() => {
    if (!active) {
      setV(false);
      return;
    }
    const id = window.setTimeout(() => setV(true), ms);
    return () => window.clearTimeout(id);
  }, [active, ms]);
  return v;
}

export function Eyebrow({ children, color = "var(--blue)" }: { children: ReactNode; color?: string }) {
  return (
    <div
      className="text-[26px] font-semibold uppercase tracking-[0.18em]"
      style={{ color }}
    >
      {children}
    </div>
  );
}

export function Pill({
  children,
  color,
  className = "",
}: {
  children: ReactNode;
  color: string;
  className?: string;
}) {
  return (
    <span
      className={`mono inline-flex items-center gap-2 rounded-full px-5 py-2 text-[22px] font-medium ${className}`}
      style={{
        color,
        background: `color-mix(in srgb, ${color} 14%, transparent)`,
        border: `1px solid color-mix(in srgb, ${color} 40%, transparent)`,
      }}
    >
      {children}
    </span>
  );
}

export function Window({
  title,
  children,
  className = "",
  style,
}: {
  title: string;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div className={`glass overflow-hidden rounded-[28px] ${className}`} style={style}>
      <div className="flex items-center gap-3 border-b border-white/[0.07] px-7 py-5">
        <span className="h-[15px] w-[15px] rounded-full bg-[#ff5f57]" />
        <span className="h-[15px] w-[15px] rounded-full bg-[#febc2e]" />
        <span className="h-[15px] w-[15px] rounded-full bg-[#28c840]" />
        <span className="mono ml-4 text-[20px] text-[var(--ink-3)]">{title}</span>
      </div>
      {children}
    </div>
  );
}

export type SceneProps = { step: number };
