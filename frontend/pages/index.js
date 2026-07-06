import Head from 'next/head'
import { useState, useEffect, useCallback } from 'react'
import Timeline from '../components/Timeline'
import SearchBar from '../components/SearchBar'
import PodMetrics from '../components/PodMetrics'
import Ec2Health from '../components/Ec2Health'
import EventChart from '../components/EventChart'
import HealthOverview from '../components/HealthOverview'
import EventDistribution from '../components/EventDistribution'
import TopFailures from '../components/TopFailures'
import { useTheme } from '../components/ThemeProvider'

function getSummaryStats(events) {
  const stats = { total: events.length, healthy: 0, degraded: 0, failed: 0, pending: 0 };
  events.forEach(e => {
    if (e.status === 'healthy') stats.healthy++;
    else if (e.status === 'degraded') stats.degraded++;
    else if (e.status === 'failed') stats.failed++;
    else if (e.status === 'pending') stats.pending++;
  });
  return stats;
}

export default function Home() {
  const { dark, toggle } = useTheme()
  const [events, setEvents] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState(null)
  const [searching, setSearching] = useState(false)
  const [loading, setLoading] = useState(false)
  const [seeding, setSeeding] = useState(false)
  const [error, setError] = useState(null)
  const [statusMessage, setStatusMessage] = useState(null)
  const [aiAvailable, setAiAvailable] = useState(false)
  const [aiQuestion, setAiQuestion] = useState('')
  const [aiAnswer, setAiAnswer] = useState(null)
  const [aiAsking, setAiAsking] = useState(false)

  useEffect(() => {
    fetch('/api/ai-status').then(r => r.json()).then(d => setAiAvailable(d.ai_available)).catch(() => {})
  }, [])

  const handleAiAsk = async () => {
    if (!aiQuestion.trim()) return
    setAiAsking(true)
    setAiAnswer(null)
    try {
      const res = await fetch(`/api/search/ask?q=${encodeURIComponent(aiQuestion)}`)
      const data = await res.json()
      setAiAnswer(data)
    } catch (err) {
      setAiAnswer({ answer: 'Failed to get answer. Is Ollama running?' })
    }
    setAiAsking(false)
  }

  const fetchTimeline = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch('/api/timeline/?hours=72&limit=50')
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setEvents(data)
    } catch (err) {
      setError('Could not connect to backend. Make sure the server is running.')
      console.error('Error fetching timeline:', err)
    }
    setLoading(false)
  }, [])

  useEffect(() => { fetchTimeline() }, [fetchTimeline])

  const handleSearch = async (query) => {
    setSearchQuery(query)
    setSearching(true)
    setError(null)
    setSearchResults(null)
    try {
      const res = await fetch(`/api/search/?q=${encodeURIComponent(query)}&limit=20`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setSearchResults(data)
      setStatusMessage(`Found ${data.length} result(s) for "${query}"`)
    } catch (err) {
      setError('Search failed. Please try again.')
      console.error('Error searching:', err)
    }
    setSearching(false)
  }

  const handleClearSearch = () => {
    setSearchQuery('')
    setSearchResults(null)
    setStatusMessage(null)
    setError(null)
  }

  const handleSeedDemo = async () => {
    setSeeding(true)
    setError(null)
    setStatusMessage(null)
    try {
      const res = await fetch('/api/events/demo', { method: 'POST' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setStatusMessage(`✅ Generated ${data.events_created} demo events! Processing in background...`)
      setTimeout(() => fetchTimeline(), 2000)
    } catch (err) {
      setError('Failed to generate demo events.')
      console.error('Error seeding demo:', err)
    }
    setSeeding(false)
  }

  const displayEvents = searchResults || events
  const stats = getSummaryStats(events)

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 transition-colors duration-200">
      <Head>
        <title>OpsEcho - Operational Memory Platform</title>
        <meta name="description" content="Infrastructure memory and operational intelligence" />
      </Head>

      <main className="container mx-auto px-4 py-6 max-w-7xl">
        {/* Header */}
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-gray-800 dark:text-white tracking-tight">OpsEcho</h1>
              <div className="hidden sm:flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500" />{stats.healthy} healthy</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500" />{stats.degraded} degraded</span>
                <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" />{stats.failed} failed</span>
                <span className="text-gray-300 dark:text-gray-600">|</span>
                <span>{stats.total} events</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                aiAvailable
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
              }`} title={aiAvailable ? 'AI (Ollama) connected' : 'AI not available'}>
                <span className={`w-1.5 h-1.5 rounded-full ${aiAvailable ? 'bg-green-500' : 'bg-gray-400'}`} />
                AI
              </span>
              <button
                onClick={toggle}
                className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors text-gray-600 dark:text-gray-300"
                title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {dark ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
                )}
              </button>
              <button
                onClick={handleSeedDemo}
                disabled={seeding}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  seeding
                    ? 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                    : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-sm'
                }`}
              >
                {seeding ? (
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Generating...
                  </span>
                ) : (
                  '+ Generate Demo'
                )}
              </button>
            </div>
          </div>
        </header>

        {statusMessage && (
          <div className="mb-4 px-3 py-2 bg-green-50 dark:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-lg text-xs text-green-700 dark:text-green-300">
            {statusMessage}
          </div>
        )}

        {error && (
          <div className="mb-4 px-3 py-2 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg text-xs text-red-600 dark:text-red-300">
            {error}
          </div>
        )}

        {/* Search Bar */}
        <div className="mb-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-3">
          <SearchBar onSearch={handleSearch} onClear={handleClearSearch} searching={searching} />
        </div>

        {searchResults && (
          <div className="mb-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3 flex items-center justify-between">
            <div>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                Search results for "<span className="font-semibold">{searchQuery}</span>"
              </p>
              <p className="text-[10px] text-blue-500 dark:text-blue-400 mt-0.5">
                Semantic search across {events.length} events
              </p>
            </div>
            <button onClick={handleClearSearch} className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 font-medium">Clear</button>
          </div>
        )}

        {/* AI Q&A Panel */}
        <div className="mb-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-3">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ask AI</span>
            <input
              type="text"
              value={aiQuestion}
              onChange={e => setAiQuestion(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAiAsk()}
              placeholder={aiAvailable ? 'Ask about your infrastructure...' : 'Install Ollama to use AI'}
              className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500"
              disabled={!aiAvailable}
            />
            <button
              onClick={handleAiAsk}
              disabled={!aiAvailable || aiAsking}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                aiAvailable
                  ? 'bg-amber-600 text-white hover:bg-amber-700'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
              }`}
            >
              {aiAsking ? (
                <span className="flex items-center gap-1.5">
                  <span className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Thinking...
                </span>
              ) : 'Ask'}
            </button>
          </div>
          {aiAnswer && (
            <div className="mt-3 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
              <p className="text-xs text-gray-600 dark:text-gray-300 whitespace-pre-line">{aiAnswer.answer}</p>
              {aiAnswer.events_used !== undefined && (
                <p className="text-[10px] text-gray-400 dark:text-gray-500 mt-1">Based on {aiAnswer.events_used} recent events</p>
              )}
            </div>
          )}
        </div>

        {/* Row 1: Summary widgets */}
        {!searchResults && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            <HealthOverview events={events} />
            <EventDistribution events={events} />
            <TopFailures events={events} />
          </div>
        )}

        {/* Row 2: Pod + EC2 health */}
        {!searchResults && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-4">
            <PodMetrics events={events} />
            <Ec2Health events={events} />
          </div>
        )}

        {/* Row 3: Event chart */}
        {!searchResults && (
          <div className="mb-4">
            <EventChart events={events} />
          </div>
        )}

        {/* Row 4: Timeline */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-700">
            <h2 className="text-sm font-semibold text-gray-800 dark:text-white">
              {searchResults ? 'Search Results' : 'Operational Timeline'}
            </h2>
          </div>
          <div className="p-4">
            <Timeline
              events={displayEvents}
              searchQuery={searchResults ? '' : searchQuery}
              loading={loading}
            />
          </div>
        </div>
      </main>
    </div>
  )
}
