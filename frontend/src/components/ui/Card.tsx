import type { HTMLAttributes, ReactNode } from 'react'

type Props = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode
}

export default function Card({ children, className = '', ...rest }: Props) {
  return (
    <div className={`card-shell ${className}`} {...rest}>
      {children}
    </div>
  )
}
