import { useEffect } from 'react'
import { useWsStore } from './stores/wsStore'
import { useGameStore } from './stores/gameStore'
import './App.css'

export default function App() {
  const { connect, disconnect } = useWsStore()
  const sessionExpired = useGameStore(s => s.sessionExpired)
  const toast = useGameStore(s => s.toast)
  const connected = useWsStore(s => s.connected)

  useEffect(() => {
    const sessionId = localStorage.getItem('lw_session_id')
    if (sessionId) connect(sessionId)

    // Constraint #10: cleanup runs on unmount AND on every Vite HMR reload.
    // Without this: every Ctrl+S = 1 zombie WebSocket.
    // After 50 saves: FastAPI broadcasting to 50 dead sockets -> crash.
    return () => disconnect()
  }, [])

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

  return (
    <div className="app-container">
      <header className="app-header">
        <h1 className="app-title">LoreWeaver</h1>
        <div className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
          {connected ? 'Connected' : 'Reconnecting...'}
        </div>
      </header>

      <main className="app-main">
        <p className="placeholder">World map and story console coming soon.</p>
      </main>

      {toast && (
        <div className="toast">{toast}</div>
      )}
    </div>
  )
}
