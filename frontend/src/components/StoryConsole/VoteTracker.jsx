import { useEffect, useState } from 'react'
import { useGameStore } from '../../stores/gameStore'

export function VoteTracker() {
  const activeVote = useGameStore(s => s.activeVote)
  const players    = useGameStore(s => s.players)
  const [timeLeft, setTimeLeft] = useState(0)

  useEffect(() => {
    if (!activeVote || activeVote.resolved) return

    const deadline = activeVote.deadline_ts
      ? activeVote.deadline_ts * 1000
      : Date.now() + (activeVote.remainingMs ?? 30000)

    function tick() {
      const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
      setTimeLeft(remaining)
    }
    tick()
    const interval = setInterval(tick, 1000)
    return () => clearInterval(interval)
  }, [activeVote])

  if (!activeVote || activeVote.resolved) return null

  const totalPlayers = Object.keys(players).length
  const votedCount   = Object.keys(activeVote.votes ?? {}).length

  return (
    <div className="vote-tracker">
      <div className="vote-timer">
        <span className={`countdown ${timeLeft <= 5 ? 'urgent' : ''}`}>
          {timeLeft}s
        </span>
      </div>
      <div className="vote-progress">
        {votedCount}/{totalPlayers} voted
      </div>
      {activeVote.result && (
        <div className="vote-result">
          Decision made{activeVote.result.was_tie_broken ? ' (leader broke tie)' : ''}
        </div>
      )}
    </div>
  )
}
