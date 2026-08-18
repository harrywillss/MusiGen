const base = ''  // proxied by Vite dev server

async function jsonFetch(path, opts = {}) {
  const res = await fetch(base + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    let msg = res.statusText
    try {
      const body = await res.json()
      msg = body.detail || body.message || JSON.stringify(body)
    } catch {}
    throw new Error(msg)
  }
  return res.json()
}

export const api = {
  status: () => jsonFetch('/api/system/status'),
  engines: () => jsonFetch('/api/system/engines'),
  presets: () => jsonFetch('/api/system/presets'),
  loadLLM: (model_path = null) =>
    jsonFetch('/api/system/llm/load', {
      method: 'POST',
      body: JSON.stringify({ model_path }),
    }),
  unloadLLM: () =>
    jsonFetch('/api/system/llm/unload', { method: 'POST' }),
  setMusicMode: (mode) =>
    jsonFetch('/api/system/music/mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    }),
  expandPrompt: (idea, style, temperature = 0.7) =>
    jsonFetch('/api/prompt/expand', {
      method: 'POST',
      body: JSON.stringify({ idea, style, temperature }),
    }),
  translate: (text) =>
    jsonFetch('/api/prompt/translate', {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
  writeLyrics: (theme, temperature = 0.9) =>
    jsonFetch('/api/prompt/lyrics', {
      method: 'POST',
      body: JSON.stringify({ theme, temperature }),
    }),
  critique: (prompt, lyrics) =>
    jsonFetch('/api/prompt/critique', {
      method: 'POST',
      body: JSON.stringify({ prompt, lyrics }),
    }),
  generate: (body) =>
    jsonFetch('/api/generate', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  listOutputs: () => jsonFetch('/api/outputs'),
  deleteOutput: (id) =>
    jsonFetch(`/api/outputs/${id}`, { method: 'DELETE' }),
  listModels: () => jsonFetch('/api/models'),
  audioUrl: (id) => `${base}/api/outputs/${id}/audio`,
  generateWS(body, handlers = {}) {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${window.location.host}/api/generate/ws`
    const ws = new WebSocket(url)
    ws.addEventListener('open', () => ws.send(JSON.stringify(body)))
    ws.addEventListener('message', (evt) => {
      const msg = JSON.parse(evt.data)
      if (msg.type === 'progress' && handlers.onProgress) handlers.onProgress(msg)
      if (msg.type === 'queued' && handlers.onQueued) handlers.onQueued(msg)
      if (msg.type === 'node' && handlers.onNode) handlers.onNode(msg)
      if (msg.type === 'done' && handlers.onDone) handlers.onDone(msg)
      if (msg.type === 'error' && handlers.onError) handlers.onError(msg)
    })
    ws.addEventListener('error', (e) => handlers.onError?.({ message: 'WebSocket error' }))
    ws.addEventListener('close', () => handlers.onClose?.())
    return ws
  },
}
