import { cn } from "@/lib/utils";

/** Decorative beam field from the binding front-end reference. */
export function BeamField({ className }: { className?: string }) {
  const width = 1000;
  const height = 700;
  const focal = { x: width * 0.9, y: height * 0.5 };
  const dots = Array.from({ length: 14 * 20 }, (_, index) => {
    const row = Math.floor(index / 20);
    const column = index % 20;
    return {
      x: 40 + (column / 19) * (width * 0.5),
      y: 40 + (row / 13) * (height - 80),
      delay: (column * 0.12 + row * 0.09) % 3,
    };
  });
  const beams = Array.from({ length: 16 }, (_, index) => {
    const position = index / 15;
    return {
      x: width * 0.52,
      y: 60 + position * (height - 120),
      opacity: Math.max(0.08, 0.5 - Math.abs(position - 0.5) * 0.7),
    };
  });

  return (
    <div
      aria-hidden="true"
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      <svg
        className="h-full w-full"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="xMidYMid slice"
        fill="none"
      >
        <defs>
          <radialGradient id="login-beam-focal" cx="90%" cy="50%" r="18%">
            <stop offset="0%" stopColor="var(--hero)" stopOpacity="0.9" />
            <stop offset="100%" stopColor="var(--hero)" stopOpacity="0" />
          </radialGradient>
        </defs>
        <g fill="var(--hero)">
          {dots.map((dot, index) => (
            <circle
              key={index}
              cx={dot.x}
              cy={dot.y}
              r={1.4}
              style={{
                opacity: 0.3,
                animation: `dot-shimmer 4s ease-in-out ${dot.delay}s infinite`,
              }}
            />
          ))}
        </g>
        <g stroke="var(--hero)" strokeWidth={1}>
          {beams.map((beam, index) => (
            <g key={index}>
              <line
                x1={beam.x}
                y1={beam.y}
                x2={focal.x}
                y2={focal.y}
                strokeOpacity={beam.opacity * 0.35}
              />
              <line
                x1={beam.x}
                y1={beam.y}
                x2={focal.x}
                y2={focal.y}
                strokeOpacity={beam.opacity}
                className="beam-flow"
                style={{ animationDelay: `${(index % 5) * 0.2}s` }}
              />
            </g>
          ))}
        </g>
        <circle cx={focal.x} cy={focal.y} r={120} fill="url(#login-beam-focal)" />
        <circle cx={focal.x} cy={focal.y} r={3} fill="var(--hero)" />
      </svg>
    </div>
  );
}
