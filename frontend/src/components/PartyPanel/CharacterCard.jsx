import { memo } from 'react'

const CLASS_ICONS = {
  warrior: '&#x2694;',
  rogue:   '&#x1F5E1;',
  mage:    '&#x2728;',
  cleric:  '&#x271D;',
  ranger:  '&#x1F3F9;',
}

function CharacterCardInner({ player, isActive, isLocal }) {
  const hpPercent = Math.max(0, Math.round((player.hp / player.max_hp) * 100))
  const hpColor = hpPercent > 50 ? '#4caf50' : hpPercent > 25 ? '#ff9800' : '#f44336'

  return (
    <div className={`character-card ${isActive ? 'active-turn' : ''} ${isLocal ? 'local' : ''} ${!player.is_connected ? 'disconnected' : ''}`}>
      <div className="card-header">
        <span
          className="class-icon"
          dangerouslySetInnerHTML={{ __html: CLASS_ICONS[player.character_class] ?? '?' }}
        />
        <span className="player-name">{player.display_name}</span>
        {!player.is_connected && <span className="dc-badge">DC</span>}
      </div>
      <div className="hp-bar-container">
        <div
          className="hp-bar"
          style={{ width: `${hpPercent}%`, backgroundColor: hpColor }}
        />
        <span className="hp-text">{player.hp}/{player.max_hp}</span>
      </div>
      <div className="card-stats">
        <span>AC {player.stats?.ac ?? 10}</span>
        <span className="class-label">{player.character_class}</span>
      </div>
    </div>
  )
}

export const CharacterCard = memo(CharacterCardInner)
