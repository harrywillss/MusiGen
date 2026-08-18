import React, { useMemo } from 'react'

/* An SVG pixel-art city skyline drawn from a seedable "building" grid.
   Big blocky buildings with lit windows against the sunset gradient. */

function randInt(seed, i) {
  const x = Math.sin(seed + i * 9973) * 43758.5453
  return Math.floor((x - Math.floor(x)) * 1_000_000)
}

function generateBuildings(count, seed) {
  const arr = []
  let x = 0
  for (let i = 0; i < count; i += 1) {
    const w = 12 + (randInt(seed, i) % 28)
    const h = 30 + (randInt(seed, i + 101) % 180)
    arr.push({ x, w, h })
    x += w + 4
  }
  return { buildings: arr, totalWidth: x }
}

export default function PixelSkyline() {
  const seed = 42
  const { buildings, totalWidth } = useMemo(() => generateBuildings(48, seed), [])

  const windows = []
  buildings.forEach((b, bi) => {
    const cols = Math.max(1, Math.floor((b.w - 4) / 4))
    const rows = Math.max(1, Math.floor((b.h - 8) / 6))
    for (let r = 0; r < rows; r += 1) {
      for (let c = 0; c < cols; c += 1) {
        const key = randInt(seed, bi * 977 + r * 31 + c)
        if (key % 5 !== 0) continue
        windows.push({
          x: b.x + 2 + c * 4,
          y: 240 - b.h + 4 + r * 6,
          on: key % 2 === 0,
        })
      }
    }
  })

  return (
    <div className="skyline-wrap" aria-hidden>
      {[...Array(80)].map((_, i) => (
        <span
          key={i}
          className="pixel-star"
          style={{
            top: `${(randInt(999, i) % 60)}%`,
            left: `${(randInt(998, i) % 100)}%`,
            animationDelay: `${(randInt(997, i) % 3000) / 1000}s`,
          }}
        />
      ))}
      <div className="skyline-sun" />
      <div className="skyline-grid" />
      <svg
        className="skyline"
        viewBox={`0 0 ${totalWidth} 260`}
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="build" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="#12042b" />
            <stop offset="100%" stopColor="#2b063d" />
          </linearGradient>
        </defs>
        {buildings.map((b, i) => (
          <g key={i}>
            <rect x={b.x} y={240 - b.h} width={b.w} height={b.h} fill="url(#build)" />
            {/* Neon top edge */}
            <rect x={b.x} y={240 - b.h} width={b.w} height={2} fill="#ff2ec4" />
            {i % 5 === 0 && (
              <rect
                x={b.x + Math.floor(b.w / 2) - 1}
                y={240 - b.h - 12}
                width={2}
                height={12}
                fill="#29ffe7"
              />
            )}
          </g>
        ))}
        {windows.map((w, i) => (
          <rect
            key={i}
            x={w.x}
            y={w.y}
            width={2}
            height={3}
            fill={w.on ? '#ffe27a' : '#3c1360'}
          />
        ))}
      </svg>
    </div>
  )
}
