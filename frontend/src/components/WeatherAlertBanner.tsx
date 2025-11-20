import type { WeatherAlertWithEvents, WeatherForecastEntry } from '../api/types'

type Props = {
  alerts: WeatherAlertWithEvents[]
  forecast?: WeatherForecastEntry[]
}

const severityColor = (sev: string) => {
  if (sev === 'high') return '#f43f5e'
  if (sev === 'medium') return '#f59e0b'
  return '#22c55e'
}

export default function WeatherAlertBanner({ alerts, forecast = [] }: Props) {
  return (
    <div className="weather-alerts">
      {forecast.length > 0 && (
        <div className="weather-alert" style={{ borderColor: '#22c55e' }}>
          <div>
            <strong>Forecast this trip</strong>
          </div>
          <div className="forecast-row">
            {forecast.map((f) => (
              <div key={f.date} className="forecast-card">
                <div className="muted">{f.date}</div>
                <div style={{ color: severityColor(f.severity) }}>{f.summary}</div>
                <div className="pill" style={{ background: severityColor(f.severity), color: '#0b1220' }}>
                  {f.severity.toUpperCase()}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {alerts.length === 0 && <div className="muted">No weather alerts right now.</div>}
      {alerts.map(({ alert, suggested_alternative, events }) => (
        <div key={alert.id} className="weather-alert" style={{ borderColor: severityColor(alert.severity) }}>
          <div>
            <span style={{ color: severityColor(alert.severity), fontWeight: 700 }}>
              {alert.severity.toUpperCase()}
            </span>{' '}
            · {alert.summary} ({alert.date})
          </div>
          {events.length > 0 && (
            <ul>
              {events.map((evt) => (
                <li key={evt.id}>{evt.title}</li>
              ))}
            </ul>
          )}
          <div className="suggestion">{suggested_alternative}</div>
        </div>
      ))}
    </div>
  )
}
