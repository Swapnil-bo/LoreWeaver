import { useEffect, useState } from 'react'
import { useWsStore } from './stores/wsStore'
import { useGameStore } from './stores/gameStore'
import { applyTheme } from './utils/themeEngine'
import { WorldMap } from './components/WorldMap/WorldMap'
import { StoryConsole } from './components/StoryConsole/StoryConsole'
import { PartyPanel } from './components/PartyPanel/PartyPanel'
import { CombatOverlay } from './components/Combat/CombatOverlay'
import { AlignmentCompass } from './components/AlignmentCompass/AlignmentCompass'
import { CharacterCreation } from './components/CharacterCreation/CharacterCreation'
import './App.css'

export default function App() {
  const { connect, disconnect } = useWsStore()
  const sessionExpired = useGameStore(s => s.sessionExpired)
  const toast          = useGameStore(s => s.toast)
  const connected      = useWsStore(s => s.connected)
  const quadrant       = useGameStore(s => s.quadrant)
  const localPlayer    = useGameStore(s => s.localPlayer)
  const [showCreation, setShowCreation] = useState(false)

  // Constraint #10: connect on mount, disconnect on unmount/HMR
  useEffect(() => {
    const sessionId = localStorage.getItem('lw_session_id')
    if (sessionId) connect(sessionId)
    return () => disconnect()
  }, [])

  // Apply quadrant theme whenever alignment changes
  useEffect(() => {
    applyTheme(quadrant)
  }, [quadrant])

  // Show character creation if no local player
  useEffect(() => {
    if (connected && !localPlayer) setShowCreation(true)
  }, [connected, localPlayer])

  if (sessionExpired) {
    return (
      <div className="session-expired">
        <h1>Session Expired</h1>
        <p>Your session has timed out. Please refresh to start a new adventure.</p>
        <button onClick={() => {
          localStorage.removeItem('lw_session_id')
          localStorage.removeItem('lw_reconnect_token')
          window.location.reload()
        }}>
          New Session
        </button>
      </div>
    )
  }

  if (showCreation) {
    return <CharacterCreation onComplete={() => setShowCreation(false)} />
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">LoreWeaver</h1>
        <AlignmentCompass />
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? 'Connected' : 'Reconnecting...'}
        </div>
      </header>

      <main className="app-main">
        <section className="map-section">
          <WorldMap />
        </section>

        <aside className="sidebar">
          <StoryConsole />
          <PartyPanel />
        </aside>
      </main>

      <CombatOverlay />

      {toast && (
        <div className="toast">{toast}</div>
      )}
    </div>
  )
}
