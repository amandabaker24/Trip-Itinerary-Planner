import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost'
  children: ReactNode
}

export default function Button({ variant = 'primary', children, ...props }: Props) {
  return (
    <button className={`btn ${variant}`} {...props}>
      {children}
    </button>
  )
}
