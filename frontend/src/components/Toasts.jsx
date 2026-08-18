import React from 'react'

export default function Toasts({ toasts, onDismiss }) {
  return (
    <div className="toast-stack">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`toast ${t.kind === 'err' ? 'toast--err' : ''}`}
          onClick={() => onDismiss(t.id)}
          role="button"
        >
          {t.message}
        </div>
      ))}
    </div>
  )
}
