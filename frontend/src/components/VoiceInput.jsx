import React, { useState, useRef, useEffect } from 'react'
import { Mic, MicOff, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

// Map our language codes to Web Speech API BCP-47 locale tags
const SPEECH_LANG_MAP = {
  en: 'en-IN',
  hi: 'hi-IN',
  kn: 'kn-IN',
  ta: 'ta-IN',
  te: 'te-IN',
  mr: 'mr-IN',
  bn: 'bn-IN',
  gu: 'gu-IN',
  pa: 'pa-IN',
  ml: 'ml-IN',
}

const LANG_LABELS = {
  en: 'English', hi: 'Hindi', kn: 'Kannada', ta: 'Tamil',
  te: 'Telugu', mr: 'Marathi', bn: 'Bengali', gu: 'Gujarati',
  pa: 'Punjabi', ml: 'Malayalam',
}

/**
 * VoiceInput — Speech-to-Text microphone button
 * 
 * Props:
 *   language  — language code ('en', 'hi', 'kn', etc.)
 *   onResult  — callback(transcript) when speech is recognized
 *   disabled  — disable the button
 */
export default function VoiceInput({ language = 'en', onResult, disabled = false }) {
  const [listening, setListening] = useState(false)
  const [supported, setSupported] = useState(true)
  const [interim, setInterim] = useState('')
  const recognitionRef = useRef(null)

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setSupported(false)
      return
    }

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = SPEECH_LANG_MAP[language] || 'en-IN'

    recognition.onresult = (event) => {
      let finalTranscript = ''
      let interimTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }
      setInterim(interimTranscript)
      if (finalTranscript && onResult) {
        onResult(finalTranscript)
        setInterim('')
      }
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      if (event.error !== 'no-speech') {
        recognition._shouldListen = false // Stop restart loop on critical errors
        setListening(false)
      }
    }

    recognition.onend = () => {
      // Auto-restart if still in listening mode (handles Chrome auto-stop)
      if (recognitionRef.current?._shouldListen) {
        try { recognition.start() } catch (e) { /* already started */ }
      } else {
        setListening(false)
        setInterim('')
      }
    }

    recognitionRef.current = recognition

    return () => {
      recognition._shouldListen = false
      try { recognition.stop() } catch (e) { /* ignore */ }
    }
  }, [language])

  // Update language on existing recognition instance
  useEffect(() => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = SPEECH_LANG_MAP[language] || 'en-IN'
    }
  }, [language])

  const toggleListening = () => {
    if (!recognitionRef.current) return

    if (listening) {
      recognitionRef.current._shouldListen = false
      recognitionRef.current.stop()
      setListening(false)
      setInterim('')
    } else {
      recognitionRef.current._shouldListen = true
      recognitionRef.current.lang = SPEECH_LANG_MAP[language] || 'en-IN'
      try {
        recognitionRef.current.start()
        setListening(true)
      } catch (e) {
        console.error('Failed to start speech recognition:', e)
      }
    }
  }

  if (!supported) return null

  return (
    <div style={{ position: 'relative', display: 'inline-flex', alignItems: 'center' }}>
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={toggleListening}
        disabled={disabled}
        title={listening ? 'Stop listening' : `Speak in ${LANG_LABELS[language] || 'English'}`}
        style={{
          width: 44, height: 44, borderRadius: 14, border: 'none', cursor: disabled ? 'not-allowed' : 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: listening
            ? 'linear-gradient(135deg, #fc5c65, #eb3b5a)'
            : 'linear-gradient(135deg, #667eea, #764ba2)',
          color: 'white',
          boxShadow: listening
            ? '0 4px 15px rgba(252,92,101,0.4)'
            : '0 4px 15px rgba(102,126,234,0.3)',
          opacity: disabled ? 0.4 : 1,
          transition: 'all 0.3s',
        }}
      >
        {listening ? <MicOff size={18} /> : <Mic size={18} />}
      </motion.button>

      {/* Pulsing ring animation when listening */}
      <AnimatePresence>
        {listening && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: [1, 1.4, 1], opacity: [0.5, 0, 0.5] }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 1.5, repeat: Infinity }}
            style={{
              position: 'absolute', top: -4, left: -4, right: -4, bottom: -4,
              borderRadius: 18, border: '2px solid rgba(252,92,101,0.4)',
              pointerEvents: 'none',
            }}
          />
        )}
      </AnimatePresence>

      {/* Interim text tooltip */}
      <AnimatePresence>
        {interim && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            style={{
              position: 'absolute', bottom: '110%', left: '50%', transform: 'translateX(-50%)',
              background: 'rgba(15,23,42,0.9)', color: 'white', padding: '6px 12px',
              borderRadius: 8, fontSize: '0.75rem', whiteSpace: 'nowrap', maxWidth: 280,
              overflow: 'hidden', textOverflow: 'ellipsis', pointerEvents: 'none',
              boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
            }}
          >
            🎤 {interim}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
