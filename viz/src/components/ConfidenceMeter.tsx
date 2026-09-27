export function ConfidenceMeter({ value, size = "sm" }: { value: number; size?: "sm" | "md" | "lg" }) {
  const pct = Math.round(value * 100);
  const color = value >= 0.9 ? "#3F5A2A" : value >= 0.75 ? "#96550A" : "#9B2C1F";
  const barH = size === "lg" ? 8 : size === "md" ? 6 : 4;
  const width = size === "lg" ? 120 : size === "md" ? 80 : 60;

  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
      <span
        style={{
          display: "inline-block",
          width,
          height: barH,
          background: "var(--paper)",
          border: "1px solid var(--rule)",
          borderRadius: 2,
          overflow: "hidden",
        }}
      >
        <span
          style={{
            display: "block",
            width: `${pct}%`,
            height: "100%",
            background: color,
            transition: "width 0.4s ease",
          }}
        />
      </span>
      <span
        style={{
          fontSize: 11,
          fontFamily: "var(--font-mono)",
          color: color,
          fontWeight: 500,
          minWidth: 32,
        }}
      >
        {pct}%
      </span>
    </span>
  );
}
