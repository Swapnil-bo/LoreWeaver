import { useState } from 'react'
import { useWsStore } from '../../stores/wsStore'
import { useGameStore } from '../../stores/gameStore'

const CLASSES = [
  { id: 'warrior', label: 'Warrior', desc: 'Heavy armor, high HP, frontline fighter',   hp: 28 },
  { id: 'rogue',   label: 'Rogue',   desc: 'High dexterity, stealth, critical strikes', hp: 20 },
  { id: 'mage',    label: 'Mage',    desc: 'Powerful spells, low HP, high intelligence', hp: 14 },
  { id: 'cleric',  label: 'Cleric',  desc: 'Healer, wisdom-based, moderate armor',      hp: 22 },
  { id: 'ranger',  label: 'Ranger',  desc: 'Ranged combat, tracking, nature magic',     hp: 22 },
]

export function CharacterCreation({ onComplete }) {
  const send        = useWsStore(s => s.send)
  const localPlayer = useGameStore(s => s.localPlayer)
  const [name, setName]             = useState('')
  const [selectedClass, setSelected] = useState(null)

  function handleCreate(e) {
    e.preventDefault()
    if (!name.trim() || !selectedClass) return
    send({
      type:            'create_character',
      player_id:       localPlayer?.player_id,
      display_name:    name.trim(),
      character_class: selectedClass,
    })
    if (onComplete) onComplete()
  }

  return (
    <div className="character-creation">
      <h2>Create Your Hero</h2>
      <form onSubmit={handleCreate}>
        <label className="name-label">
          Name
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="Enter character name"
            maxLength={24}
          />
        </label>

        <div className="class-grid">
          {CLASSES.map(cls => (
            <button
              key={cls.id}
              type="button"
              className={`class-option ${selectedClass === cls.id ? 'selected' : ''}`}
              onClick={() => setSelected(cls.id)}
            >
              <span className="class-name">{cls.label}</span>
              <span className="class-desc">{cls.desc}</span>
              <span className="class-hp">HP: {cls.hp}</span>
            </button>
          ))}
        </div>

        <button
          type="submit"
          className="create-button"
          disabled={!name.trim() || !selectedClass}
        >
          Enter the World
        </button>
      </form>
    </div>
  )
}
