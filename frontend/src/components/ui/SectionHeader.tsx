import type { ReactNode } from 'react'

export default function SectionHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="section-header">
      <div>
        <h3>{title}</h3>
        {subtitle && <p className="muted">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}
