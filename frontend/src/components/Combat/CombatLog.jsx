// Last 5 entries only — matches backend COMBAT_LOG_WINDOW = 5 sliding window

import { useGameStore } from '../../stores/gameStore'

export function CombatLog() {
  const combatLog = useGameStore(s => s.combatLog)

  if (combatLog.length === 0) return null

  return (
    <div className="combat-log">
      <h4 className="log-heading">Combat</h4>
      <ul className="log-entries">
        {combatLog.map((entry, i) => (
          <li
            key={i}
            className={`log-entry ${i === combatLog.length - 1 ? 'latest' : ''}`}
          >
            {entry}
          </li>
        ))}
      </ul>
    </div>
  )
}
