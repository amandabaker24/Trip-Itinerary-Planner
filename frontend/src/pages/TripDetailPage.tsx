import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api, { fetchTripWeather } from '../api/client'
import type {
  BudgetEnvelopeCreate,
  BudgetEnvelopeRead,
  BudgetSummaryResponse,
  EventCreate,
  EventRead,
  ExpenseCreate,
  LocationRead,
  TripRead,
  TripWeatherResponse,
} from '../api/types'
import EventList from '../components/EventList'
import { useAuth } from '../context/AuthContext'
import PdfExportButton from '../components/PdfExportButton'
import SectionHeader from '../components/ui/SectionHeader'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'

const toF = (c: number) => Math.round((c * 9) / 5 + 32)

export default function TripDetailPage() {
  const { id } = useParams()
  const tripId = Number(id)
  const navigate = useNavigate()
  const { logout } = useAuth()

  const [trip, setTrip] = useState<TripRead | null>(null)
  const [events, setEvents] = useState<EventRead[]>([])
  const [budget, setBudget] = useState<BudgetSummaryResponse | null>(null)
  const [weather, setWeather] = useState<TripWeatherResponse | null>(null)

  const [eventForm, setEventForm] = useState<EventCreate>({
    trip_id: tripId,
    title: '',
    type: 'activity',
    date: '',
  } as EventCreate)
  const [expenseForm, setExpenseForm] = useState<ExpenseCreate>({
    trip_id: tripId,
    description: '',
    amount: 0,
    currency: 'USD',
    spent_at_date: '',
  })
  const [envelopeForm, setEnvelopeForm] = useState<BudgetEnvelopeCreate>({
    trip_id: tripId,
    category: '',
    planned_amount: 0,
    notes: '',
  })
  const [editingEnvelope, setEditingEnvelope] = useState<BudgetEnvelopeRead | null>(null)
  const [envelopeError, setEnvelopeError] = useState<string | null>(null)
  const [weatherLoading, setWeatherLoading] = useState(false)
  const [weatherError, setWeatherError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'itinerary' | 'budget' | 'weather'>('overview')
  const [destinations, setDestinations] = useState<{ id: number; sort_order: number; location: LocationRead }[]>([])
  const [destinationForm, setDestinationForm] = useState<{ name: string; type: string; address?: string }>({
    name: '',
    type: 'city',
    address: '',
  })
  const [dayRange, setDayRange] = useState<string[]>([])

  const loadData = async () => {
    try {
      const [tripRes, eventsRes, budgetRes, destRes] = await Promise.all([
        api.get<TripRead>(`/trips/${tripId}`),
        api.get<EventRead[]>(`/trips/${tripId}/events`),
        api.get<BudgetSummaryResponse>(`/trips/${tripId}/budget`),
        api.get(`/trips/${tripId}/destinations`),
      ])
      setTrip(tripRes.data)
      setEvents(eventsRes.data)
      setBudget(budgetRes.data)
      setDestinations(destRes.data)
    } catch {
      logout()
      navigate('/login')
    }
  }

  useEffect(() => {
    if (!id) return
    setEventForm((prev) => ({ ...prev, trip_id: tripId }))
    setExpenseForm((prev) => ({ ...prev, trip_id: tripId }))
    setEnvelopeForm((prev) => ({ ...prev, trip_id: tripId }))
    loadData()
  }, [id])

  useEffect(() => {
    if (!trip) return
    const days: string[] = []
    const start = new Date(trip.start_date)
    const end = new Date(trip.end_date)
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      days.push(new Date(d).toISOString().slice(0, 10))
    }
    setDayRange(days)
  }, [trip])

  useEffect(() => {
    const loadWeather = async () => {
      if (!tripId) return
      setWeatherLoading(true)
      setWeatherError(null)
      try {
        const data = await fetchTripWeather(tripId)
        setWeather(data)
      } catch {
        setWeatherError('Could not load weather right now.')
      } finally {
        setWeatherLoading(false)
      }
    }
    if (activeTab === 'weather') loadWeather()
  }, [activeTab, tripId])

  const plannedTotal = useMemo(() => {
    if (budget?.envelopes?.length) return budget.envelopes.reduce((sum, e) => sum + e.planned_amount, 0)
    return budget?.totals.planned_total_all ?? 0
  }, [budget])

  const actualTotal = useMemo(() => {
    if (budget?.expenses?.length) return budget.expenses.reduce((sum, e) => sum + e.amount, 0)
    return budget?.totals.actual_total_all ?? 0
  }, [budget])

  if (!trip) return <div className="page">Loading...</div>

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h2>{trip.name}</h2>
          <p className="muted">
            {trip.destination} · {trip.start_date} → {trip.end_date}
          </p>
        </div>
        <div className="pill">Trip #{trip.id}</div>
      </header>

      <div className="tabs">
        {(['overview', 'itinerary', 'budget', 'weather'] as const).map((tab) => (
          <div key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </div>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="page">
          <SectionHeader
            title="Overview"
            subtitle="At-a-glance stats for your trip."
            action={<PdfExportButton tripId={trip.id} />}
          />
          <div className="trip-grid">
            <Card>
              <h4>Dates</h4>
              <p>{trip.start_date} → {trip.end_date}</p>
            </Card>
            <Card>
              <h4>Destination</h4>
              <p>{trip.destination}</p>
            </Card>
            <Card>
              <h4>Events</h4>
              <p>{events.length}</p>
            </Card>
            <Card>
              <h4>Budget</h4>
              <p>${actualTotal.toFixed(2)} / ${plannedTotal.toFixed(2)}</p>
            </Card>
            {weather?.days?.length ? (
              <Card>
                <h4>Weather snapshot</h4>
                <div className="forecast-row">
                  {weather.days.map((f) => (
                    <div key={f.date} className="forecast-card">
                      <div className="muted">{f.date}</div>
                      <div style={{ color: f.precip_prob >= 70 ? '#f43f5e' : f.precip_prob >= 40 ? '#f59e0b' : '#22c55e' }}>
                        {f.summary}
                      </div>
                      <div className="muted">High {toF(f.temp_max)}°F · Low {toF(f.temp_min)}°F · Rain {f.precip_prob}%</div>
                    </div>
                  ))}
                </div>
              </Card>
            ) : null}
          </div>

          <SectionHeader title="Destinations" subtitle="Places you plan to visit." />
          <Card>
            <div className="form-row">
              <input placeholder="Name" value={destinationForm.name} onChange={(e) => setDestinationForm({ ...destinationForm, name: e.target.value })} />
              <input placeholder="Type (city, hotel, etc.)" value={destinationForm.type} onChange={(e) => setDestinationForm({ ...destinationForm, type: e.target.value })} />
              <input placeholder="Address" value={destinationForm.address} onChange={(e) => setDestinationForm({ ...destinationForm, address: e.target.value })} />
              <Button onClick={async () => {
                if (!destinationForm.name) { setMessage('Destination name required'); return }
                await api.post(`/trips/${tripId}/destinations`, destinationForm)
                setDestinationForm({ name: '', type: 'city', address: '' })
                setMessage(null)
                await loadData()
              }}>
                Add Destination
              </Button>
            </div>
            <ul>
              {destinations.map((dest) => (
                <li key={dest.id}>
                  <strong>{dest.location.name}</strong> · {dest.location.type}
                  <div className="muted">{dest.location.address}</div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.3rem' }}>
                    <Button variant="ghost" onClick={() => api.patch(`/trips/${tripId}/destinations/${dest.id}?direction=up`).then(loadData)}>↑</Button>
                    <Button variant="ghost" onClick={() => api.patch(`/trips/${tripId}/destinations/${dest.id}?direction=down`).then(loadData)}>↓</Button>
                    <Button variant="ghost" onClick={() => api.delete(`/trips/${tripId}/destinations/${dest.id}`).then(loadData)}>Remove</Button>
                  </div>
                </li>
              ))}
              {destinations.length === 0 && <p className="muted">No destinations yet.</p>}
            </ul>
          </Card>
        </div>
      )}

      {activeTab === 'itinerary' && (
        <div className="page">
          <SectionHeader title="Itinerary" subtitle="Day-by-day schedule." />
          <Card>
            <EventList
              events={events}
              days={dayRange}
              onAddForDay={(date) => {
                setEventForm((prev) => ({ ...prev, date }))
              }}
            />
            <div className="form-row" style={{ marginTop: '1rem' }}>
              <input
                placeholder="Title"
                value={eventForm.title}
                onChange={(e) => setEventForm({ ...eventForm, title: e.target.value })}
              />
              <input
                placeholder="Type (flight, hotel, meal, etc.)"
                value={eventForm.type}
                onChange={(e) => setEventForm({ ...eventForm, type: e.target.value })}
              />
              <input
                type="date"
                min={trip.start_date}
                max={trip.end_date}
                value={eventForm.date}
                onChange={(e) => setEventForm({ ...eventForm, date: e.target.value })}
              />
              <Button
                onClick={async () => {
                  if (!tripId) return
                  if (!eventForm.title || !eventForm.date) {
                    setMessage('Event title and date are required')
                    return
                  }
                  await api.post(`/trips/${tripId}/events`, { ...eventForm, trip_id: tripId })
                  setEventForm({ ...eventForm, title: '', date: '' })
                  setMessage(null)
                  await loadData()
                }}
              >
                Add Event
              </Button>
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'budget' && (
        <div className="page">
          <SectionHeader title="Budget" subtitle="Planned vs actual spending." />
          <p className="muted" style={{ marginTop: '-0.5rem' }}>
            Planned Total: ${plannedTotal.toFixed(2)} · Actual Total: ${actualTotal.toFixed(2)}
          </p>
          <Card>
            <div className="form-row">
              <input
                placeholder="Category"
                value={editingEnvelope ? editingEnvelope.category : envelopeForm.category}
                onChange={(e) =>
                  editingEnvelope
                    ? setEditingEnvelope({ ...editingEnvelope, category: e.target.value })
                    : setEnvelopeForm({ ...envelopeForm, category: e.target.value })
                }
              />
              <input
                type="number"
                placeholder="Planned amount"
                value={editingEnvelope ? editingEnvelope.planned_amount : envelopeForm.planned_amount}
                onChange={(e) =>
                  editingEnvelope
                    ? setEditingEnvelope({ ...editingEnvelope, planned_amount: Number(e.target.value) })
                    : setEnvelopeForm({ ...envelopeForm, planned_amount: Number(e.target.value) })
                }
              />
              <input
                placeholder="Notes"
                value={editingEnvelope ? editingEnvelope.notes || '' : envelopeForm.notes || ''}
                onChange={(e) =>
                  editingEnvelope
                    ? setEditingEnvelope({ ...editingEnvelope, notes: e.target.value })
                    : setEnvelopeForm({ ...envelopeForm, notes: e.target.value })
                }
              />
              <Button
                onClick={async () => {
                  if (!tripId) return
                  setEnvelopeError(null)
                  const category = editingEnvelope ? editingEnvelope.category : envelopeForm.category
                  const planned = editingEnvelope ? editingEnvelope.planned_amount : envelopeForm.planned_amount
                  if (!category || planned <= 0) {
                    setEnvelopeError('Category and planned amount (> 0) are required')
                    return
                  }
                  try {
                    if (editingEnvelope) {
                      await api.patch(`/envelopes/${editingEnvelope.id}`, { ...editingEnvelope, trip_id: tripId })
                      setEditingEnvelope(null)
                    } else {
                      await api.post(`/trips/${tripId}/envelopes`, { ...envelopeForm, trip_id: tripId })
                      setEnvelopeForm({ ...envelopeForm, category: '', planned_amount: 0, notes: '' })
                    }
                    await loadData()
                  } catch {
                    setEnvelopeError('Could not save category. Please try again.')
                  }
                }}
              >
                {editingEnvelope ? 'Update Category' : 'Add Category'}
              </Button>
            </div>
            {envelopeError && <p className="error">{envelopeError}</p>}
            <div style={{ marginTop: '1rem', overflowX: 'auto' }}>
              <table className="budget-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Planned</th>
                    <th>Actual</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {budget?.envelopes?.map((env) => {
                    const actual = budget.expenses
                      .filter((e) => e.envelope_id === env.id)
                      .reduce((sum, e) => sum + e.amount, 0)
                    const pct = env.planned_amount ? Math.min(100, Math.round((actual / env.planned_amount) * 100)) : 0
                    return (
                      <tr key={env.id}>
                        <td>{env.category}</td>
                        <td>${env.planned_amount.toFixed(2)}</td>
                        <td>
                          ${actual.toFixed(2)}
                          <div className="muted">{pct}% used</div>
                          <div className="progress">
                            <div className="progress-bar" style={{ width: `${pct}%` }} />
                          </div>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <Button variant="ghost" onClick={() => setEditingEnvelope(env)}>Edit</Button>
                            <Button variant="ghost" onClick={async () => {
                              await api.delete(`/envelopes/${env.id}`)
                              await loadData()
                            }}>Delete</Button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>

            <div className="form-row">
              <input
                placeholder="Expense description"
                value={expenseForm.description}
                onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })}
              />
              <input
                type="number"
                placeholder="Amount"
                value={expenseForm.amount}
                onChange={(e) => setExpenseForm({ ...expenseForm, amount: Number(e.target.value) })}
              />
              <select
                value={expenseForm.envelope_id || ''}
                onChange={(e) => setExpenseForm({ ...expenseForm, envelope_id: e.target.value ? Number(e.target.value) : undefined })}
              >
                <option value="">Uncategorized</option>
                {budget?.envelopes?.map((env) => (
                  <option key={env.id} value={env.id}>{env.category}</option>
                ))}
              </select>
              <input
                type="date"
                value={expenseForm.spent_at_date}
                onChange={(e) => setExpenseForm({ ...expenseForm, spent_at_date: e.target.value })}
              />
              <Button
                onClick={async () => {
                  if (!tripId) return
                  if (!expenseForm.description || !expenseForm.spent_at_date) {
                    setMessage('Expense description and date are required')
                    return
                  }
                  await api.post(`/trips/${tripId}/expenses`, { ...expenseForm, trip_id: tripId })
                  setExpenseForm({ ...expenseForm, description: '', amount: 0, spent_at_date: '' })
                  setMessage(null)
                  await loadData()
                }}
              >
                Add Expense
              </Button>
            </div>
            {message && <p className="muted">{message}</p>}
            <div style={{ marginTop: '1rem' }}>
              <h4>Expenses</h4>
              {budget?.expenses.map((exp) => (
                <div key={exp.id} className="event-day">
                  <div><strong>{exp.description}</strong> — ${exp.amount.toFixed(2)}</div>
                  <div className="muted">{exp.spent_at_date}</div>
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.3rem' }}>
                    <Button variant="ghost" onClick={async () => {
                      await api.delete(`/expenses/${exp.id}`)
                      await loadData()
                    }}>Delete</Button>
                  </div>
                </div>
              ))}
              {budget?.expenses.length === 0 && <p className="muted">No expenses yet.</p>}
            </div>
          </Card>
        </div>
      )}

      {activeTab === 'weather' && (
        <div className="page">
          <SectionHeader title="Weather" subtitle="Live forecast for your trip dates." />
          {weatherLoading && <p className="muted">Loading forecast...</p>}
          {weatherError && <p className="error">{weatherError}</p>}
          {weather && weather.days.length > 0 && (
            <div className="forecast-row">
              {weather.days.map((d) => (
                <div key={d.date} className="forecast-card">
                  <div className="muted">{d.date}</div>
                  <div style={{ fontWeight: 600 }}>{d.summary}</div>
                  <div className="muted">High {toF(d.temp_max)}°F · Low {toF(d.temp_min)}°F</div>
                  <div className="muted">Chance of rain: {d.precip_prob}%</div>
                  <div className="weather-alert" style={{ borderColor: '#6366f1', background: 'rgba(99,102,241,0.1)' }}>
                    <strong>Travel tip</strong>
                    <div className="muted">{d.advice}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
