import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCorners,
  useSensor,
  useSensors,
  useDroppable,
  type DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable'
import type { CandidaturaDTO, EstagioDTO } from '../../api/client'
import { CandidaturaCard } from './CandidaturaCard'
import {
  RASTREADOR_COLUNA_CLASSES,
  RASTREADOR_COLUNA_CORPO_CLASSES,
  RASTREADOR_COLUNA_HEADER_CLASSES,
  RASTREADOR_COLUNA_VAZIA,
} from '../../constants/ui'

// Column droppable ids are PREFIXED strings so they can never collide with a
// card id (candidatura and estagio PKs are independent counters).
const PREFIXO_COLUNA = 'estagio-'

interface KanbanBoardProps {
  estagios: EstagioDTO[]
  candidaturas: CandidaturaDTO[]
  abertaId: number | null
  onAbrir: (candidaturaId: number) => void
  onMover: (candidaturaId: number, estagioId: number) => void
}

interface ColunaProps {
  estagio: EstagioDTO
  candidaturas: CandidaturaDTO[]
  abertaId: number | null
  onAbrir: (candidaturaId: number) => void
}

/** One column: header + a droppable body that accepts drops even when EMPTY
 * (useDroppable keyed by the prefixed stage id). The SortableContext items
 * array derives from THE SAME filtered array the JSX maps over (Pitfall 10 —
 * items and render order can never diverge). */
function KanbanColuna({ estagio, candidaturas, abertaId, onAbrir }: ColunaProps) {
  const { setNodeRef, isOver } = useDroppable({ id: `${PREFIXO_COLUNA}${estagio.id}` })
  const ids = candidaturas.map((candidatura) => candidatura.id)
  return (
    <div className={RASTREADOR_COLUNA_CLASSES}>
      <h4 className={RASTREADOR_COLUNA_HEADER_CLASSES}>
        {estagio.nome} ({candidaturas.length})
      </h4>
      <SortableContext items={ids} strategy={verticalListSortingStrategy}>
        <div
          ref={setNodeRef}
          className={`${RASTREADOR_COLUNA_CORPO_CLASSES} min-h-16 ${isOver ? 'bg-gray-50' : ''}`}
        >
          {candidaturas.map((candidatura) => (
            <CandidaturaCard
              key={candidatura.id}
              candidatura={candidatura}
              estagioNome={estagio.nome}
              aberta={abertaId === candidatura.id}
              onAbrir={onAbrir}
            />
          ))}
          {candidaturas.length === 0 && (
            <p className="text-sm text-gray-400">{RASTREADOR_COLUNA_VAZIA}</p>
          )}
        </div>
      </SortableContext>
    </div>
  )
}

/**
 * The D-14 ready-made DnD board (RESEARCH Pattern 5 verbatim — zero
 * hand-rolled drag): ONE DndContext with PointerSensor(distance 8 — clicks
 * stay clicks, Pitfall 4) + KeyboardSensor(sortableKeyboardCoordinates) and
 * closestCorners; one SortableContext per column; every drop resolves through
 * the mover mutation — NO optimistic update (A8: the ['tracker'] refetch is
 * the truth), and intra-column reordering is not persisted (no candidatura
 * ordem exists — the refetch restores payload order).
 */
export function KanbanBoard({ estagios, candidaturas, abertaId, onAbrir, onMover }: KanbanBoardProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const resolverEstagio = (overId: string | number): number | null => {
    if (typeof overId === 'string' && overId.startsWith(PREFIXO_COLUNA)) {
      return Number(overId.slice(PREFIXO_COLUNA.length))
    }
    const card = candidaturas.find((candidatura) => candidatura.id === overId)
    return card ? card.estagio_id : null
  }

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over) return
    const origem = candidaturas.find((candidatura) => candidatura.id === active.id)
    const estagioAlvo = resolverEstagio(over.id)
    // Same-stage "moves" (visual intra-column sorts) never fire a mutation.
    if (!origem || estagioAlvo === null || estagioAlvo === origem.estagio_id) return
    onMover(origem.id, estagioAlvo)
  }

  return (
    <DndContext sensors={sensors} collisionDetection={closestCorners} onDragEnd={handleDragEnd}>
      {/* A-UI-1: horizontal scroll keeps the max-w-3xl shell intact — 5+
          stage columns never squeeze and the shell never widens. */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {estagios.map((estagio) => (
          <KanbanColuna
            key={estagio.id}
            estagio={estagio}
            candidaturas={candidaturas.filter(
              (candidatura) => candidatura.estagio_id === estagio.id,
            )}
            abertaId={abertaId}
            onAbrir={onAbrir}
          />
        ))}
      </div>
    </DndContext>
  )
}
