import { useState, useEffect, useRef, useCallback } from 'react'

export default function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState(null)
  const wsRef = useRef(null)

  const connect = useCallback(() => {
    if (wsRef.current) wsRef.current.close()

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => setIsConnected(true)
    ws.onclose = () => setIsConnected(false)
    ws.onerror = () => setIsConnected(false)
    ws.onmessage = (event) => {
      try {
        setLastMessage(JSON.parse(event.data))
      } catch {
        setLastMessage(event.data)
      }
    }
  }, [url])

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }, [])

  const disconnect = useCallback(() => {
    if (wsRef.current) wsRef.current.close()
  }, [])

  useEffect(() => {
    return () => { if (wsRef.current) wsRef.current.close() }
  }, [])

  return { isConnected, lastMessage, connect, send, disconnect }
}
