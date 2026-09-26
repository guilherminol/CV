import { useQuery } from '@tanstack/react-query'

import { fetchProfile } from './api/client'
import { PlaceholderBanner } from './components/PlaceholderBanner'
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
    return <p className="text-red-600">{PERFIL_ERROR_TITLE}</p>
  }

  if (data.status === 'erro') {
    // Backend already renders PT-BR lines naming file + field (D-13/D-14).
    // Full ErrorPanel arrives in plan 03.
    return (
      <div className="rounded-md border border-red-300 bg-red-50 px-4 py-3">
        <p className="font-semibold text-red-700">{PERFIL_ERROR_TITLE}</p>
        <ul className="mt-2 list-disc pl-5 text-sm text-red-700">
          {data.erros.map((linha) => (
            <li key={linha} className="whitespace-pre-wrap">
              {linha}
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div>
      {data.exemplo && <PlaceholderBanner />}
      <h2 className="text-xl font-semibold text-gray-900">{PERFIL_SECTION_TITLE}</h2>
      <p className="mt-2 text-gray-700">
        Perfil carregado: <span className="font-medium">{data.perfil.name as string}</span>
      </p>
      {/* Completeness grid + resume-style preview arrive in plan 03 (D-12). */}
    </div>
  )
}

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <span className="text-lg font-bold">{APP_TITLE}</span>
          <nav className="flex gap-4">
            {NAV_ITEMS.map((item) => (
              <span
                key={item.id}
                className={
                  item.enabled
                    ? 'font-medium text-blue-600'
                    : 'text-gray-400' /* módulos futuros */
                }
                aria-disabled={!item.enabled}
              >
                {item.label}
              </span>
            ))}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-6">
        <PerfilHome />
      </main>
    </div>
  )
}
