import { useGameStore } from '../../stores/gameStore'
import { DiceRoller } from './DiceRoller'
import { CombatLog } from './CombatLog'

export function CombatOverlay() {
  const phase     = useGameStore(s => s.phase)
  const combatLog = useGameStore(s => s.combatLog)

  if (phase !== 'combat') return null

  return (
    <div className="combat-overlay">
      <div className="combat-header">
        <h3>Combat</h3>
      </div>
      <div className="combat-content">
        <DiceRoller />
        <CombatLog />
      </div>
    </div>
  )
}
