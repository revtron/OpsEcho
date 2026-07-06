const PHASE_STYLES = {
  Running:    { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', dot: 'bg-green-500', label: 'Running' },
  Succeeded:  { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', dot: 'bg-green-500', label: 'Succeeded' },
  Failed:     { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500', label: 'Failed' },
  Pending:    { bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300', dot: 'bg-yellow-500', label: 'Pending' },
  Unknown:    { bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-600 dark:text-gray-300', dot: 'bg-gray-400', label: 'Unknown' },
  NotReady:   { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500', label: 'NotReady' },
  Ready:      { bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300', dot: 'bg-green-500', label: 'Ready' },
  CrashLoopBackOff: { bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300', dot: 'bg-red-500', label: 'CrashLoopBackOff' },
};

function getPhaseMetrics(events) {
  const k8sEvents = events.filter(e => e.event_type === 'kubernetes');
  const counts = {};
  let totalIssues = 0;

  k8sEvents.forEach(e => {
    const rawPhase = e.resource?.phase;
    const reason = e.failure_reason;
    const phase = reason && PHASE_STYLES[reason] ? reason : (rawPhase || 'Unknown');
    counts[phase] = (counts[phase] || 0) + 1;
    if (e.status === 'failed' || e.status === 'degraded' || e.severity === 'critical') {
      totalIssues++;
    }
  });

  return { counts, total: k8sEvents.length, totalIssues };
}

function MetricCard({ label, count, total, color }) {
  const pct = total > 0 ? ((count / total) * 100).toFixed(0) : 0;
  return (
    <div className={`rounded-lg p-3 border ${color.bg} ${color.text} border-transparent`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider truncate">{label}</span>
        <span className="text-lg font-bold ml-2">{count}</span>
      </div>
      {total > 0 && (
        <div className="mt-2 w-full bg-white/50 dark:bg-black/20 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full ${color.dot} transition-all`}
            style={{ width: `${pct}%` }}
          />
        </div>
      )}
      <span className="text-xs opacity-75">{pct}% of pods</span>
    </div>
  );
}

function IssueList({ events }) {
  const issues = events.filter(
    e => e.event_type === 'kubernetes' && (e.status === 'failed' || e.status === 'degraded' || e.severity === 'critical')
  ).slice(0, 5);

  if (issues.length === 0) return null;

  return (
    <div className="mt-3">
      <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">Current Issues</h4>
      <div className="space-y-1.5">
        {issues.map(pod => {
          const phase = pod.resource?.phase || 'Unknown';
          const reason = pod.failure_reason;
          const isCritical = pod.severity === 'critical' || pod.status === 'failed';
          return (
            <div
              key={pod.id}
              className={`flex items-center gap-2 px-2.5 py-1.5 rounded text-xs ${
                isCritical
                  ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                  : 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-300'
              }`}
            >
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isCritical ? 'bg-red-500' : 'bg-yellow-500'}`} />
              <span className="font-mono font-medium truncate">{pod.resource?.kind || 'Pod'}</span>
              <span className="truncate max-w-[120px]">{pod.resource?.name || pod.source}</span>
              <span className={`ml-auto font-mono px-1 py-0.5 rounded ${
                isCritical ? 'bg-red-200 dark:bg-red-800' : 'bg-yellow-200 dark:bg-yellow-800'
              }`}>{phase}</span>
              {reason && <span className="truncate max-w-[120px] opacity-75">{reason}</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function PodMetrics({ events }) {
  const { counts, total, totalIssues } = getPhaseMetrics(events);

  if (total === 0) return null;

  const displayPhases = ['Running', 'CrashLoopBackOff', 'Failed', 'Pending', 'NotReady', 'Unknown'];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-white">Pod Status</h3>
        <span className="text-xs text-gray-400 dark:text-gray-500">{total} resources</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {displayPhases.map(phase => {
          const count = counts[phase] || 0;
          const style = PHASE_STYLES[phase] || PHASE_STYLES.Unknown;
          return (
            <MetricCard
              key={phase}
              label={style.label}
              count={count}
              total={total}
              color={style}
            />
          );
        })}
      </div>

      {totalIssues > 0 && (
        <div className="mt-3 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-300">
          <span className="font-bold">{totalIssues}</span> pod{totalIssues > 1 ? 's' : ''} with issues
          {counts['CrashLoopBackOff'] > 0 && (
            <span> — <span className="font-medium">{counts['CrashLoopBackOff']}</span> in CrashLoopBackOff</span>
          )}
          {counts['Failed'] > 0 && (
            <span> — <span className="font-medium">{counts['Failed']}</span> failed</span>
          )}
          {counts['NotReady'] > 0 && (
            <span> — <span className="font-medium">{counts['NotReady']}</span> not ready</span>
          )}
          {counts['Pending'] > 0 && (
            <span> — <span className="font-medium">{counts['Pending']}</span> pending</span>
          )}
        </div>
      )}

      <IssueList events={events} />
    </div>
  );
}
