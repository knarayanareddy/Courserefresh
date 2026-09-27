import { motion } from 'framer-motion';

/**
 * The problem, as dots. 52 red = subject changes in a year the course never saw;
 * 2 blue = course updates in that same year. The counts are a visual metaphor,
 * not measured figures — the label under the chart says so.
 */
export default function DotsVisual() {
  const red = 52;
  const blue = 2;
  const total = red + blue;
  const perRow = 9;
  const rows = Math.ceil(total / perRow);
  const dotR = 4.5;
  const stepX = 13;
  const stepY = 18;
  const width = 342;
  const height = 10 + (rows - 1) * stepY + 52;

  const dots: { id: number; kind: 'red' | 'blue' }[] = [];
  for (let i = 0; i < red; i++) dots.push({ id: i, kind: 'red' });
  for (let i = 0; i < blue; i++) dots.push({ id: red + i, kind: 'blue' });

  return (
    <div className="w-full" style={{ fontFamily: "'IBM Plex Sans', system-ui, sans-serif" }}>
      <div className="inline-block border rounded-sm p-5" style={{ borderColor: '#C9C0AE', backgroundColor: '#F3EFE7' }}>
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="52 red dots for weekly subject changes, 2 blue dots for yearly course updates"
        >
          {dots.map((d, i) => {
            const row = Math.floor(i / perRow);
            const col = i % perRow;
            const isBlue = d.kind === 'blue';
            const x = 14 + col * stepX;
            const y = 10 + row * stepY;
            return (
              <motion.circle
                key={d.id}
                cx={x}
                cy={y}
                r={dotR}
                fill={isBlue ? '#2F5D8A' : '#9B2C1F'}
                stroke={isBlue ? '#1C4E77' : '#7A1F16'}
                strokeWidth={0.8}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ delay: 0.1 + i * 0.04, duration: 0.3, ease: 'easeOut' }}
                style={{ transformOrigin: `${x}px ${y}px` }}
              />
            );
          })}
          {/* Legend */}
          <text x="14" y={10 + (rows - 1) * stepY + 26} fontSize="10" fontFamily="'IBM Plex Mono', monospace" fill="#68604F">
            <tspan fill="#9B2C1F" fontWeight="700">● 52</tspan>
            <tspan> subject changes the course never saw</tspan>
          </text>
          <text x="14" y={10 + (rows - 1) * stepY + 39} fontSize="10" fontFamily="'IBM Plex Mono', monospace" fill="#68604F">
            <tspan fill="#2F5D8A" fontWeight="700">● 2</tspan>
            <tspan> course updates in the same year</tspan>
          </text>
        </svg>
        <div className="mt-2 text-[10px] font-mono" style={{ color: '#8E8160' }}>
          counts are a visual metaphor, not measured figures
        </div>
      </div>
    </div>
  );
}
