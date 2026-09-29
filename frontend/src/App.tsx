import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { fetchProfile } from './api/client'
import { CompletenessGrid } from './components/CompletenessGrid'
import { ErrorPanel } from './components/ErrorPanel'
import { PlaceholderBanner } from './components/PlaceholderBanner'
import { ProfilePreview } from './components/ProfilePreview'
import { StatusLine } from './components/StatusLine'
import CurriculoHome from './pages/CurriculoHome'
import LinkedInHome from './pages/LinkedInHome'
import {
  APP_TITLE,
  NAV_ITEMS,
  PERFIL_ERROR_TITLE,
  PERFIL_LOADING,
  PERFIL_SECTION_TITLE,
} from './constants/ui'

function PerfilHome() {
  // React Query v5: single options object; initial-load state is isPending (Pitfall 9).
  const { data, isPending, isError } = useQuery({
    queryKey: ['perfil'],
    queryFn: fetchProfile,
  })

  if (isPending) {
    return <p className="text-gray-500">{PERFIL_LOADING}</p>
  }

  if (isError || !data) {
    // Only reachable when the fetch itself fails (server down) — the backend
    // never answers 500 for a broken profile (Pattern 4).
    return <p className="text-red-600">{PERFIL_ERROR_TITLE}</p>
  }

  if (data.status === 'erro') {
    // Broken profile = rendered UI state (D-12/D-13): the ErrorPanel shows the
    // backend's PT-BR lines verbatim; the app shell stays up.
    return (
      <div className="space-y-4">
        <StatusLine ok={false} />
        <ErrorPanel erros={data.erros} />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <StatusLine ok={true} />
      {data.exemplo && <PlaceholderBanner />}
      <h2 className="text-xl font-semibold text-gray-900">{PERFIL_SECTION_TITLE}</h2>
      {/* Perfil home assembly (D-12): completeness at a glance, then the
          resume-style preview — visual order the Phase 4 print template
          will build on. */}
      <CompletenessGrid completude={data.completude} />
      <ProfilePreview perfil={data.perfil} />
    </div>
  )
}

export default function App() {
  // Plan 03-04: minimal view switch — no router dependency (STACK.md lean stack).
  // Currículo is the default landing view (the phase's core flow; planner decision).
  // Phase 6 (D-01): the LinkedIn placeholder becomes the third view.
  const [view, setView] = useState<'curriculo' | 'perfil' | 'linkedin'>('curriculo')

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <span className="text-lg font-bold">{APP_TITLE}</span>
          <nav className="flex gap-4">
            {NAV_ITEMS.map((item) =>
              item.enabled ? (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setView(item.id)}
                  aria-current={view === item.id ? 'true' : undefined}
                  className={
                    view === item.id
                      ? 'rounded font-medium text-blue-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                      : 'rounded font-medium text-gray-600 hover:text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600'
                  }
                >
                  {item.label}
                </button>
              ) : (
                <span
                  key={item.id}
                  className="text-gray-400" /* módulos futuros */
                  aria-disabled={!item.enabled}
                >
                  {item.label}
                </span>
              ),
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-6">
        {view === 'perfil' ? <PerfilHome /> : view === 'linkedin' ? <LinkedInHome /> : <CurriculoHome />}
      </main>
    </div>
  )
}
