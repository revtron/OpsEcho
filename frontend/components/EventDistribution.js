import { useState, useEffect } from 'react';

const COLORS = {
  kubernetes: '#3B82F6', terraform: '#8B5CF6', ec2: '#F59E0B',
  aws: '#EC4899', docker: '#06B6D4', git: '#10B981',
  other: '#6B7280'
};

const LABELS = {
  kubernetes: 'K8s', terraform: 'TF', ec2: 'EC2',
  aws: 'AWS', docker: 'Docker', git: 'Git', other: 'Other'
};

function describeArc(cx, cy, r, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y} Z`;
}

function polarToCartesian(cx, cy, r, angleDeg) {
  const rad = (angleDeg - 90) * Math.PI / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

export default function EventDistribution({ events }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (events.length === 0) return null;

  const counts = {};
  events.forEach(e => {
    const key = LABELS[e.event_type] || LABELS.other;
    counts[key] = (counts[key] || 0) + 1;
  });

  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const cx = 80, cy = 80, r = 60;
  let currentAngle = 0;
  const slices = sorted.map(([key, val]) => {
    const angle = (val / total) * 360;
    const slice = { key, val, pct: (val / total) * 100, startAngle: currentAngle, endAngle: currentAngle + angle };
    currentAngle += angle;
    return slice;
  });

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 h-full">
      <h3 className="text-sm font-semibold text-gray-800 dark:text-white mb-3">Event Distribution</h3>

      <div className="flex items-center gap-4">
        {/* Donut */}
        <div className="flex-shrink-0">
          {mounted ? (
            <svg width="160" height="160" viewBox="0 0 160 160">
              {slices.map(s => {
                const color = COLORS[Object.entries(LABELS).find(([,v]) => v === s.key)?.[0]] || '#6B7280';
                return (
                  <path
                    key={s.key}
                    d={describeArc(cx, cy, r, s.startAngle, s.endAngle)}
                    fill={color}
                    opacity="0.9"
                  />
                );
              })}
              <circle cx={cx} cy={cy} r="32" fill="white" className="dark:fill-gray-800" />
              <text x={cx} y={cy - 4} textAnchor="middle" className="fill-gray-800 dark:fill-white text-xs font-bold" fontSize="13">
                {total}
              </text>
              <text x={cx} y={cy + 11} textAnchor="middle" className="fill-gray-500" fontSize="10">
                events
              </text>
            </svg>
          ) : (
            <div className="w-[160px] h-[160px] flex items-center justify-center text-gray-400 text-xs">Loading...</div>
          )}
        </div>

        {/* Legend */}
        <div className="flex-1 min-w-0 space-y-1.5">
          {sorted.map(([key, val]) => {
            const color = COLORS[Object.entries(LABELS).find(([,v]) => v === key)?.[0]] || '#6B7280';
            return (
              <div key={key} className="flex items-center gap-2 text-xs">
                <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                <span className="text-gray-600 dark:text-gray-400 flex-1 truncate">{key}</span>
                <span className="font-medium text-gray-800 dark:text-gray-200">{val}</span>
                <span className="text-gray-400 w-8 text-right">{(val / total * 100).toFixed(0)}%</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
