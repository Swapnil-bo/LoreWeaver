import { useGameStore } from '../../stores/gameStore'
import { useWsStore } from '../../stores/wsStore'
import { NarrativeBlock } from './NarrativeBlock'
import { ChoicePanel } from './ChoicePanel'
import { VoteTracker } from './VoteTracker'
import { useState } from 'react'

export function StoryConsole() {
  const narrativeStreaming = useGameStore(s => s.narrativeStreaming)
  const currentNarrative  = useGameStore(s => s.currentNarrative)
  const innerConflict     = useGameStore(s => s.innerConflict)
  const phase             = useGameStore(s => s.phase)
  const send              = useWsStore(s => s.send)
  const localPlayer       = useGameStore(s => s.localPlayer)
  const [actionInput, setActionInput] = useState('')

  function handleAction(e) {
    e.preventDefault()
    if (!actionInput.trim() || narrativeStreaming) return
    send({
      type:      'player_action',
      action:    actionInput.trim(),
      player_id: localPlayer?.player_id,
    })
    setActionInput('')
  }

  return (
    <div className="story-console">
      <div className="narrative-area">
        {currentNarrative && !narrativeStreaming && (
          <p className="narrative-text done">{currentNarrative}</p>
        )}
        <NarrativeBlock />
      </div>

      {innerConflict && (
        <div className="inner-conflict">
          <em>{innerConflict}</em>
        </div>
      )}

      <VoteTracker />
      <ChoicePanel />

      {phase === 'exploration' && (
        <form className="action-input" onSubmit={handleAction}>
          <input
            type="text"
            value={actionInput}
            onChange={e => setActionInput(e.target.value)}
            placeholder={narrativeStreaming ? 'The DM is speaking...' : 'What do you do?'}
            disabled={narrativeStreaming}
          />
          <button type="submit" disabled={narrativeStreaming || !actionInput.trim()}>
            Act
          </button>
        </form>
      )}
    </div>
  )
}
