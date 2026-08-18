import React from 'react'
import { api } from '../api'

function fmtDate(ts) {
  try {
    return new Date(ts * 1000).toLocaleString()
  } catch {
    return ''
  }
}

export default function Gallery({ outputs, onDelete, onReuse, toast }) {
  if (!outputs) return null
  if (outputs.length === 0) {
    return (
      <div className="pixel-panel pixel-panel--lime">
        <h2>Gallery</h2>
        <div className="pixel-hint">
          Nothing generated yet. Hit <b>GENERATE</b> to fill this up.
        </div>
      </div>
    )
  }
  return (
    <div className="pixel-panel pixel-panel--lime stack">
      <h2>Gallery</h2>
      <div className="gallery">
        {outputs.map((o) => (
          <div
            key={o.id}
            className={`card card--${o.status === 'done' ? 'done' : o.status === 'failed' ? 'fail' : 'run'}`}
          >
            <div className="card__title">
              {o.id} · {o.engine}
            </div>
            <div className="card__prompt">{o.prompt}</div>
            <div className="card__meta">
              <span>{fmtDate(o.created_at)}</span>
              <span>
                {o.params?.duration}s · {o.params?.steps} steps · cfg {o.params?.cfg}
              </span>
            </div>
            {o.status === 'done' && o.audio_url && (
              <audio controls src={api.audioUrl(o.id)} preload="none" />
            )}
            {o.status === 'failed' && (
              <div className="pixel-hint" style={{ color: 'var(--danger)' }}>
                {o.error}
              </div>
            )}
            <div className="card__actions">
              {o.status === 'done' && (
                <a
                  className="pixel-btn pixel-btn--tiny pixel-btn--cyan"
                  href={api.audioUrl(o.id)}
                  download={`${o.id}.wav`}
                >
                  ⬇ wav
                </a>
              )}
              <button
                className="pixel-btn pixel-btn--tiny pixel-btn--ghost"
                onClick={() => onReuse(o)}
              >
                ↻ reuse
              </button>
              <button
                className="pixel-btn pixel-btn--tiny pixel-btn--danger"
                onClick={() => {
                  if (confirm('delete this generation?')) onDelete(o.id)
                }}
              >
                ✕ delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
