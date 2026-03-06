// Constraint #6: useStoreApi() for D3 canvas — NOT useViewport().
// useViewport() has async lag. useStoreApi() reads synchronously every frame.
// Canvas transform ALWAYS matches React Flow SVG — zero lag at any pan speed.

import { useEffect, useRef } from 'react'
import { useStoreApi } from 'reactflow'

const MAX_PARTICLES = 60
const CONFIGS = {
  justice: { color: '#ffd700', speed: 0.5 },
  tyranny: { color: '#ff4444', speed: 1.2 },
  mercy:   { color: '#90ee90', speed: 0.3 },
  anarchy: { color: '#ff6600', speed: 0.8 },
}

export function AlignmentOverlay({ quadrant, intensity, regionPositions }) {
  const canvasRef    = useRef(null)
  const store        = useStoreApi()
  const particlesRef = useRef([])

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx    = canvas.getContext('2d')
    const config = CONFIGS[quadrant] ?? CONFIGS.justice
    const count  = Math.floor((intensity / 100) * MAX_PARTICLES)

    particlesRef.current = Array.from({ length: count }, (_, i) => {
      const r = regionPositions[i % regionPositions.length] ?? { x: 300, y: 300 }
      return {
        x: r.x + (Math.random() - 0.5) * 200,
        y: r.y + (Math.random() - 0.5) * 200,
        vx: (Math.random() - 0.5) * config.speed,
        vy: (Math.random() - 0.5) * config.speed,
        alpha: Math.random(),
        size: Math.random() * 3 + 1,
        life: Math.random(),
      }
    })

    let animId
    function frame() {
      const { transform } = store.getState()   // synchronous read, zero lag
      const [x, y, zoom]  = transform
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width
      canvas.height = rect.height
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.save()
      ctx.translate(x, y)
      ctx.scale(zoom, zoom)

      particlesRef.current.forEach(p => {
        p.x += p.vx
        p.y += p.vy
        p.life += 0.005
        p.alpha = Math.sin(p.life * Math.PI)
        if (p.life >= 1) {
          const r = regionPositions[Math.floor(Math.random() * regionPositions.length)]
          p.x = r.x + (Math.random() - 0.5) * 150
          p.y = r.y + (Math.random() - 0.5) * 150
          p.life = 0
          p.vx = (Math.random() - 0.5) * config.speed
          p.vy = (Math.random() - 0.5) * config.speed
        }
        ctx.globalAlpha = Math.max(0, p.alpha) * 0.7
        ctx.fillStyle = config.color
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fill()
      })

      ctx.restore()
      ctx.globalAlpha = 1
      animId = requestAnimationFrame(frame)
    }
    animId = requestAnimationFrame(frame)
    return () => cancelAnimationFrame(animId)
  }, [quadrant, intensity])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 10,
      }}
    />
  )
}
