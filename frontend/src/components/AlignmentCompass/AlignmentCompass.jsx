import { useGameStore } from '../../stores/gameStore'

const QUADRANT_LABELS = {
  justice: 'Justice',
  tyranny: 'Tyranny',
  mercy:   'Mercy',
  anarchy: 'Anarchy',
}

const QUADRANT_COLORS = {
  justice: '#ffd700',
  tyranny: '#cc0000',
  mercy:   '#90ee90',
  anarchy: '#ff4500',
}

export function AlignmentCompass() {
  const alignment = useGameStore(s => s.worldAlignment)
  const quadrant  = useGameStore(s => s.quadrant)

  // Map -100..100 to 0..100% for dot position
  const dotX = 50 + (alignment.order_chaos / 2)
  const dotY = 50 - (alignment.harm_harmony / 2)

  return (
    <div className="alignment-compass">
      <div className="compass-grid">
        {/* Axis labels */}
        <span className="axis-label top">Harmony</span>
        <span className="axis-label bottom">Harm</span>
        <span className="axis-label left">Chaos</span>
        <span className="axis-label right">Order</span>

        {/* Quadrant backgrounds */}
        <div className="quadrant tl" style={{ backgroundColor: QUADRANT_COLORS.mercy + '20' }} />
        <div className="quadrant tr" style={{ backgroundColor: QUADRANT_COLORS.justice + '20' }} />
        <div className="quadrant bl" style={{ backgroundColor: QUADRANT_COLORS.anarchy + '20' }} />
        <div className="quadrant br" style={{ backgroundColor: QUADRANT_COLORS.tyranny + '20' }} />

        {/* Crosshairs */}
        <div className="crosshair horizontal" />
        <div className="crosshair vertical" />

        {/* Position dot */}
        <div
          className="alignment-dot"
          style={{
            left: `${dotX}%`,
            top:  `${dotY}%`,
            backgroundColor: QUADRANT_COLORS[quadrant] ?? '#fff',
            boxShadow: `0 0 8px ${QUADRANT_COLORS[quadrant] ?? '#fff'}`,
          }}
        />
      </div>
      <div
        className="compass-label"
        style={{ color: QUADRANT_COLORS[quadrant] }}
      >
        {QUADRANT_LABELS[quadrant]}
      </div>
    </div>
  )
}
