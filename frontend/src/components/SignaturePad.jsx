import React, { useRef } from 'react'

export default function SignaturePad({ onSave }) {
  const canvasRef = useRef(null)
  const isDrawing = useRef(false)

  const startDraw = (e) => {
    isDrawing.current = true
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const rect = canvas.getBoundingClientRect()
    ctx.beginPath()
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top)
  }

  const draw = (e) => {
    if (!isDrawing.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    const rect = canvas.getBoundingClientRect()
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top)
    ctx.strokeStyle = '#667eea'
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    ctx.stroke()
  }

  const endDraw = () => {
    isDrawing.current = false
  }

  const clear = () => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }

  const save = () => {
    const data = canvasRef.current.toDataURL()
    if (onSave) onSave(data)
  }

  return (
    <div>
      <canvas ref={canvasRef} width={400} height={150}
        className="border border-gray-600 rounded-xl bg-gray-900 cursor-crosshair w-full"
        onMouseDown={startDraw} onMouseMove={draw} onMouseUp={endDraw} onMouseLeave={endDraw} />
      <div className="flex gap-2 mt-2">
        <button onClick={clear} className="btn-secondary text-xs py-1 px-3">Clear</button>
        <button onClick={save} className="btn-primary text-xs py-1 px-3">Save Signature</button>
      </div>
    </div>
  )
}
