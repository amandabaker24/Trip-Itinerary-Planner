import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import type { TripCreate, TripRead } from '../api/types'
import TripCard from '../components/TripCard'
import { useAuth } from '../context/AuthContext'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import SectionHeader from '../components/ui/SectionHeader'

export default function TripsListPage() {
  const [trips, setTrips] = useState<TripRead[]>([])
  const [form, setForm] = useState<TripCreate>({
    name: '',
    destination: '',
    start_date: '',
    end_date: '',
  })
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'upcoming' | 'past'>('all')
  const [loading, setLoading] = useState(false)

  const loadTrips = async () => {
    setLoading(true)
    try {
      const { data } = await api.get<TripRead[]>('/trips')
      setTrips(data.slice().sort((a, b) => b.id - a.id))
    } catch (err) {
      logout()
      navigate('/login')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTrips()
  }, [])

  const createTrip = async () => {
    setError(null)
    setSaving(true)
    try {
      await api.post('/trips', form)
      await loadTrips()
      setForm({ name: '', destination: '', start_date: '', end_date: '' })
    } catch (err) {
      setError('Could not create trip')
    } finally {
      setSaving(false)
    }
  }

  const filteredTrips = trips.filter((t) => {
    const end = new Date(t.end_date)
    const now = new Date()
    if (filter === 'upcoming') return end >= now
    if (filter === 'past') return end < now
    return true
  })

  const useTemplate = () => {
    const today = new Date()
    const nextFriday = new Date(today)
    nextFriday.setDate(today.getDate() + ((5 - today.getDay() + 7) % 7 || 7))
    const nextSunday = new Date(nextFriday)
    nextSunday.setDate(nextFriday.getDate() + 2)

    setForm({
      name: 'Weekend in Chicago',
      destination: 'Chicago',
      start_date: nextFriday.toISOString().slice(0, 10),
      end_date: nextSunday.toISOString().slice(0, 10),
    })
  }

  return (
    <div className="page">
      <div className="hero">
        <div>
          <p className="pill">TripIt</p>
          <h1>Plan your next trip</h1>
          <p className="muted">
            Create trips, build daily itineraries, track your budget, and watch for weather alerts.
          </p>
        </div>
      </div>

      <SectionHeader title="Create a trip" subtitle="Start by adding your destination and dates." />
      <Card>
        <div className="form-row">
          <label>
            Name
            <input required placeholder="e.g., Summer in Paris" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          </label>
          <label>
            Destination
            <input
              required
              placeholder="City or region"
              value={form.destination}
              onChange={(e) => setForm({ ...form, destination: e.target.value })}
            />
          </label>
          <label>
            Start date
            <input
              required
              type="date"
              value={form.start_date}
              onChange={(e) => setForm({ ...form, start_date: e.target.value })}
            />
          </label>
          <label>
            End date
            <input required type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} />
          </label>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <Button onClick={createTrip} disabled={saving || !form.name || !form.destination || !form.start_date || !form.end_date}>
              {saving ? 'Saving...' : 'Create trip'}
            </Button>
            <Button variant="ghost" onClick={useTemplate}>Use sample template</Button>
          </div>
        </div>
        {error && <p className="error">{error}</p>}
      </Card>

      <SectionHeader title="Your Trips" subtitle="Browse your itineraries and jump back in." />
      <div className="tabs">
        {(['all', 'upcoming', 'past'] as const).map((tab) => (
          <div key={tab} className={`tab ${filter === tab ? 'active' : ''}`} onClick={() => setFilter(tab)}>
            {tab === 'all' ? 'All' : tab === 'upcoming' ? 'Upcoming' : 'Past'}
          </div>
        ))}
      </div>
      {loading && <p className="muted">Loading trips...</p>}
      {error && <p className="error">{error}</p>}
      {filteredTrips.length === 0 && !loading ? (
        <Card>
          <p className="muted">No trips yet. Create one above to get started.</p>
        </Card>
      ) : (
        <div className="trip-grid">
          {filteredTrips.map((trip) => (
            <TripCard key={trip.id} trip={trip} onSelect={() => navigate(`/trips/${trip.id}`)} onDuplicate={async () => {
              await api.post('/trips', {
                name: `${trip.name} (Copy)`,
                destination: trip.destination,
                start_date: trip.start_date,
                end_date: trip.end_date,
              })
              await loadTrips()
            }} />
          ))}
        </div>
      )}
    </div>
  )
}
