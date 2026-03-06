import { useGameStore } from '../../stores/gameStore'
import { CharacterCard } from './CharacterCard'

export function PartyPanel() {
  const players     = useGameStore(s => s.players)
  const activeTurn  = useGameStore(s => s.activeTurn)
  const localPlayer = useGameStore(s => s.localPlayer)

  const playerList = Object.values(players)

  if (playerList.length === 0) return null

  return (
    <div className="party-panel">
      <h3 className="panel-heading">Party</h3>
      <div className="party-list">
        {playerList.map(p => (
          <CharacterCard
            key={p.player_id}
            player={p}
            isActive={activeTurn === p.player_id}
            isLocal={localPlayer?.player_id === p.player_id}
          />
        ))}
      </div>
    </div>
  )
}
