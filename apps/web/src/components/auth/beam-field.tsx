import { memo } from "react";

import { cn } from "@/lib/utils";

const WIDTH = 1000;
const HEIGHT = 700;
const FOCAL = { x: WIDTH * 0.9, y: HEIGHT * 0.5 };
const DOTS = Array.from({ length: 14 * 20 }, (_, index) => {
  const row = Math.floor(index / 20);
  const column = index % 20;
  return {
    x: 40 + (column / 19) * (WIDTH * 0.5),
    y: 40 + (row / 13) * (HEIGHT - 80),
    delay: (column * 0.12 + row * 0.09) % 3,
  };
});
const BEAMS = Array.from({ length: 16 }, (_, index) => {
  const position = index / 15;
  return {
    x: WIDTH * 0.52,
    y: 60 + position * (HEIGHT - 120),
    opacity: Math.max(0.08, 0.5 - Math.abs(position - 0.5) * 0.7),
  };
});

/** Decorative beam field from the binding front-end reference. */
export const BeamField = memo(function BeamField({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      <svg
        className="h-full w-full"
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
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
          {DOTS.map((dot, index) => (
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
          {BEAMS.map((beam, index) => (
            <g key={index}>
              <line
                x1={beam.x}
                y1={beam.y}
                x2={FOCAL.x}
                y2={FOCAL.y}
                strokeOpacity={beam.opacity * 0.35}
              />
              <line
                x1={beam.x}
                y1={beam.y}
                x2={FOCAL.x}
                y2={FOCAL.y}
                strokeOpacity={beam.opacity}
                className="beam-flow"
                style={{ animationDelay: `${(index % 5) * 0.2}s` }}
              />
            </g>
          ))}
        </g>
        <circle cx={FOCAL.x} cy={FOCAL.y} r={120} fill="url(#login-beam-focal)" />
        <circle cx={FOCAL.x} cy={FOCAL.y} r={3} fill="var(--hero)" />
      </svg>
    </div>
  );
});
