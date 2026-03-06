import { useGameStore } from '../../stores/gameStore'
import { useWsStore } from '../../stores/wsStore'

export function ChoicePanel() {
  const choices           = useGameStore(s => s.choices)
  const narrativeStreaming = useGameStore(s => s.narrativeStreaming)
  const localPlayer       = useGameStore(s => s.localPlayer)
  const send              = useWsStore(s => s.send)

  if (!choices || choices.length === 0) return null

  function handleChoice(index) {
    if (narrativeStreaming) return
    send({
      type:         'vote_choice',
      choice_index: index,
      player_id:    localPlayer?.player_id,
    })
  }

  return (
    <div className="choice-panel">
      <h3 className="choice-heading">What will the party do?</h3>
      {choices.map((choice, i) => (
        <button
          key={i}
          className="choice-button"
          disabled={narrativeStreaming}
          onClick={() => handleChoice(i)}
        >
          <span className="choice-text">{choice.text}</span>
          <span className="choice-shifts">
            {choice.order_chaos_shift !== 0 && (
              <span className={`shift ${choice.order_chaos_shift > 0 ? 'order' : 'chaos'}`}>
                {choice.order_chaos_shift > 0 ? '+' : ''}{choice.order_chaos_shift} O/C
              </span>
            )}
            {choice.harm_harmony_shift !== 0 && (
              <span className={`shift ${choice.harm_harmony_shift > 0 ? 'harmony' : 'harm'}`}>
                {choice.harm_harmony_shift > 0 ? '+' : ''}{choice.harm_harmony_shift} H/H
              </span>
            )}
          </span>
        </button>
      ))}
    </div>
  )
}
