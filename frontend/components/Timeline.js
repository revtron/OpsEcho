import { useState } from 'react';

const TYPE_STYLES = {
  kubernetes: { bg: 'bg-blue-100 dark:bg-blue-900/40', text: 'text-blue-800 dark:text-blue-300', dot: 'bg-blue-500', icon: '⎈' },
  terraform:  { bg: 'bg-purple-100 dark:bg-purple-900/40', text: 'text-purple-800 dark:text-purple-300', dot: 'bg-purple-500', icon: '⛁' },
  git:        { bg: 'bg-green-100 dark:bg-green-900/40', text: 'text-green-800 dark:text-green-300', dot: 'bg-green-500', icon: '⎇' },
  ec2:        { bg: 'bg-orange-100 dark:bg-orange-900/40', text: 'text-orange-800 dark:text-orange-300', dot: 'bg-orange-500', icon: '☁' },
};

const PHASE_STYLES = {
  Running:    { dot: 'bg-green-500',  badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800', icon: '✓' },
  Succeeded:  { dot: 'bg-green-500',  badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800', icon: '✓' },
  Failed:     { dot: 'bg-red-500',    badge: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800', icon: '✕' },
  Error:      { dot: 'bg-red-500',    badge: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800', icon: '✕' },
  Pending:    { dot: 'bg-yellow-500', badge: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800', icon: '○' },
  Unknown:    { dot: 'bg-gray-400',   badge: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600', icon: '?' },
  NotReady:   { dot: 'bg-red-500',    badge: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800', icon: '✕' },
  Ready:      { dot: 'bg-green-500',  badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800', icon: '✓' },
  CrashLoopBackOff: { dot: 'bg-red-500', badge: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800', icon: '⟳' },
};

const STATUS_STYLES = {
  healthy:  { dot: 'bg-green-500',  badge: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 border-green-200 dark:border-green-800', icon: '✓' },
  degraded: { dot: 'bg-yellow-500', badge: 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800', icon: '⚡' },
  failed:   { dot: 'bg-red-500',    badge: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300 border-red-200 dark:border-red-800', icon: '✕' },
  pending:  { dot: 'bg-blue-400',   badge: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800', icon: '○' },
  unknown:  { dot: 'bg-gray-400',   badge: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-600', icon: '?' },
};

function PhaseBadge({ phase, failure_reason }) {
  const displayPhase = failure_reason && PHASE_STYLES[failure_reason]
    ? failure_reason
    : phase;
  const s = PHASE_STYLES[displayPhase] || PHASE_STYLES.Unknown;

  if (!phase) return null;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${s.badge}`}>
      <span>{s.icon}</span>
      <span>{displayPhase}</span>
    </span>
  );
}

function ResourceInfo({ resource }) {
  if (!resource || !resource.kind) return null;

  return (
    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mt-1">
      <span className="font-mono bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded dark:text-gray-300">{resource.kind}</span>
      <span className="font-medium text-gray-700 dark:text-gray-200 truncate max-w-[200px]">{resource.name}</span>
      {resource.namespace && (
        <span className="text-gray-400 dark:text-gray-500">ns: {resource.namespace}</span>
      )}
      {resource.restart_count > 0 && (
        <span className="text-orange-600 dark:text-orange-400 font-medium">restarts: {resource.restart_count}</span>
      )}
      {resource.kind === 'Deployment' && resource.replicas != null && (
        <span className="text-gray-400 dark:text-gray-500">
          {resource.available_replicas || 0}/{resource.replicas} ready
        </span>
      )}
    </div>
  );
}

function StatusBadge({ status, severity, failure_reason }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.unknown;
  const severityColor =
    severity === 'critical' ? 'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300 border-red-200 dark:border-red-800' :
    severity === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/30 text-yellow-600 dark:text-yellow-300 border-yellow-200 dark:border-yellow-800' :
    'bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-300 border-green-200 dark:border-green-800';

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${s.badge}`}>
        <span>{s.icon}</span>
        <span className="capitalize">{status}</span>
      </span>
      {severity && severity !== 'info' && (
        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${severityColor}`}>
          {severity === 'critical' ? '🔴' : '🟡'} {severity}
        </span>
      )}
      {failure_reason && !PHASE_STYLES[failure_reason] && (
        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 max-w-[200px] truncate" title={failure_reason}>
          {failure_reason}
        </span>
      )}
    </div>
  );
}

function EventCard({ event }) {
  const [expanded, setExpanded] = useState(false);
  const typeStyle = TYPE_STYLES[event.event_type] || TYPE_STYLES.kubernetes;
  const statusStyle = STATUS_STYLES[event.status] || STATUS_STYLES.unknown;

  const summary = event.summary || '';
  const summarySnippet = summary.split('\n\n')[0] || '';

  const phase = event.resource?.phase;
  const failure_reason = event.failure_reason;
  const isIssue = event.status === 'failed' || event.status === 'degraded' || event.severity === 'critical';

  return (
    <div className={`border rounded-lg hover:shadow-md dark:hover:shadow-gray-900/50 transition-shadow ${
      isIssue ? 'border-red-200 dark:border-red-800 bg-red-50/30 dark:bg-red-900/10' : 'border-gray-200 dark:border-gray-700'
    }`}>
      <div
        className="p-4 cursor-pointer flex items-start gap-3"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={`w-3 h-3 rounded-full mt-1.5 flex-shrink-0 ${statusStyle.dot}`} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${typeStyle.bg} ${typeStyle.text}`}>
              <span>{typeStyle.icon}</span>
              <span>{event.event_type}</span>
            </span>
            <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{event.source}</span>
            {phase && <PhaseBadge phase={phase} failure_reason={failure_reason} />}
            <span className="text-xs text-gray-400 dark:text-gray-500 ml-auto">
              {(() => { const d = new Date(event.timestamp); return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`; })()}
            </span>
          </div>

          <ResourceInfo resource={event.resource} />

          <p className={`text-sm leading-relaxed mt-1 ${isIssue ? 'text-red-700 dark:text-red-300 font-medium' : 'text-gray-600 dark:text-gray-300'}`}>
            {summarySnippet || (isIssue ? `${event.status} — ${event.failure_reason || 'Unknown issue'}` : 'No summary available')}
          </p>
          <div className="flex items-center gap-2 mt-2">
            <StatusBadge
              status={event.status}
              severity={event.severity}
              failure_reason={event.failure_reason}
            />
            {event.is_processed ? (
              <span className="inline-flex items-center gap-1 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 text-xs px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full" />
                Processed
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300 text-xs px-2 py-0.5 rounded-full">
                <span className="w-1.5 h-1.5 bg-yellow-500 rounded-full animate-pulse" />
                Pending
              </span>
            )}
            {summary && (
              <span className="text-xs text-gray-400 dark:text-gray-500">
                {expanded ? '▲ Less' : '▼ More'}
              </span>
            )}
          </div>
        </div>
      </div>
      {expanded && summary && (
        <div className="px-4 pb-4 pl-10 border-t border-gray-100 dark:border-gray-700">
          <div className="mt-3 space-y-3">
            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
              <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">AI Summary</h4>
              <p className="text-sm text-gray-700 dark:text-gray-200 whitespace-pre-line">{summary}</p>
            </div>
            {event.operational_context && (
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3">
                <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1">Operational Context</h4>
                <div className="text-xs text-gray-600 dark:text-gray-300 space-y-1">
                  {event.operational_context.ownership?.ownership && (
                    <p>Owned by: <span className="font-medium">{event.operational_context.ownership.ownership}</span></p>
                  )}
                  {event.operational_context.previous_failures?.length > 0 && (
                    <p className="text-red-600 dark:text-red-400">
                      Previous failures: <span className="font-medium">{event.operational_context.previous_failures.length}</span>
                    </p>
                  )}
                  {event.operational_context.historical_patterns?.total_similar_events !== undefined && (
                    <p>
                      Similar events (90d): <span className="font-medium">{event.operational_context.historical_patterns.total_similar_events}</span>
                      {event.operational_context.historical_patterns.average_interval_hours && (
                        <span> (avg every {event.operational_context.historical_patterns.average_interval_hours.toFixed(1)}h)</span>
                      )}
                    </p>
                  )}
                  {event.operational_context.deployment_history?.length > 0 && (
                    <p>Related deployments: <span className="font-medium">{event.operational_context.deployment_history.length}</span></p>
                  )}
                  {event.operational_context.correlations?.length > 0 && (
                    <p>Correlated events: <span className="font-medium">{event.operational_context.correlations.length}</span></p>
                  )}
                  {event.operational_context.dependencies?.length > 0 && (
                    <div>
                      <p>Service dependencies:</p>
                      <ul className="list-disc list-inside ml-2">
                        {event.operational_context.dependencies.map((dep, i) => (
                          <li key={i}>{dep.name} ({dep.ownership || 'unowned'})</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function Timeline({ events, searchQuery, loading }) {
  const [filter, setFilter] = useState('all');

  const typeCounts = {};
  const statusCounts = {};
  const phaseCounts = {};
  let total = 0;
  let issueCount = 0;
  events.forEach(e => {
    if (e.event_type) {
      typeCounts[e.event_type] = (typeCounts[e.event_type] || 0) + 1;
      total++;
    }
    if (e.status) {
      statusCounts[e.status] = (statusCounts[e.status] || 0) + 1;
    }
    if (e.resource?.phase) {
      const p = e.failure_reason && PHASE_STYLES[e.failure_reason] ? e.failure_reason : e.resource.phase;
      phaseCounts[p] = (phaseCounts[p] || 0) + 1;
    }
    if (e.status === 'failed' || e.status === 'degraded' || e.severity === 'critical') {
      issueCount++;
    }
  });

  const filteredEvents = events.filter(event => {
    if (searchQuery) {
      const searchable = `${event.event_type} ${event.source} ${event.summary || ''} ${event.failure_reason || ''} ${event.status || ''} ${event.resource?.name || ''} ${event.resource?.phase || ''}`.toLowerCase();
      if (!searchable.includes(searchQuery.toLowerCase())) return false;
    }
    if (filter === 'all') return true;
    if (filter === 'issues') return event.status === 'failed' || event.status === 'degraded' || event.severity === 'critical';
    return event.event_type === filter;
  });

  return (
    <div>
      {issueCount > 0 && (
        <div className="mb-4 px-4 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-700 dark:text-red-300 flex items-center gap-2">
          <span className="font-bold">{issueCount}</span> issue{issueCount > 1 ? 's' : ''} detected
          {issueCount > 0 && (
            <span className="text-xs text-red-500 dark:text-red-400">
              ({statusCounts['failed'] || 0} failed, {statusCounts['degraded'] || 0} degraded)
            </span>
          )}
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <div className="flex flex-wrap gap-2">
          {['all', 'issues', 'kubernetes', 'terraform', 'git', 'ec2'].map(type => (
            <button
              key={type}
              onClick={() => setFilter(type)}
              className={`text-sm px-3 py-1.5 rounded-lg transition-colors capitalize ${
                filter === type
                  ? 'bg-blue-600 text-white shadow-sm'
                  : type === 'issues'
                    ? 'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/50'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {type === 'issues' ? (
                <span className="flex items-center gap-1">
                  ⚠ Issues
                  {issueCount > 0 && <span className="ml-1 text-xs bg-red-500 text-white px-1.5 py-0.5 rounded-full">{issueCount}</span>}
                </span>
              ) : (
                <>
                  {type}
                  {type !== 'all' && typeCounts[type] !== undefined && (
                    <span className={`ml-1.5 text-xs ${filter === type ? 'text-blue-200' : 'text-gray-400 dark:text-gray-500'}`}>
                      ({typeCounts[type]})
                    </span>
                  )}
                </>
              )}
            </button>
          ))}
        </div>
        <span className="text-xs text-gray-400 dark:text-gray-500">{filteredEvents.length} of {total} events</span>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">Loading events...</p>
        </div>
      )}

      {!loading && filteredEvents.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-400 dark:text-gray-500 text-lg mb-1">No events found</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm">
            {events.length === 0
              ? 'Click "Generate Demo Events" to populate the timeline.'
              : 'Try adjusting your search or filter.'}
          </p>
        </div>
      )}

      {!loading && filteredEvents.length > 0 && (
        <div className="space-y-3">
          {filteredEvents.map(event => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      )}
    </div>
  );
}
