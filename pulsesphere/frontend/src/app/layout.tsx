import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'PulseSphere - Crisis Intelligence',
  description: 'Real-time brand crisis monitoring'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#050509] antialiased">{children}</body>
    </html>
  )
}
