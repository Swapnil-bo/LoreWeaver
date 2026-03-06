import { useMemo, useCallback } from 'react'
import ReactFlow, { Background, Controls, ReactFlowProvider } from 'reactflow'
import 'reactflow/dist/style.css'

import { useGameStore } from '../../stores/gameStore'
import { AlignmentOverlay } from './AlignmentOverlay'
import { RegionNode } from './RegionNode'

const nodeTypes = { region: RegionNode }

function WorldMapInner() {
  const mapNodes  = useGameStore(s => s.mapNodes)
  const mapEdges  = useGameStore(s => s.mapEdges)
  const quadrant  = useGameStore(s => s.quadrant)
  const intensity = useGameStore(s => s.intensity)

  const regionPositions = useMemo(
    () => mapNodes.map(n => ({ x: n.position?.x ?? 0, y: n.position?.y ?? 0 })),
    [mapNodes]
  )

  // Prevent React Flow from replacing nodes on drag (we manage position externally)
  const onNodesChange = useCallback(() => {}, [])

  return (
    <div className="world-map" style={{ width: '100%', height: '100%', position: 'relative' }}>
      <ReactFlow
        nodes={mapNodes}
        edges={mapEdges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        fitView
        minZoom={0.3}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="var(--world-accent, #333)" gap={40} size={1} />
        <Controls showInteractive={false} />
        <AlignmentOverlay
          quadrant={quadrant}
          intensity={intensity}
          regionPositions={regionPositions}
        />
      </ReactFlow>
    </div>
  )
}

export function WorldMap() {
  return (
    <ReactFlowProvider>
      <WorldMapInner />
    </ReactFlowProvider>
  )
}
