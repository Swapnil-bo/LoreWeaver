// Constraint #14: DiceRoller NEVER calls Math.random() for game values.
// Server rolls -> sends dice_result WS message -> frontend animates to that EXACT value.
// Math.random() is ONLY used for pre-roll spin duration (pure visual flourish).

import { useEffect, useRef } from 'react'
import { useGameStore } from '../../stores/gameStore'

// Maps d20 value (1-20) to CSS transform for each face
const D20_FACE_ROTATIONS = {
  1:  'rotateX(0deg)   rotateY(0deg)',
  2:  'rotateX(18deg)  rotateY(36deg)',
  3:  'rotateX(36deg)  rotateY(72deg)',
  4:  'rotateX(54deg)  rotateY(108deg)',
  5:  'rotateX(72deg)  rotateY(144deg)',
  6:  'rotateX(90deg)  rotateY(180deg)',
  7:  'rotateX(108deg) rotateY(216deg)',
  8:  'rotateX(126deg) rotateY(252deg)',
  9:  'rotateX(144deg) rotateY(288deg)',
  10: 'rotateX(162deg) rotateY(324deg)',
  11: 'rotateX(180deg) rotateY(0deg)',
  12: 'rotateX(198deg) rotateY(36deg)',
  13: 'rotateX(216deg) rotateY(72deg)',
  14: 'rotateX(234deg) rotateY(108deg)',
  15: 'rotateX(252deg) rotateY(144deg)',
  16: 'rotateX(270deg) rotateY(180deg)',
  17: 'rotateX(288deg) rotateY(216deg)',
  18: 'rotateX(306deg) rotateY(252deg)',
  19: 'rotateX(324deg) rotateY(288deg)',
  20: 'rotateX(0deg)   rotateY(180deg)',
}

export function DiceRoller() {
  const diceRef     = useRef(null)
  const spinningRef = useRef(false)

  useEffect(() => {
    // Subscribe to server dice results — NOT to Math.random()
    const unsub = useGameStore.subscribe(
      s => s.pendingDiceResult,
      (result) => {
        if (!result || spinningRef.current) return
        spinningRef.current = true
        animateDiceTo(result.d20, result.is_crit)
      }
    )
    return () => unsub()
  }, [])

  function animateDiceTo(targetValue, isCrit) {
    const el = diceRef.current
    if (!el) return

    // Random spin duration for visual variety (does NOT affect outcome)
    const spinDuration = 800 + Math.random() * 400  // 800-1200ms

    // Phase 1: fast random spin (pure visual flourish)
    el.style.transition = `transform ${spinDuration}ms ease-in`
    el.style.transform = `rotateX(${720 + Math.random() * 360}deg) rotateY(${720 + Math.random() * 360}deg)`
    el.classList.remove('crit-glow')

    // Phase 2: snap to server-dictated face
    setTimeout(() => {
      const finalRotation = D20_FACE_ROTATIONS[targetValue] ?? D20_FACE_ROTATIONS[1]
      el.style.transition = 'transform 400ms cubic-bezier(0.17, 0.67, 0.35, 1.0)'
      el.style.transform = finalRotation

      if (isCrit) el.classList.add('crit-glow')

      setTimeout(() => {
        spinningRef.current = false
        useGameStore.getState().clearDiceResult()
      }, 450)
    }, spinDuration + 50)
  }

  return (
    <div className="dice-container">
      <div ref={diceRef} className="dice-d20">
        {/* CSS 3D faces rendered via stylesheet */}
      </div>
    </div>
  )
}
