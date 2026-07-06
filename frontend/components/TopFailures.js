const EVENT_ICONS = {
  kubernetes: { bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-600 dark:text-blue-400', label: 'K8s' },
  terraform: { bg: 'bg-purple-100 dark:bg-purple-900/30', text: 'text-purple-600 dark:text-purple-400', label: 'TF' },
  ec2: { bg: 'bg-amber-100 dark:bg-amber-900/30', text: 'text-amber-600 dark:text-amber-400', label: 'EC2' },
  aws: { bg: 'bg-pink-100 dark:bg-pink-900/30', text: 'text-pink-600 dark:text-pink-400', label: 'AWS' },
  docker: { bg: 'bg-cyan-100 dark:bg-cyan-900/30', text: 'text-cyan-600 dark:text-cyan-400', label: 'Dkr' },
  git: { bg: 'bg-emerald-100 dark:bg-emerald-900/30', text: 'text-emerald-600 dark:text-emerald-400', label: 'Git' },
  default: { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-600 dark:text-gray-400', label: '?' },
};

export default function TopFailures({ events }) {
  const failed = events.filter(e => e.status === 'failed' || e.severity === 'critical');
  if (failed.length === 0) return null;

  const byResource = {};
  failed.forEach(e => {
    const name = e.resource?.name || e.source || 'unknown';
    const reason = e.failure_reason || e.severity || 'error';
    if (!byResource[name]) byResource[name] = { count: 0, reasons: {}, eventType: e.event_type, source: e.source };
    byResource[name].count++;
    byResource[name].reasons[reason] = (byResource[name].reasons[reason] || 0) + 1;
  });

  const sorted = Object.entries(byResource)
    .sort((a, b) => b[1].count - a[1].count)
    .slice(0, 8);

  const maxCount = sorted[0]?.[1].count || 1;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 h-full">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-white">Top Failures</h3>
        <span className="text-xs text-red-500 font-medium">{failed.length} total</span>
      </div>

      <div className="space-y-1.5">
        {sorted.map(([name, info]) => {
          const icon = EVENT_ICONS[info.eventType] || EVENT_ICONS.default;
          const pct = (info.count / maxCount) * 100;
          const topReason = Object.entries(info.reasons).sort((a, b) => b[1] - a[1])[0];
          return (
            <div key={name} className="group">
              <div className="flex items-center gap-2 mb-0.5">
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${icon.bg} ${icon.text}`}>{icon.label}</span>
                <span className="text-xs text-gray-700 dark:text-gray-300 truncate flex-1">{name}</span>
                <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">{info.count}</span>
              </div>
              <div className="h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-red-500 to-red-400 dark:from-red-600 dark:to-red-500 transition-all"
                  style={{ width: `${pct}%` }}
                />
              </div>
              {topReason && (
                <div className="text-[10px] text-gray-400 dark:text-gray-500 truncate mt-0.5">{topReason[0]} ({topReason[1]})</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
