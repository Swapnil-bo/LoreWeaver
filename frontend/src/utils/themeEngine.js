// Section 12.6: Visual theme system — CSS variables driven by world alignment quadrant

export const ALIGNMENT_THEMES = {
  justice: {
    '--world-bg-start': '#1a1a2e',
    '--world-bg-end':   '#16213e',
    '--world-accent':   '#e2b714',
    '--node-border':    '#ffd700',
    '--node-glow':      'rgba(255,215,0,0.3)',
    '--map-filter':     'brightness(1.1) saturate(1.2)',
  },
  tyranny: {
    '--world-bg-start': '#0d0d0d',
    '--world-bg-end':   '#1a0a0a',
    '--world-accent':   '#8b0000',
    '--node-border':    '#cc0000',
    '--node-glow':      'rgba(139,0,0,0.4)',
    '--map-filter':     'contrast(1.3) saturate(0.6)',
  },
  mercy: {
    '--world-bg-start': '#0a1a0a',
    '--world-bg-end':   '#1a2e1a',
    '--world-accent':   '#7ecf8e',
    '--node-border':    '#90ee90',
    '--node-glow':      'rgba(144,238,144,0.3)',
    '--map-filter':     'brightness(1.0) hue-rotate(10deg)',
  },
  anarchy: {
    '--world-bg-start': '#1a0a00',
    '--world-bg-end':   '#2e1a0a',
    '--world-accent':   '#ff6600',
    '--node-border':    '#ff4500',
    '--node-glow':      'rgba(255,69,0,0.4)',
    '--map-filter':     'contrast(1.2) saturate(1.4) brightness(0.9)',
  },
}

export function applyTheme(quadrant) {
  const theme = ALIGNMENT_THEMES[quadrant] ?? ALIGNMENT_THEMES.justice
  Object.entries(theme).forEach(([key, value]) => {
    document.documentElement.style.setProperty(key, value)
  })
}
