import { useState } from 'react';

const INSTANCE_STATE_STYLES = {
  running:    { dot: 'bg-green-500',  bg: 'bg-green-100 dark:bg-green-900/30', text: 'text-green-700 dark:text-green-300' },
  stopped:    { dot: 'bg-red-500',    bg: 'bg-red-100 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300' },
  stopping:   { dot: 'bg-yellow-500', bg: 'bg-yellow-100 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300' },
  pending:    { dot: 'bg-blue-400',   bg: 'bg-blue-100 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300' },
  terminated: { dot: 'bg-gray-400',   bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-600 dark:text-gray-300' },
  unknown:    { dot: 'bg-gray-400',   bg: 'bg-gray-100 dark:bg-gray-700', text: 'text-gray-600 dark:text-gray-300' },
};

const STATUS_CHECK_STYLES = {
  ok:                 { dot: 'bg-green-500',  label: 'OK',      bg: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
  degraded:           { dot: 'bg-yellow-500', label: 'Degraded', bg: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
  impaired:           { dot: 'bg-red-500',    label: 'Impaired', bg: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
  'insufficient-data': { dot: 'bg-blue-400',  label: 'No Data',  bg: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  unknown:            { dot: 'bg-gray-400',   label: 'Unknown',  bg: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300' },
};

function InstanceRow({ instance }) {
  const [expanded, setExpanded] = useState(false);
  const stateStyle = INSTANCE_STATE_STYLES[instance.state] || INSTANCE_STATE_STYLES.unknown;
  const checkStyle = STATUS_CHECK_STYLES[instance.status_check] || STATUS_CHECK_STYLES.unknown;
  const isIssue = instance.state === 'stopped' || instance.status_check === 'impaired' || instance.status_check === 'degraded';

  return (
    <div
      className={`border rounded-lg transition-shadow ${
        isIssue ? 'border-red-200 dark:border-red-800 bg-red-50/30 dark:bg-red-900/10' : 'border-gray-200 dark:border-gray-700'
      }`}
    >
      <div className="p-3 cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-3">
          <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${stateStyle.dot}`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{instance.name}</span>
              <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">{instance.instance_id}</span>
              <span className="text-xs text-gray-400">{instance.instance_type}</span>
            </div>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${stateStyle.bg} ${stateStyle.text}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${stateStyle.dot}`} />
                {instance.state}
              </span>
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${checkStyle.bg}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${checkStyle.dot}`} />
                {checkStyle.label}
              </span>
              {instance.public_ip && (
                <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">{instance.public_ip}</span>
              )}
              {instance.private_ip && (
                <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">{instance.private_ip}</span>
              )}
              {instance.events?.length > 0 && (
                <span className="text-xs text-red-600 dark:text-red-400 font-medium">
                  ⚠ {instance.events.length} event{instance.events.length > 1 ? 's' : ''}
                </span>
              )}
            </div>
          </div>
          <span className="text-xs text-gray-400">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>
      {expanded && (
        <div className="px-3 pb-3 pl-8 border-t border-gray-100 dark:border-gray-700">
          <div className="mt-2 text-xs text-gray-600 dark:text-gray-300 space-y-1">
            <p>Instance ID: <span className="font-mono font-medium">{instance.instance_id}</span></p>
            <p>Instance type: <span className="font-medium">{instance.instance_type}</span></p>
            <p>Region: <span className="font-medium">{instance.region}</span></p>
            {instance.vpc_id && <p>VPC: <span className="font-mono">{instance.vpc_id}</span></p>}
            {instance.subnet_id && <p>Subnet: <span className="font-mono">{instance.subnet_id}</span></p>}
            {instance.public_ip && <p>Public IP: <span className="font-mono">{instance.public_ip}</span></p>}
            {instance.private_ip && <p>Private IP: <span className="font-mono">{instance.private_ip}</span></p>}
            <p>System status: <span className={`font-medium ${instance.system_status_check === 'ok' ? 'text-green-600' : 'text-red-600'}`}>{instance.system_status_check}</span></p>
            <p>Instance status: <span className={`font-medium ${instance.status_check === 'ok' ? 'text-green-600' : 'text-red-600'}`}>{instance.status_check}</span></p>
            {instance.events?.length > 0 && (
              <div className="mt-2">
                <p className="font-semibold text-red-600 dark:text-red-400">Scheduled events:</p>
                <ul className="list-disc list-inside ml-2">
                  {instance.events.map((evt, i) => (
                    <li key={i}>{evt.description || evt.code}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function HealthSummary({ instances }) {
  const total = instances.length;
  const running = instances.filter(i => i.state === 'running').length;
  const stopped = instances.filter(i => i.state === 'stopped' || i.state === 'stopping').length;
  const pending = instances.filter(i => i.state === 'pending').length;
  const impaired = instances.filter(i => i.status_check === 'impaired' || i.system_status_check === 'impaired').length;
  const degraded = instances.filter(i => (i.status_check === 'degraded' || i.system_status_check === 'degraded') && i.status_check !== 'impaired').length;
  const ok = instances.filter(i => i.status_check === 'ok' || i.system_status_check === 'ok').length;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-4">
      <div className="bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg p-3 border border-transparent">
        <div className="text-xs uppercase tracking-wider font-medium">Running</div>
        <div className="text-lg font-bold">{running}</div>
      </div>
      <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg p-3 border border-transparent">
        <div className="text-xs uppercase tracking-wider font-medium">Impaired</div>
        <div className="text-lg font-bold">{impaired}</div>
      </div>
      <div className="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded-lg p-3 border border-transparent">
        <div className="text-xs uppercase tracking-wider font-medium">Degraded</div>
        <div className="text-lg font-bold">{degraded}</div>
      </div>
      <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg p-3 border border-transparent">
        <div className="text-xs uppercase tracking-wider font-medium">Stopped</div>
        <div className="text-lg font-bold">{stopped}</div>
      </div>
      <div className="bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg p-3 border border-transparent">
        <div className="text-xs uppercase tracking-wider font-medium">Pending</div>
        <div className="text-lg font-bold">{pending}</div>
      </div>
    </div>
  );
}

export default function Ec2Health({ events }) {
  const ec2Events = events.filter(e => e.event_type === 'ec2');
  if (ec2Events.length === 0) return null;

  const instances = ec2Events.map(e => ({
    instance_id: e.resource?.instance_id || e.source,
    name: e.resource?.name || e.source,
    instance_type: e.resource?.instance_type || '?',
    state: e.resource?.state || 'unknown',
    status_check: e.resource?.status_check || 'unknown',
    system_status_check: e.resource?.system_status_check || 'unknown',
    region: e.resource?.region || '?',
    private_ip: e.resource?.private_ip || '',
    public_ip: e.resource?.public_ip || '',
    vpc_id: e.resource?.vpc_id || '',
    subnet_id: e.resource?.subnet_id || '',
    events: e.resource?.events || [],
  }));

  const issueCount = instances.filter(
    i => i.state === 'stopped' || i.status_check === 'impaired' || i.status_check === 'degraded'
  ).length;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-800 dark:text-white">EC2 Instance Health</h3>
        <span className="text-xs text-gray-400 dark:text-gray-500">{instances.length} instances</span>
      </div>

      <HealthSummary instances={instances} />

      {issueCount > 0 && (
        <div className="mb-3 px-3 py-2 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-700 dark:text-red-300">
          <span className="font-bold">{issueCount}</span> instance{issueCount > 1 ? 's' : ''} with issues — investigate immediately
        </div>
      )}

      <div className="space-y-2">
        {instances.map(inst => (
          <InstanceRow key={inst.instance_id} instance={inst} />
        ))}
      </div>
    </div>
  );
}
