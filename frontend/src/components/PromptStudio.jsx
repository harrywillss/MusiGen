import React, { useEffect, useMemo, useState } from 'react'
import { api } from '../api'

const SAMPLERS = ['euler', 'euler_ancestral', 'dpmpp_2m', 'dpmpp_2m_sde', 'ddim', 'lcm']
const SCHEDULERS = ['normal', 'karras', 'exponential', 'sgm_uniform', 'simple']

export default function PromptStudio({
  status,
  onGenerate,
  busy,
  progress,
  onCancel,
  toast,
  seed: reuseSeed,
}) {
  const [idea, setIdea] = useState('')
  const [prompt, setPrompt] = useState(reuseSeed?.prompt || '')
  const [lyrics, setLyrics] = useState(reuseSeed?.lyrics || '')
  const [style, setStyle] = useState('')
  const [duration, setDuration] = useState(reuseSeed?.params?.duration ?? 30)
  const [steps, setSteps] = useState(reuseSeed?.params?.steps ?? 30)
  const [cfg, setCfg] = useState(reuseSeed?.params?.cfg ?? 1.7)
  const [seed, setSeed] = useState(reuseSeed?.params?.seed != null ? String(reuseSeed.params.seed) : '')
  const [sampler, setSampler] = useState(reuseSeed?.params?.sampler || 'euler')
  const [scheduler, setScheduler] = useState(reuseSeed?.params?.scheduler || 'simple')
  const [presets, setPresets] = useState({})
  const [expBusy, setExpBusy] = useState(false)
  const [lyrBusy, setLyrBusy] = useState(false)
  const [critique, setCritique] = useState('')
  const [logLines, setLogLines] = useState([])

  useEffect(() => {
    api.presets().then((r) => setPresets(r.presets || {})).catch(() => {})
  }, [])

  useEffect(() => {
    if (progress?.line) {
      setLogLines((l) => [...l.slice(-40), progress.line])
    }
  }, [progress])

  const styleKeys = useMemo(() => Object.keys(presets), [presets])

  async function expandPrompt() {
    if (!idea && !prompt) {
      toast('type an idea first', 'err')
      return
    }
    setExpBusy(true)
    try {
      const source = idea || prompt
      const r = await api.expandPrompt(source, style || null)
      setPrompt(r.prompt)
      toast('prompt expanded')
    } catch (e) {
      toast(e.message, 'err')
    } finally {
      setExpBusy(false)
    }
  }

  async function translate() {
    if (!idea) {
      toast('type an idea to translate', 'err')
      return
    }
    setExpBusy(true)
    try {
      const r = await api.translate(idea)
      setPrompt(r.prompt)
      toast('translated')
    } catch (e) {
      toast(e.message, 'err')
    } finally {
      setExpBusy(false)
    }
  }

  async function writeLyrics() {
    const theme = idea || prompt || 'a song about the night sky'
    setLyrBusy(true)
    try {
      const r = await api.writeLyrics(theme)
      setLyrics(r.lyrics)
      toast('lyrics written')
    } catch (e) {
      toast(e.message, 'err')
    } finally {
      setLyrBusy(false)
    }
  }

  async function critiqueNow() {
    if (!prompt) {
      toast('need a prompt to critique', 'err')
      return
    }
    setExpBusy(true)
    try {
      const r = await api.critique(prompt, lyrics)
      setCritique(r.critique)
    } catch (e) {
      toast(e.message, 'err')
    } finally {
      setExpBusy(false)
    }
  }

  function applyPreset(key) {
    setStyle(key)
    setPrompt(presets[key])
    toast(`preset: ${key}`)
  }

  function randomiseSeed() {
    setSeed(String(Math.floor(Math.random() * 2 ** 31)))
  }

  function submit() {
    if (!prompt.trim()) {
      toast('prompt is empty', 'err')
      return
    }
    onGenerate({
      prompt: prompt.trim(),
      lyrics: lyrics.trim(),
      duration: Number(duration),
      steps: Number(steps),
      cfg: Number(cfg),
      seed: seed === '' ? null : Number(seed),
      sampler,
      scheduler,
      expanded_prompt: prompt.trim(),
      llm_notes: critique || null,
    })
    setLogLines([])
  }

  const llmAvailable = status?.llm?.loaded

  return (
    <div className="pixel-panel stack">
      <h2>Studio</h2>

      <div>
        <div className="pixel-label">
          Idea <span className="pixel-hint">short brief — any language</span>
        </div>
        <textarea
          className="pixel-textarea"
          rows={2}
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="chill boom-bap for late night coding, dusty vinyl vibe"
        />
        <div className="row" style={{ marginTop: 8 }}>
          <button
            className="pixel-btn pixel-btn--cyan"
            onClick={expandPrompt}
            disabled={expBusy || !llmAvailable}
            title={!llmAvailable ? 'Load an LLM to use the copilot' : ''}
          >
            {expBusy ? <span className="spinner" /> : '✦'} expand → prompt
          </button>
          <button
            className="pixel-btn pixel-btn--ghost"
            onClick={translate}
            disabled={expBusy || !llmAvailable}
          >
            🌐 translate → prompt
          </button>
          <button
            className="pixel-btn pixel-btn--ghost"
            onClick={writeLyrics}
            disabled={lyrBusy || !llmAvailable}
          >
            {lyrBusy ? <span className="spinner" /> : '📝'} write lyrics
          </button>
        </div>
      </div>

      <div>
        <div className="pixel-label">
          Style presets <span className="pixel-hint">click to seed the prompt</span>
        </div>
        <div>
          {styleKeys.map((k) => (
            <span
              key={k}
              className={`pixel-tag ${style === k ? 'pixel-tag--pink' : ''}`}
              onClick={() => applyPreset(k)}
            >
              {k}
            </span>
          ))}
        </div>
      </div>

      <div>
        <div className="pixel-label">
          Prompt <span className="pixel-hint">description sent to the music model</span>
        </div>
        <textarea
          className="pixel-textarea"
          rows={5}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Warm dusty lo-fi hip-hop beat around 82 BPM, mellow Rhodes chords..."
        />
        <div className="row" style={{ marginTop: 8 }}>
          <button
            className="pixel-btn pixel-btn--ghost"
            onClick={critiqueNow}
            disabled={expBusy || !llmAvailable}
          >
            🔍 critique
          </button>
          {critique && (
            <div className="pixel-hint" style={{ flex: 1 }}>
              {critique}
            </div>
          )}
        </div>
      </div>

      <div>
        <div className="pixel-label">
          Lyrics <span className="pixel-hint">optional — leave empty for instrumental</span>
        </div>
        <textarea
          className="pixel-textarea"
          rows={4}
          value={lyrics}
          onChange={(e) => setLyrics(e.target.value)}
          placeholder="[Verse]&#10;Neon rain on empty streets..."
        />
      </div>

      <div>
        <div className="pixel-label">Parameters</div>
        <div className="param-grid">
          <label>
            <div className="pixel-label">Duration (s)</div>
            <input
              className="pixel-input"
              type="number"
              min="4"
              max="240"
              step="1"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
          </label>
          <label>
            <div className="pixel-label">Steps</div>
            <input
              className="pixel-input"
              type="number"
              min="1"
              max="200"
              value={steps}
              onChange={(e) => setSteps(e.target.value)}
            />
          </label>
          <label>
            <div className="pixel-label">CFG</div>
            <input
              className="pixel-input"
              type="number"
              step="0.1"
              min="0"
              max="20"
              value={cfg}
              onChange={(e) => setCfg(e.target.value)}
            />
          </label>
          <label>
            <div className="pixel-label">Seed</div>
            <div className="row">
              <input
                className="pixel-input"
                type="number"
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                placeholder="random"
              />
              <button
                className="pixel-btn pixel-btn--tiny pixel-btn--ghost"
                onClick={randomiseSeed}
              >
                🎲
              </button>
            </div>
          </label>
          <label>
            <div className="pixel-label">Sampler</div>
            <select
              className="pixel-select"
              value={sampler}
              onChange={(e) => setSampler(e.target.value)}
            >
              {SAMPLERS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <label>
            <div className="pixel-label">Scheduler</div>
            <select
              className="pixel-select"
              value={scheduler}
              onChange={(e) => setScheduler(e.target.value)}
            >
              {SCHEDULERS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      <div className="row row--between">
        <button
          className="pixel-btn pixel-btn--primary"
          onClick={submit}
          disabled={busy}
          style={{ minWidth: 220 }}
        >
          {busy ? '▶ generating…' : '▶ GENERATE'}
        </button>
        {busy && (
          <button className="pixel-btn pixel-btn--danger" onClick={onCancel}>
            ⏹ cancel
          </button>
        )}
      </div>

      {progress && (
        <div>
          <div className="progress">
            <div
              className="progress__bar"
              style={{ width: `${Math.min(100, (progress.value || 0) * 100)}%` }}
            />
          </div>
          <div className="pixel-hint" style={{ marginTop: 6 }}>
            {progress.message || 'working...'}
          </div>
        </div>
      )}

      {logLines.length > 0 && (
        <div>
          <div className="pixel-label">Log</div>
          <div className="console">
            {logLines.map((l, i) => (
              <div key={i}>▸ {l}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
