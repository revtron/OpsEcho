const TYPE_LABELS = {
  kubernetes: 'Kubernetes', terraform: 'Terraform', ec2: 'EC2',
  aws: 'AWS CloudTrail', docker: 'Docker', git: 'Git', default: 'Other'
};

function getHealth(events) {
  const sources = {};
  let totalHealthy = 0, totalDegraded = 0, totalFailed = 0;

  events.forEach(e => {
    const key = TYPE_LABELS[e.event_type] || TYPE_LABELS.default;
    if (!sources[key]) sources[key] = { healthy: 0, degraded: 0, failed: 0 };
    if (e.status === 'healthy') { sources[key].healthy++; totalHealthy++; }
    else if (e.status === 'degraded') { sources[key].degraded++; totalDegraded++; }
    else { sources[key].failed++; totalFailed++; }
  });

  return { sources, totalHealthy, totalDegraded, totalFailed, total: events.length };
}

function Bar({ pct, color }) {
  return (
    <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
      <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${Math.max(pct, 2)}%` }} />
    </div>
  );
}

export default function HealthOverview({ events }) {
  const { sources, totalHealthy, totalDegraded, totalFailed, total } = getHealth(events);
  if (total === 0) return null;

  const entries = Object.entries(sources);
  const healthyPct = total ? (totalHealthy / total) * 100 : 0;
  const degradedPct = total ? (totalDegraded / total) * 100 : 0;
  const failedPct = total ? (totalFailed / total) * 100 : 0;
  const okPct = healthyPct + degradedPct;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 h-full">
      <h3 className="text-sm font-semibold text-gray-800 dark:text-white mb-3">Health Overview</h3>

      {/* Stacked bar */}
      <div className="h-3 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden mb-3 flex">
        <div className="h-full bg-green-500 transition-all" style={{ width: `${healthyPct}%` }} />
        <div className="h-full bg-yellow-500 transition-all" style={{ width: `${degradedPct}%` }} />
        <div className="h-full bg-red-500 transition-all" style={{ width: `${failedPct}%` }} />
      </div>

      <div className="flex items-center justify-between text-xs mb-4">
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />{' '}{totalHealthy} healthy</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" />{' '}{totalDegraded} degraded</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />{' '}{totalFailed} failed</span>
        <span className="text-gray-400">{total} total</span>
      </div>

      <div className="space-y-2">
        {entries.map(([name, s]) => {
          const h = s.healthy + s.degraded + s.failed;
          const pct = total ? (h / total) * 100 : 0;
          return (
            <div key={name}>
              <div className="flex justify-between text-xs mb-0.5">
                <span className="text-gray-600 dark:text-gray-400">{name}</span>
                <span className="text-gray-500 dark:text-gray-500 font-medium">{h}</span>
              </div>
              <div className="flex h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden gap-px">
                <div className="bg-green-500" style={{ width: `${s.healthy / h * 100}%` }} />
                {s.degraded > 0 && <div className="bg-yellow-500" style={{ width: `${s.degraded / h * 100}%` }} />}
                {s.failed > 0 && <div className="bg-red-500" style={{ width: `${s.failed / h * 100}%` }} />}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
