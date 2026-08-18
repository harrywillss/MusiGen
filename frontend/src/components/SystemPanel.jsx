import React, { useEffect, useState } from 'react'
import { api } from '../api'

export default function SystemPanel({ status, onRefresh, toast }) {
  const [busy, setBusy] = useState(false)
  const [models, setModels] = useState(null)

  useEffect(() => {
    api.listModels().then(setModels).catch(() => setModels(null))
  }, [status])

  if (!status) return null

  const engine = status.music_engine
  const llm = status.llm

  async function setMode(mode) {
    setBusy(true)
    try {
      await api.setMusicMode(mode)
      toast(`Music engine → ${mode}`)
      onRefresh()
    } catch (e) {
      toast(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  async function loadLLM(path = null) {
    setBusy(true)
    try {
      await api.loadLLM(path)
      toast('LLM loaded')
      onRefresh()
    } catch (e) {
      toast(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  async function unloadLLM() {
    setBusy(true)
    try {
      await api.unloadLLM()
      toast('LLM unloaded')
      onRefresh()
    } catch (e) {
      toast(e.message, 'err')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="pixel-panel pixel-panel--cyan stack">
      <h2>System</h2>

      <div>
        <div className="pixel-label">
          Music engine <span className="pixel-hint">{engine.name}</span>
        </div>
        <div className="row">
          {['auto', 'comfy', 'stub'].map((m) => (
            <button
              key={m}
              className={`pixel-btn ${status.config.music_engine_mode === m ? 'pixel-btn--primary' : ''}`}
              onClick={() => setMode(m)}
              disabled={busy}
            >
              {m}
            </button>
          ))}
        </div>
        <div className="pixel-hint" style={{ marginTop: 8 }}>
          ComfyUI: {engine.reachable ? '● reachable' : '○ not reachable'} — {engine.base_url}
          {engine.model_files && (
            <div style={{ marginTop: 4 }}>
              music: {engine.model_files.music_ckpt || '—'} · text_encoder:{' '}
              {engine.model_files.text_encoder || '—'} · vae:{' '}
              {engine.model_files.vae || '—'}
            </div>
          )}
        </div>
      </div>

      <div>
        <div className="pixel-label">
          LLM copilot <span className="pixel-hint">{llm.loaded ? 'loaded' : 'unloaded'}</span>
        </div>
        <div className="pixel-hint" style={{ marginBottom: 8 }}>
          {llm.model_path || 'no model'}
          {llm.error && (
            <div style={{ color: 'var(--danger)', marginTop: 4 }}>{llm.error}</div>
          )}
        </div>
        <div className="row">
          {llm.available_models?.length ? (
            llm.available_models.map((name) => (
              <button
                key={name}
                className="pixel-btn pixel-btn--tiny"
                onClick={() => loadLLM(`${status.models_dir}/llm/${name}`)}
                disabled={busy}
              >
                load {name}
              </button>
            ))
          ) : (
            <span className="pixel-hint">
              drop a .gguf into {status.models_dir}/llm/
            </span>
          )}
          {llm.loaded && (
            <button className="pixel-btn pixel-btn--ghost" onClick={unloadLLM} disabled={busy}>
              unload
            </button>
          )}
        </div>
      </div>

      {models && (
        <div>
          <div className="pixel-label">
            Model store <span className="pixel-hint">Models/</span>
          </div>
          <div className="pixel-hint">
            music: {models.music.files.length} file(s), llm: {models.llm.files.length} file(s)
          </div>
        </div>
      )}
    </div>
  )
}
