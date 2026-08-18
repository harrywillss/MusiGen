import React, { useCallback, useEffect, useRef, useState } from 'react'
import { api } from './api'
import PixelSkyline from './components/PixelSkyline'
import StatusStrip from './components/StatusStrip'
import Toasts from './components/Toasts'
import SystemPanel from './components/SystemPanel'
import PromptStudio from './components/PromptStudio'
import Gallery from './components/Gallery'

export default function App() {
  const [status, setStatus] = useState(null)
  const [outputs, setOutputs] = useState([])
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(null)
  const [toasts, setToasts] = useState([])
  const [reuseSeed, setReuseSeed] = useState(null)
  const wsRef = useRef(null)

  const toast = useCallback((message, kind = 'ok') => {
    const id = Math.random().toString(36).slice(2)
    setToasts((t) => [...t, { id, message, kind }])
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4200)
  }, [])

  const refreshStatus = useCallback(async () => {
    try {
      const s = await api.status()
      setStatus(s)
    } catch (e) {
      toast(`status: ${e.message}`, 'err')
    }
  }, [toast])

  const refreshOutputs = useCallback(async () => {
    try {
      const r = await api.listOutputs()
      setOutputs(r.outputs)
    } catch (e) {
      // silent — the panel will just be empty
    }
  }, [])

  useEffect(() => {
    refreshStatus()
    refreshOutputs()
    const iv = setInterval(refreshStatus, 10_000)
    return () => clearInterval(iv)
  }, [refreshStatus, refreshOutputs])

  const onGenerate = useCallback(
    (body) => {
      setBusy(true)
      setProgress({ value: 0, message: 'queued', line: 'submitting…' })
      let last = null
      const ws = api.generateWS(body, {
        onQueued: (m) => {
          setProgress({ value: 0.02, message: `queued ${m.record.id}`, line: `queued ${m.record.id}` })
          refreshOutputs()
        },
        onProgress: (m) => {
          const line = m.message || `progress ${(m.value * 100).toFixed(0)}%`
          setProgress({ value: m.value, message: line, line })
        },
        onNode: (m) => {
          setProgress((p) => ({ ...(p || {}), line: `node ${m.node ?? '·'}` }))
        },
        onDone: (m) => {
          last = m.record
          setProgress({ value: 1, message: '✔ done', line: `done ${m.record.id}` })
          toast('generation complete')
          refreshOutputs()
        },
        onError: (m) => {
          toast(m.message, 'err')
          setProgress({ value: 0, message: `✕ ${m.message}`, line: m.message })
        },
        onClose: () => {
          setBusy(false)
          setTimeout(() => setProgress(null), 4000)
          wsRef.current = null
        },
      })
      wsRef.current = ws
    },
    [refreshOutputs, toast]
  )

  const onCancel = useCallback(() => {
    if (wsRef.current) {
      try { wsRef.current.close() } catch {}
      wsRef.current = null
    }
    setBusy(false)
    setProgress(null)
    toast('cancelled')
  }, [toast])

  const onDelete = useCallback(
    async (id) => {
      try {
        await api.deleteOutput(id)
        toast('deleted')
        refreshOutputs()
      } catch (e) {
        toast(e.message, 'err')
      }
    },
    [refreshOutputs, toast]
  )

  const onReuse = useCallback((rec) => {
    setReuseSeed({
      prompt: rec.prompt,
      lyrics: rec.lyrics,
      params: rec.params,
      _ts: Date.now(),
    })
    toast(`loaded ${rec.id} into studio`)
  }, [toast])

  return (
    <>
      <PixelSkyline />
      <div className="app">
        <header className="app__header">
          <div className="brand">
            <div className="brand__glyph" />
            <div>
              <div className="brand__name">MusiGen</div>
              <div className="brand__tagline">
                pixel-art studio · text → music · llm copilot
              </div>
            </div>
          </div>
          <StatusStrip status={status} />
        </header>

        <div className="grid">
          <PromptStudio
            key={reuseSeed?._ts || 'studio'}
            status={status}
            busy={busy}
            progress={progress}
            onGenerate={onGenerate}
            onCancel={onCancel}
            toast={toast}
            seed={reuseSeed}
          />

          <div className="stack">
            <SystemPanel
              status={status}
              onRefresh={refreshStatus}
              toast={toast}
            />
            <Gallery
              outputs={outputs}
              onDelete={onDelete}
              onReuse={onReuse}
              toast={toast}
            />
          </div>
        </div>

        <div className="footer">MusiGen v0.1 · press start to make music</div>
      </div>
      <Toasts toasts={toasts} onDismiss={(id) => setToasts((t) => t.filter((x) => x.id !== id))} />
    </>
  )
}
