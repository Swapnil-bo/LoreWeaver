import { create } from 'zustand'
import { useGameStore } from './gameStore'

// ── Section 10.6: Typed message dispatcher ─────────────────────────────────
const MESSAGE_HANDLERS = {
  narrative_stream:  (d) => useGameStore.getState().appendNarrativeChunk(d.chunk, d.done),
  turn_complete:     (d) => useGameStore.getState().setChoices(d.choices),
  combat_update:     (d) => useGameStore.getState().applyCombatUpdate(d),
  world_shift:       (d) => useGameStore.getState().updateAlignment(d.alignment),
  map_update:        (d) => useGameStore.getState().updateRegions(d.regions),
  vote_started:      (d) => useGameStore.getState().startVote(d),
  vote_result:       (d) => useGameStore.getState().resolveVote(d),
  inner_conflict:    (d) => useGameStore.getState().showInnerConflict(d.text),
  action_rejected:   (d) => useGameStore.getState().showToast(d.reason),
  dice_result:       (d) => useGameStore.getState().setDiceResult(d),
  full_state_sync:   (d) => {
    const s = useGameStore.getState()
    s.updateAlignment(d.world_alignment)
    if (d.regions) s.updateRegions(d.regions)
    s.syncPlayers(d.players)
    s.setPhase(d.current_phase)
    s.setLastNarrative(d.last_narrative)
    if (d.last_choices) s.setChoices(d.last_choices)
    if (d.active_vote) {
      const remainingMs = (d.active_vote.deadline_ts * 1000) - Date.now()
      if (remainingMs > 0) s.startVote({ ...d.active_vote, remainingMs })
    }
  },
  player_joined:     (d) => useGameStore.getState().addPlayer(d.player),
  player_left:       (d) => useGameStore.getState().removePlayer(d.player_id),
  turn_indicator:    (d) => useGameStore.getState().setActiveTurn(d.active_player),
  session_expired:   ()  => useGameStore.getState().handleSessionExpired(),
  identity_issued:   (d) => {
    localStorage.setItem('lw_player_id',       d.identity.player_id)
    localStorage.setItem('lw_reconnect_token', d.identity.reconnect_token)
    useGameStore.getState().setLocalPlayer(d.identity)
  },
  pong: () => {},
}

export const useWsStore = create((set, get) => ({
  socket: null,
  connected: false,
  _reconnectAttempts: 0,

  connect: (sessionId) => {
    const token = localStorage.getItem('lw_reconnect_token')
    const ws = new WebSocket(
      `ws://localhost:8000/ws?token=${token ?? ''}`
    )

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      const handler = MESSAGE_HANDLERS[data.type]
      if (handler) handler(data)
      else console.warn('[WS] Unhandled:', data.type)
    }

    ws.onclose = () => {
      set({ connected: false })
      const delay = Math.min(1000 * 2 ** get()._reconnectAttempts, 30000)
      set(s => ({ _reconnectAttempts: s._reconnectAttempts + 1 }))
      setTimeout(() => get().connect(sessionId), delay)
    }

    ws.onopen = () => {
      set({ connected: true, _reconnectAttempts: 0 })
      const reconnectToken = localStorage.getItem('lw_reconnect_token')
      if (reconnectToken) {
        get().send({ type: 'reconnect', reconnect_token: reconnectToken })
      }
      if (sessionId) {
        get().send({ type: 'join_session', session_id: sessionId })
      }
    }

    set({ socket: ws })
  },

  // Constraint #10: explicit disconnect — prevents Vite HMR zombie connections
  disconnect: () => {
    const { socket } = get()
    if (socket) {
      socket.onclose = null   // prevent auto-reconnect on intentional close
      socket.close(1000, 'HMR cleanup')
      set({ socket: null, connected: false })
    }
  },

  send: (msg) => {
    const { socket } = get()
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(msg))
    }
  },
}))
