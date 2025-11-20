import type { TripRead } from '../api/types'
import Card from './ui/Card'
import Button from './ui/Button'

type Props = {
  trip: TripRead
  onSelect: () => void
  onDuplicate: () => void
}

export default function TripCard({ trip, onSelect, onDuplicate }: Props) {
  return (
    <Card className="trip-card">
      <h3>{trip.name}</h3>
      <p className="muted">{trip.destination}</p>
      <p className="muted">
        {trip.start_date} → {trip.end_date}
      </p>
      <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.75rem' }}>
        <Button onClick={onSelect}>Open itinerary</Button>
        <Button variant="ghost" onClick={onDuplicate}>Duplicate</Button>
      </div>
    </Card>
  )
}
