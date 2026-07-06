import { useState, useMemo, useEffect } from 'react';

function fmtTime(d) {
  const h = d.getHours();
  const m = String(d.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
}

function fmtDate(d) {
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return `${months[d.getMonth()]} ${d.getDate()}, ${fmtTime(d)}`;
}

const STATUS_COLORS = {
  healthy:  { fill: '#22c55e', label: 'Healthy', bar: 'bg-green-500' },
  degraded: { fill: '#eab308', label: 'Degraded', bar: 'bg-yellow-500' },
  failed:   { fill: '#ef4444', label: 'Failed', bar: 'bg-red-500' },
  pending:  { fill: '#3b82f6', label: 'Pending', bar: 'bg-blue-500' },
};

const TYPE_COLORS = {
  kubernetes: { fill: '#3b82f6', label: 'K8s' },
  terraform:  { fill: '#a855f7', label: 'TF' },
  git:        { fill: '#22c55e', label: 'Git' },
  ec2:        { fill: '#f97316', label: 'EC2' },
};

function groupByHour(events, hoursBack) {
  const now = Date.now();
  const interval = hoursBack <= 24 ? 3600000 : hoursBack <= 48 ? 7200000 : 14400000;
  const slots = Math.ceil((hoursBack * 3600000) / interval);
  const buckets = [];

  for (let i = slots - 1; i >= 0; i--) {
    const start = now - (i + 1) * interval;
    const end = now - i * interval;
    const d = new Date(start);
    const label = interval === 3600000 ? fmtTime(d) : fmtDate(d);
    buckets.push({
      label,
      start,
      end,
      total: 0,
      byStatus: { healthy: 0, degraded: 0, failed: 0, pending: 0 },
      byType: {},
    });
  }

  events.forEach(e => {
    const t = new Date(e.timestamp).getTime();
    for (const b of buckets) {
      if (t >= b.start && t < b.end) {
        b.total++;
        b.byStatus[e.status] = (b.byStatus[e.status] || 0) + 1;
        b.byType[e.event_type] = (b.byType[e.event_type] || 0) + 1;
        break;
      }
    }
  });

  return buckets;
}

function TimeSeriesChart({ buckets, chartType }) {
  if (buckets.length === 0) return null;

  const maxVal = Math.max(...buckets.map(b => b.total), 1);
  const svgW = 800;
  const svgH = 200;
  const pad = { top: 20, right: 20, bottom: 40, left: 40 };
  const w = svgW - pad.left - pad.right;
  const h = svgH - pad.top - pad.bottom;
  const barW = Math.max(4, Math.min(30, w / buckets.length - 4));

  const yTicks = 5;
  const yStep = Math.ceil(maxVal / yTicks);

  return (
    <svg viewBox={`0 0 ${svgW} ${svgH}`} className="w-full" style={{ maxHeight: '220px' }}>
      {/* Grid lines */}
      {Array.from({ length: yTicks + 1 }, (_, i) => {
        const y = pad.top + h - (i / yTicks) * h;
        return (
          <g key={i}>
            <line x1={pad.left} y1={y} x2={svgW - pad.right} y2={y} stroke="#e5e7eb" strokeWidth="1" className="dark:stroke-gray-700" />
            <text x={pad.left - 8} y={y + 4} textAnchor="end" className="fill-gray-400 dark:fill-gray-500 text-xs">
              {Math.round(i * yStep)}
            </text>
          </g>
        );
      })}

      {/* Bars */}
      {buckets.map((b, i) => {
        const x = pad.left + (i / buckets.length) * w;

        if (chartType === 'status') {
          const statuses = ['failed', 'degraded', 'pending', 'healthy'];
          let yOff = 0;
          return statuses.map(s => {
            const val = b.byStatus[s] || 0;
            if (val === 0) return null;
            const barH = (val / maxVal) * h;
            const y = pad.top + h - yOff - barH;
            yOff += barH;
            return (
              <rect
                key={s}
                x={x}
                y={y}
                width={barW}
                height={barH}
                fill={STATUS_COLORS[s].fill}
                rx="2"
                className="transition-opacity hover:opacity-80"
              >
                <title>{`${STATUS_COLORS[s].label}: ${val} (${b.label})`}</title>
              </rect>
            );
          });
        }

        if (chartType === 'type') {
          const types = Object.keys(TYPE_COLORS);
          let yOff = 0;
          return types.map(t => {
            const val = b.byType[t] || 0;
            if (val === 0) return null;
            const barH = (val / maxVal) * h;
            const y = pad.top + h - yOff - barH;
            yOff += barH;
            return (
              <rect
                key={t}
                x={x}
                y={y}
                width={barW}
                height={barH}
                fill={TYPE_COLORS[t].fill}
                rx="2"
                className="transition-opacity hover:opacity-80"
              >
                <title>{`${TYPE_COLORS[t].label}: ${val} (${b.label})`}</title>
              </rect>
            );
          });
        }

        // Total bar
        const barH = (b.total / maxVal) * h;
        return (
          <rect
            key={i}
            x={x}
            y={pad.top + h - barH}
            width={barW}
            height={barH}
            fill="#6366f1"
            rx="2"
            className="transition-opacity hover:opacity-80"
          >
            <title>{`${b.total} events (${b.label})`}</title>
          </rect>
        );
      })}

      {/* X-axis labels */}
      {buckets.filter((_, i) => i % Math.max(1, Math.floor(buckets.length / 8)) === 0).map((b, i) => {
        const idx = buckets.indexOf(b);
        const x = pad.left + (idx / buckets.length) * w + barW / 2;
        return (
          <text key={i} x={x} y={svgH - 10} textAnchor="end" transform={`rotate(-30, ${x}, ${svgH - 10})`} className="fill-gray-400 dark:fill-gray-500 text-[10px]">
            {b.label}
          </text>
        );
      })}
    </svg>
  );
}

function StatusDistribution({ events }) {
  const counts = {};
  events.forEach(e => {
    const s = e.status || 'unknown';
    counts[s] = (counts[s] || 0) + 1;
  });

  const total = events.length;
  if (total === 0) return null;

  const order = ['healthy', 'degraded', 'failed', 'pending', 'unknown'];

  return (
    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
      <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">Status Distribution</h4>
      <div className="space-y-2">
        {order.map(s => {
          const c = STATUS_COLORS[s];
          const count = counts[s] || 0;
          const pct = total > 0 ? (count / total) * 100 : 0;
          if (count === 0) return null;
          return (
            <div key={s} className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: c?.fill || '#9ca3af' }} />
              <span className={`text-xs capitalize w-16 ${c ? 'text-gray-600 dark:text-gray-300' : 'text-gray-400'}`}>
                {c?.label || s}
              </span>
              <div className="flex-1 h-2.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: c?.fill || '#9ca3af' }} />
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400 w-10 text-right font-medium">{count}</span>
              <span className="text-xs text-gray-400 dark:text-gray-500 w-10 text-right">{pct.toFixed(0)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TypeDistribution({ events }) {
  const counts = {};
  events.forEach(e => {
    counts[e.event_type] = (counts[e.event_type] || 0) + 1;
  });

  const total = events.length;

  return (
    <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
      <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">By Resource Type</h4>
      <div className="space-y-2">
        {Object.entries(counts).map(([type, count]) => {
          const c = TYPE_COLORS[type];
          const pct = (count / total) * 100;
          return (
            <div key={type} className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: c?.fill || '#9ca3af' }} />
              <span className="text-xs capitalize w-16 text-gray-600 dark:text-gray-300">{c?.label || type}</span>
              <div className="flex-1 h-2.5 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: c?.fill || '#9ca3af' }} />
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-400 w-10 text-right font-medium">{count}</span>
              <span className="text-xs text-gray-400 dark:text-gray-500 w-10 text-right">{pct.toFixed(0)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function EventChart({ events }) {
  const [mounted, setMounted] = useState(false);
  const [hoursBack, setHoursBack] = useState(24);
  const [chartType, setChartType] = useState('status');

  useEffect(() => setMounted(true), []);

  const buckets = useMemo(() => groupByHour(events, hoursBack), [events, hoursBack]);

  if (!mounted) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-800 dark:text-white">Event Analytics</h3>
        </div>
        <div className="h-[200px] flex items-center justify-center text-sm text-gray-400 dark:text-gray-500">
          Loading chart...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-white">Event Analytics</h3>
        <div className="flex gap-2">
          {[24, 48, 72].map(h => (
            <button
              key={h}
              onClick={() => setHoursBack(h)}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                hoursBack === h
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {h}h
            </button>
          ))}
        </div>
      </div>

      {buckets.length > 0 && (
        <>
          <div className="flex gap-2 mb-3">
            <button
              onClick={() => setChartType('status')}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                chartType === 'status'
                  ? 'bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-800'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              By Status
            </button>
            <button
              onClick={() => setChartType('type')}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                chartType === 'type'
                  ? 'bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-800'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              By Type
            </button>
            <button
              onClick={() => setChartType('total')}
              className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                chartType === 'total'
                  ? 'bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-800'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Total
            </button>
          </div>

          {chartType === 'status' && (
            <div className="flex gap-3 mb-2 flex-wrap">
              {Object.entries(STATUS_COLORS).map(([k, v]) => (
                <span key={k} className="flex items-center gap-1 text-[10px] text-gray-500 dark:text-gray-400">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: v.fill }} />
                  {v.label}
                </span>
              ))}
            </div>
          )}

          {chartType === 'type' && (
            <div className="flex gap-3 mb-2 flex-wrap">
              {Object.entries(TYPE_COLORS).map(([k, v]) => (
                <span key={k} className="flex items-center gap-1 text-[10px] text-gray-500 dark:text-gray-400">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: v.fill }} />
                  {v.label}
                </span>
              ))}
            </div>
          )}

          <TimeSeriesChart buckets={buckets} chartType={chartType} />
        </>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4">
        <StatusDistribution events={events} />
        <TypeDistribution events={events} />
      </div>
    </div>
  );
}
