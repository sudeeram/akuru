'use client';
/* SVG diagrams require role=img; an HTML img cannot host interactive vector elements. */
/* eslint-disable jsx-a11y/prefer-tag-over-role */
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Play, Pause, RotateCcw } from 'lucide-react';
export function Diagram({
  kind,
  interactive = false,
}: {
  kind: string;
  interactive?: boolean;
}) {
  const [playing, setPlaying] = useState(false);
  const [filled, setFilled] = useState(3);
  if (!kind) return null;
  return (
    <div className={`diagram ${playing ? 'playing' : ''}`}>
      <svg
        viewBox="0 0 480 230"
        role="img"
        aria-label={
          (
            {
              fraction: 'Eight equal sections, three shaded',
              triangle: 'Triangle with angles 50 degrees, 60 degrees and x',
              coordinates: 'Coordinate plane with P at 4, 3',
              particles: 'Particles in a solid compared with a liquid',
              forces: 'Box with opposing 8 and 12 newton forces',
              circuit: 'Series circuit with an open switch',
              network:
                'Home devices connected through a router to the internet',
              algorithm: 'Algorithm: start at 3, double, then add 4',
              reading: 'Reading and evidence diagram',
            } as Record<string, string>
          )[kind]
        }
      >
        <defs>
          <marker
            id={`arrow-${kind}`}
            markerWidth="8"
            markerHeight="8"
            refX="7"
            refY="4"
            orient="auto"
          >
            <path d="M0 0L8 4L0 8" fill="#4779c9" />
          </marker>
        </defs>
        {kind === 'fraction' && (
          <>
            {Array.from({ length: 8 }, (_, i) => (
              <rect
                key={i}
                x={64 + (i % 4) * 90}
                y={28 + Math.floor(i / 4) * 77}
                width="78"
                height="65"
                rx="8"
                fill={i < filled ? '#5481d9' : '#edf2fa'}
                stroke={i < filled ? '#5481d9' : '#cad7ec'}
                onClick={interactive ? () => setFilled(i + 1) : undefined}
                style={{ cursor: interactive ? 'pointer' : undefined }}
              />
            ))}
            <text
              x="240"
              y="213"
              textAnchor="middle"
              fontSize="18"
              fill="#446083"
            >
              {filled} of 8 equal sections
            </text>
          </>
        )}
        {kind === 'triangle' && (
          <>
            <path
              d="M70 183L410 183L217 37Z"
              fill="#eef3ff"
              stroke="#4b79ce"
              strokeWidth="3"
            />
            <text x="111" y="168" fontSize="22">
              50°
            </text>
            <text x="345" y="168" fontSize="22">
              60°
            </text>
            <text x="212" y="84" fontSize="22" fill="#2e65d5">
              x°
            </text>
            <text
              x="240"
              y="218"
              textAnchor="middle"
              fontSize="13"
              fill="#77889e"
            >
              Diagram not drawn to scale
            </text>
          </>
        )}
        {kind === 'coordinates' && (
          <>
            {Array.from({ length: 6 }, (_, i) => (
              <g key={i}>
                <path
                  d={`M100 ${190 - i * 30}H350 M${100 + i * 45} 30V190`}
                  stroke="#dce5f2"
                />
                <text x={96 + i * 45} y="211" fontSize="12">
                  {i}
                </text>
                <text x="77" y={194 - i * 30} fontSize="12">
                  {i}
                </text>
              </g>
            ))}
            <path d="M100 25V190H365" stroke="#6585b5" strokeWidth="2" />
            <circle cx="280" cy="100" r="6" fill="#316bd7" />
            <path d="M280 190V100H100" stroke="#86a7dd" strokeDasharray="5" />
            <text x="291" y="91" fontSize="18" fill="#2e65d5">
              P
            </text>
            <text x="372" y="195">
              x
            </text>
            <text x="96" y="18">
              y
            </text>
          </>
        )}
        {kind === 'particles' && (
          <>
            <rect
              x="35"
              y="38"
              width="175"
              height="145"
              rx="12"
              fill="#f0f5fb"
              stroke="#d2deee"
            />
            <rect
              x="270"
              y="38"
              width="175"
              height="145"
              rx="12"
              fill="#f0f8f5"
              stroke="#d0e6dc"
            />
            {Array.from({ length: 16 }, (_, i) => (
              <g key={i}>
                <circle
                  className="solid-particle"
                  cx={68 + (i % 4) * 35}
                  cy={64 + Math.floor(i / 4) * 32}
                  r="8"
                  fill="#5481d9"
                />
                <circle
                  className="liquid-particle"
                  style={{ animationDelay: `-${i * 0.21}s` }}
                  cx={296 + (i % 4) * 37 + (i % 2) * 5}
                  cy={63 + Math.floor(i / 4) * 31 + (i % 3) * 4}
                  r="8"
                  fill="#52a183"
                />
              </g>
            ))}
            <path
              d="M220 107H257"
              stroke="#4779c9"
              strokeWidth="2"
              markerEnd={`url(#arrow-${kind})`}
            />
            <text x="120" y="212" textAnchor="middle">
              Solid
            </text>
            <text x="355" y="212" textAnchor="middle">
              Liquid
            </text>
          </>
        )}
        {kind === 'forces' && (
          <>
            <rect
              x="185"
              y="72"
              width="110"
              height="92"
              rx="9"
              fill="#edf3ff"
              stroke="#6e92ce"
              strokeWidth="2"
            />
            <text x="240" y="126" textAnchor="middle">
              Box
            </text>
            <path
              d="M185 118H85 M295 118H435"
              stroke="#4779c9"
              strokeWidth="4"
              markerEnd={`url(#arrow-${kind})`}
            />
            <text x="115" y="96" fontSize="20">
              8 N
            </text>
            <text x="350" y="96" fontSize="20">
              12 N
            </text>
          </>
        )}
        {kind === 'circuit' && (
          <>
            <path
              d="M215 175H90V60H230 M300 60H385V175H247"
              fill="none"
              stroke="#587bab"
              strokeWidth="3"
            />
            <path
              d="M228 60L286 30 M220 160V190 M242 151V199"
              stroke="#375d95"
              strokeWidth="3"
            />
            <circle
              cx="290"
              cy="175"
              r="20"
              fill="white"
              stroke="#587bab"
              strokeWidth="3"
            />
            <path
              d="M277 162L303 188M303 162L277 188"
              stroke="#587bab"
              strokeWidth="2"
            />
            <circle cx="230" cy="60" r="4" fill="#375d95" />
            <circle cx="300" cy="60" r="4" fill="#375d95" />
            <text x="268" y="105" textAnchor="middle" fontSize="14">
              Open switch
            </text>
          </>
        )}
        {kind === 'network' && (
          <>
            <path
              d="M105 58L245 114M105 173L245 114M245 114H383"
              stroke="#88a7d8"
              strokeWidth="2"
              strokeDasharray="5"
            />
            <rect
              x="32"
              y="30"
              width="105"
              height="56"
              rx="10"
              fill="#eaf1ff"
            />
            <text x="84" y="64" textAnchor="middle" fontSize="15">
              Laptop
            </text>
            <rect
              x="32"
              y="147"
              width="105"
              height="56"
              rx="10"
              fill="#eaf1ff"
            />
            <text x="84" y="181" textAnchor="middle" fontSize="15">
              Tablet
            </text>
            <rect
              x="186"
              y="84"
              width="115"
              height="63"
              rx="12"
              fill="#537bd0"
            />
            <text
              x="244"
              y="122"
              textAnchor="middle"
              fontSize="17"
              fill="white"
            >
              Router
            </text>
            <circle cx="399" cy="114" r="49" fill="#e7f3ed" />
            <text x="399" y="120" textAnchor="middle" fontSize="15">
              Internet
            </text>
          </>
        )}
        {kind === 'algorithm' && (
          <>
            {['x = 3', 'x × 2', 'x + 4'].map((t, i) => (
              <g key={t}>
                <rect
                  x={24 + i * 160}
                  y="80"
                  width="112"
                  height="65"
                  rx="12"
                  fill={i === 0 ? '#ecf0ff' : '#e9f3ff'}
                  stroke="#adc4e9"
                />
                <text
                  x={80 + i * 160}
                  y="120"
                  textAnchor="middle"
                  fontSize="22"
                >
                  {t}
                </text>
                {i < 2 && (
                  <path
                    d={`M${138 + i * 160} 112h35`}
                    stroke="#4779c9"
                    strokeWidth="2"
                    markerEnd={`url(#arrow-${kind})`}
                  />
                )}
              </g>
            ))}
          </>
        )}
        {kind === 'reading' && (
          <>
            {['Notice the words', 'Make a connection', 'Support your idea'].map(
              (t, i) => (
                <g key={t}>
                  <circle cx="80" cy={45 + i * 70} r="19" fill="#fff1dd" />
                  <text
                    x="80"
                    y={51 + i * 70}
                    textAnchor="middle"
                    fill="#a17434"
                  >
                    {i + 1}
                  </text>
                  <text x="120" y={51 + i * 70} fontSize="20" fill="#52647e">
                    {t}
                  </text>
                </g>
              ),
            )}
          </>
        )}
      </svg>
      {interactive && kind === 'particles' && (
        <Button variant="outline" onClick={() => setPlaying(!playing)}>
          {playing ? <Pause size={15} /> : <Play size={15} />}{' '}
          {playing ? 'Pause' : 'Animate particles'}
        </Button>
      )}
      {interactive && kind === 'fraction' && (
        <div className="diagram-controls">
          <label htmlFor="fraction-range">
            Shaded sections: {filled} / 8 = {(filled / 8) * 100}%
          </label>
          <input
            id="fraction-range"
            type="range"
            min="0"
            max="8"
            value={filled}
            onChange={(e) => setFilled(Number(e.target.value))}
          />
          <Button variant="ghost" onClick={() => setFilled(3)}>
            <RotateCcw size={14} />
            Reset
          </Button>
        </div>
      )}
    </div>
  );
}
