import { memo } from 'react'
import { Handle, Position } from 'reactflow'

// Constraint #8: React Flow receives data-only mutations.
// This component re-renders only when node.data changes — never remounts.

const MOOD_COLORS = {
  justice: '#ffd700',
  tyranny: '#cc0000',
  mercy:   '#90ee90',
  anarchy: '#ff4500',
  neutral: '#888888',
}

function RegionNodeInner({ data }) {
  const borderColor = MOOD_COLORS[data.mood] ?? MOOD_COLORS.neutral
  const explored = data.explored

  return (
    <div
      className={`region-node ${explored ? 'explored' : 'unexplored'}`}
      style={{
        border: `2px solid ${borderColor}`,
        boxShadow: explored ? `0 0 12px ${borderColor}40` : 'none',
      }}
    >
      <Handle type="target" position={Position.Top} style={{ visibility: 'hidden' }} />
      <div className="region-name">{data.label}</div>
      {explored && (
        <div className="region-info">
          <span className="danger-level">
            {'!'.repeat(Math.min(data.dangerLevel ?? 1, 5))}
          </span>
        </div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ visibility: 'hidden' }} />
    </div>
  )
}

export const RegionNode = memo(RegionNodeInner)
