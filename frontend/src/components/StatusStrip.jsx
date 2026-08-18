import React from 'react'

function dot(state) {
  if (state === 'ok') return <span className="pixel-dot" />
  if (state === 'warn') return <span className="pixel-dot pixel-dot--warn" />
  if (state === 'err') return <span className="pixel-dot pixel-dot--danger" />
  return <span className="pixel-dot pixel-dot--off" />
}

export default function StatusStrip({ status }) {
  if (!status) {
    return (
      <div className="status-strip">
        {dot('off')} connecting…
      </div>
    )
  }
  const engine = status.music_engine
  const llm = status.llm
  const engineState = engine.available ? 'ok' : engine.name === 'stub' ? 'warn' : 'err'
  const llmState = llm.loaded ? 'ok' : llm.available_models?.length ? 'warn' : 'err'
  return (
    <div className="status-strip">
      {dot(engineState)}
      <span>engine: {engine.name}</span>
      <span style={{ opacity: 0.5 }}>|</span>
      {dot(llmState)}
      <span>llm: {llm.loaded ? (llm.model_path?.split('/').pop() || 'loaded') : 'off'}</span>
    </div>
  )
}
