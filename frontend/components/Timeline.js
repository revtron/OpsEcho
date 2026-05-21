import { useState } from 'react';

export default function Timeline({ events, searchQuery }) {
  const [filter, setFilter] = useState('all');

  const filteredEvents = events.filter(event => {
    // Filter by search query (simple implementation)
    if (searchQuery) {
      const searchableText = `${event.event_type} ${event.source}`.toLowerCase();
      return searchableText.includes(searchQuery.toLowerCase());
    }
    return true;
  }).filter(event => {
    // Filter by type
    if (filter === 'all') return true;
    return event.event_type === filter;
  });

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-4">
        <button 
          onClick={() => setFilter('all')}
          className={filter === 'all' ? 'bg-blue-500 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'}
        >
          All
        </button>
        <button 
          onClick={() => setFilter('kubernetes')}
          className={filter === 'kubernetes' ? 'bg-blue-500 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'}
        >
          K8s
        </button>
        <button 
          onClick={() => setFilter('terraform')}
          className={filter === 'terraform' ? 'bg-blue-500 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'}
        >
          Terraform
        </button>
        <button 
          onClick={() => setFilter('git')}
          className={filter === 'git' ? 'bg-blue-500 text-white px-3 py-1 rounded' : 'bg-gray-200 px-3 py-1 rounded'}
        >
          Git
        </button>
      </div>

      <div className="space-y-4">
        {filteredEvents.length > 0 ? (
          filteredEvents.map(event => (
            <div key={event.id} className="border-l-2 border-blue-500 pl-4 mb-4">
              <div className="flex justify-between items-start mb-1">
                <span className="font-medium text-gray-800">{event.event_type}</span>
                <span className="text-xs text-gray-500">{new Date(event.timestamp).toLocaleString()}</span>
              </div>
              <p className="text-gray-600">{event.source}</p>
              {event.is_processed ? (
                <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">Processed</span>
              ) : (
                <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">Pending</span>
              )}
            </div>
          ))
        ) : (
          <p className="text-gray-500">No events found.</p>
        )}
      </div>
    </div>
  );
}