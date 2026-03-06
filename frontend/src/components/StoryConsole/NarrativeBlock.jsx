// Constraint #7: useRef + requestAnimationFrame — NOT useState.
// Tokens arrive every 20-50ms. useState = 20-50 re-renders/sec = UI freeze.
// useRef + rAF = zero re-renders during stream. One re-render when done.

import { useRef, useEffect, useState } from 'react'
import { useGameStore } from '../../stores/gameStore'

export function NarrativeBlock() {
  const containerRef = useRef(null)
  const bufferRef    = useRef('')
  const rafRef       = useRef(null)
  const [isDone, setIsDone] = useState(false)

  useEffect(() => {
    const unsub = useGameStore.subscribe(
      s => s._latestChunk,
      ({ chunk, done }) => {
        if (!chunk && !done) return
        bufferRef.current += chunk

        if (!rafRef.current) {
          rafRef.current = requestAnimationFrame(() => {
            if (containerRef.current)
              containerRef.current.textContent = bufferRef.current
            rafRef.current = null
          })
        }

        if (done) {
          setIsDone(true)
          bufferRef.current = ''
        }
      }
    )
    return () => {
      unsub()
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return <p ref={containerRef} className={`narrative-text ${isDone ? 'done' : 'streaming'}`} />
}
