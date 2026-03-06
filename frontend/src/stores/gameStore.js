import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export const useGameStore = create(
  subscribeWithSelector((set, get) => ({
    // ── Alignment state ────────────────────────────────────────────────────────
    worldAlignment: { order_chaos: 0, harm_harmony: 0 },
    quadrant: 'justice',
    intensity: 0,

    updateAlignment: (alignment) => set({
      worldAlignment: alignment,
      quadrant: alignment.quadrant ?? getQuadrant(alignment),
      intensity: Math.max(Math.abs(alignment.order_chaos), Math.abs(alignment.harm_harmony)),
    }),

    // ── Map nodes (React Flow) ─────────────────────────────────────────────────
    mapNodes: [],
    mapEdges: [],

    // Constraint #8: mutate node.data ONLY — never replace full nodes array
    updateRegions: (updatedRegions) => set(state => ({
      mapNodes: state.mapNodes.map(node => {
        const updated = updatedRegions.find(r => r.region_id === node.id)
        if (!updated) return node
        return {
          ...node,
          data: {
            ...node.data,
            mood:        updated.base_mood,
            dangerLevel: updated.danger_level,
            explored:    updated.explored,
            alignment:   updated.alignment_modifiers,
          }
        }
      })
    })),

    setMapData: (nodes, edges) => set({ mapNodes: nodes, mapEdges: edges }),

    // ── Narrative streaming (Constraint #7: useRef + rAF in component) ─────────
    currentNarrative:   '',
    narrativeStreaming:  false,
    _latestChunk:       { chunk: '', done: false },
    _narrativeBuffer:   '',

    appendNarrativeChunk: (chunk, done) => set(s => ({
      _latestChunk:      { chunk, done },
      currentNarrative:  done ? s._narrativeBuffer + chunk : s.currentNarrative,
      _narrativeBuffer:  done ? '' : s._narrativeBuffer + chunk,
      narrativeStreaming: !done,
    })),

    setLastNarrative: (text) => set({ currentNarrative: text || '' }),

    // ── Choices ────────────────────────────────────────────────────────────────
    choices: [],
    setChoices: (choices) => set({ choices: choices || [] }),

    // ── Players ────────────────────────────────────────────────────────────────
    players: {},
    localPlayer: null,

    syncPlayers: (players) => set({ players: players || {} }),
    addPlayer:   (player) => set(s => ({
      players: { ...s.players, [player.player_id]: player }
    })),
    removePlayer: (playerId) => set(s => {
      const { [playerId]: _, ...rest } = s.players
      return { players: rest }
    }),
    setLocalPlayer: (identity) => set({ localPlayer: identity }),

    // ── Phase + turn ───────────────────────────────────────────────────────────
    phase: 'exploration',
    activeTurn: null,

    setPhase:      (phase) => set({ phase }),
    setActiveTurn: (playerId) => set({ activeTurn: playerId }),

    // ── Combat ─────────────────────────────────────────────────────────────────
    combatState: null,
    combatLog:   [],

    applyCombatUpdate: (data) => set(s => ({
      combatLog: [...s.combatLog.slice(-4), data.narration],
    })),

    // ── Dice (Constraint #14: server-dictated values only) ─────────────────────
    pendingDiceResult: null,
    setDiceResult:   (result) => set({ pendingDiceResult: result }),
    clearDiceResult: ()       => set({ pendingDiceResult: null }),

    // ── Voting ─────────────────────────────────────────────────────────────────
    activeVote: null,

    startVote:   (vote) => set({ activeVote: vote }),
    resolveVote: (result) => set(s => ({
      activeVote: s.activeVote ? { ...s.activeVote, resolved: true, result } : null,
    })),

    // ── Inner conflict (dissenter narrative) ───────────────────────────────────
    innerConflict: null,
    showInnerConflict: (text) => set({ innerConflict: text }),

    // ── Toast messages ─────────────────────────────────────────────────────────
    toast: null,
    showToast: (message) => {
      set({ toast: message })
      setTimeout(() => set({ toast: null }), 4000)
    },

    // ── Session expired ────────────────────────────────────────────────────────
    sessionExpired: false,
    handleSessionExpired: () => set({ sessionExpired: true }),
  }))
)

// ── Helper: derive quadrant from raw alignment values ──────────────────────
function getQuadrant({ order_chaos, harm_harmony }) {
  if (order_chaos >= 0 && harm_harmony >= 0) return 'justice'
  if (order_chaos >= 0 && harm_harmony < 0)  return 'tyranny'
  if (order_chaos < 0  && harm_harmony >= 0) return 'mercy'
  return 'anarchy'
}
