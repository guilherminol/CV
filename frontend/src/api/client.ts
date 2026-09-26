// Typed client for GET /api/profile — mirrors the backend status envelope
// (backend/app/routes/profile.py). Native fetch only — no axios (STACK.md).

/** Loose shape of the validated profile — the backend owns the strict schema. */
export type Perfil = Record<string, unknown>

export type ProfileResponse =
  | { status: 'ok'; exemplo: boolean; perfil: Perfil }
  | { status: 'erro'; erros: string[] }

export async function fetchProfile(): Promise<ProfileResponse> {
  const resp = await fetch('/api/profile')
  if (!resp.ok) {
    throw new Error(`GET /api/profile falhou: ${resp.status}`)
  }
  return (await resp.json()) as ProfileResponse
}
