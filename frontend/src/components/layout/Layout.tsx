import React from 'react'
import { Header } from './Header'
import { HealthStatusIndicator } from '../HealthStatus'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <HealthStatusIndicator />
      <main className="max-w-7xl mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}
