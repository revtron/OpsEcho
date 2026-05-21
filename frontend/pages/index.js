import Head from 'next/head'
import { useState, useEffect } from 'react'
import Timeline from '../components/Timeline'
import SearchBar from '../components/SearchBar'

export default function Home() {
  const [events, setEvents] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    // Fetch events from the backend API
    fetch('/api/events')
      .then(response => response.json())
      .then(data => setEvents(data))
      .catch(err => console.error('Error fetching events:', err))
  }, [])

  const handleSearch = (query) => {
    setSearchQuery(query)
    // In a real app, we would call the search API
    console.log('Searching for:', query)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>OpsEcho - Operational Memory Platform</title>
        <meta name="description" content="Infrastructure memory and operational intelligence" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-800">OpsEcho</h1>
          <p className="text-gray-600 mt-2">Infrastructure memory and operational intelligence</p>
        </header>

        <div className="space-y-6">
          <SearchBar onSearch={handleSearch} />
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-xl font-semibold mb-4">Operational Timeline</h2>
            <Timeline events={events} searchQuery={searchQuery} />
          </div>
        </div>
      </main>
    </div>
  )
}