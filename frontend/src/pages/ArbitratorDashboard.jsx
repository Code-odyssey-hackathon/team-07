import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppContext } from '../App'
import { motion, AnimatePresence } from 'framer-motion'
import { Gavel, LogIn, User, Shield, CheckCircle, Clock, AlertTriangle, Send, MessageSquare, Bot, Users, XCircle, Pen, X } from 'lucide-react'

export default function ArbitratorDashboard() {
  const { API_URL } = useAppContext()
  const navigate = useNavigate()
  const [arbToken, setArbToken] = useState(localStorage.getItem('arb_token') || '')
  const [arbInfo, setArbInfo] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [registerForm, setRegisterForm] = useState({ name: '', email: '', password: '', bar_registration: '' })
  const [isRegister, setIsRegister] = useState(false)
  const [error, setError] = useState('')
  const [activeSession, setActiveSession] = useState(null)  // dispute_id of active session
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [connected, setConnected] = useState(false)
  const wsRef = useRef(null)
  const chatEndRef = useRef(null)

  useEffect(() => { if (arbToken) loadDashboard() }, [arbToken])
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const loadDashboard = async () => {
    try {
      const res = await fetch(`${API_URL}/arbitrator/dashboard?token=${arbToken}`)
      if (res.ok) {
        const data = await res.json()
        setDashboard(data)
        setArbInfo(data.arbitrator)
      } else { setArbToken(''); localStorage.removeItem('arb_token') }
    } catch { setError('Failed to load dashboard') }
  }

  const handleLogin = async (e) => {
    e.preventDefault(); setError('')
    try {
      const res = await fetch(`${API_URL}/arbitrator/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm),
      })
      if (res.ok) {
        const data = await res.json()
        setArbToken(data.token); localStorage.setItem('arb_token', data.token)
        setArbInfo({ id: data.arbitrator_id, name: data.name, email: data.email })
      } else { setError('Invalid credentials') }
    } catch { setError('Login failed') }
  }

  const handleRegister = async (e) => {
    e.preventDefault(); setError('')
    try {
      const res = await fetch(`${API_URL}/arbitrator/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerForm),
      })
      if (res.ok) {
        const data = await res.json()
        setArbToken(data.token); localStorage.setItem('arb_token', data.token)
        setArbInfo({ id: data.arbitrator_id, name: data.name, email: data.email })
      } else {
        const err = await res.json()
        setError(err.detail || 'Registration failed')
      }
    } catch { setError('Registration failed') }
  }

  const acceptCase = async (disputeId) => {
    try {
      const res = await fetch(`${API_URL}/arbitrator/${disputeId}/accept?token=${arbToken}`, { method: 'POST' })
      if (res.ok) { loadDashboard(); joinSession(disputeId) }
    } catch { setError('Failed to accept case') }
  }

  const joinSession = (disputeId) => {
    setActiveSession(disputeId)
    setMessages([])

    const ws = new WebSocket(`ws://localhost:8000/ws/arbitrator/${disputeId}?token=${arbToken}`)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'history') setMessages(data.messages || [])
      else if (data.type === 'message') setMessages(p => [...p, data])
      else if (data.type === 'system') setMessages(p => [...p, { role: 'system', content: data.content }])
      else if (data.type === 'signal') {
        if (data.signal === 'AGREEMENT_REACHED') setMessages(p => [...p, { role: 'system', content: '✅ Agreement reached!' }])
      }
    }
  }

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current) return
    wsRef.current.send(JSON.stringify({ message: input.trim() }))
    setInput('')
  }

  const [arbConfirmStep, setArbConfirmStep] = useState(0)
  const [arbSigned, setArbSigned] = useState(false)

  const declareAgreement = () => {
    if (!wsRef.current) return
    wsRef.current.send(JSON.stringify({ signal: 'AGREEMENT_REACHED', option: 'arbitrator_decision' }))
  }

  const initiateArbSign = () => setArbConfirmStep(1)

  const signAsArbitrator = async () => {
    try {
      const res = await fetch(`${API_URL}/agreement/${activeSession}/arbitrator-sign?token=${arbToken}`, { method: 'POST' })
      if (res.ok) { setArbSigned(true); setArbConfirmStep(0) }
    } catch { console.error('Sign failed') }
  }

  const leaveSession = () => {
    if (wsRef.current) wsRef.current.close()
    setActiveSession(null); setMessages([]); setConnected(false)
    setArbSigned(false); setArbConfirmStep(0)
    loadDashboard()
  }

  const logout = () => {
    setArbToken(''); setArbInfo(null); setDashboard(null)
    localStorage.removeItem('arb_token')
    if (wsRef.current) wsRef.current.close()
  }

  // ─── Login / Register ─────────────────────────────
  if (!arbToken) return (
    <div style={{ maxWidth: 460, margin: '0 auto', padding: '80px 24px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ width: 64, height: 64, borderRadius: 20, background: 'linear-gradient(135deg, #ed8936, #dd6b20)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px',
                        boxShadow: '0 12px 30px rgba(237,137,54,0.3)' }}>
            <Gavel size={28} color="white" />
          </div>
          <h1 style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.8rem', marginBottom: 4 }}>
            Arbitrator Portal
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Certified arbitrators under Arbitration Act, 1996</p>
        </div>

        <div className="glass-static" style={{ padding: 32, borderRadius: 20 }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
            <button onClick={() => setIsRegister(false)} style={{
              flex: 1, padding: '10px', borderRadius: 10, border: 'none', cursor: 'pointer', fontWeight: 600,
              background: !isRegister ? 'rgba(237,137,54,0.15)' : 'transparent',
              color: !isRegister ? '#ed8936' : '#64748b', fontSize: '0.9rem'
            }}>Login</button>
            <button onClick={() => setIsRegister(true)} style={{
              flex: 1, padding: '10px', borderRadius: 10, border: 'none', cursor: 'pointer', fontWeight: 600,
              background: isRegister ? 'rgba(237,137,54,0.15)' : 'transparent',
              color: isRegister ? '#ed8936' : '#64748b', fontSize: '0.9rem'
            }}>Register</button>
          </div>

          {error && <div style={{ padding: '10px 14px', borderRadius: 10, background: 'rgba(252,92,101,0.1)',
                                   border: '1px solid rgba(252,92,101,0.2)', color: '#fc5c65', fontSize: '0.85rem',
                                   marginBottom: 16 }}>{error}</div>}

          {isRegister ? (
            <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <input className="input-field" placeholder="Full Name" value={registerForm.name}
                onChange={e => setRegisterForm({ ...registerForm, name: e.target.value })} required />
              <input className="input-field" placeholder="Email" type="email" value={registerForm.email}
                onChange={e => setRegisterForm({ ...registerForm, email: e.target.value })} required />
              <input className="input-field" placeholder="Password" type="password" value={registerForm.password}
                onChange={e => setRegisterForm({ ...registerForm, password: e.target.value })} required />
              <input className="input-field" placeholder="Bar Registration No. (optional)" value={registerForm.bar_registration}
                onChange={e => setRegisterForm({ ...registerForm, bar_registration: e.target.value })} />
              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                className="btn-primary" type="submit" style={{ padding: '14px', fontSize: '0.95rem', marginTop: 8,
                  background: 'linear-gradient(135deg, #ed8936, #dd6b20)' }}>
                Register as Arbitrator
              </motion.button>
            </form>
          ) : (
            <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <input className="input-field" placeholder="Email" type="email" value={loginForm.email}
                onChange={e => setLoginForm({ ...loginForm, email: e.target.value })} required />
              <input className="input-field" placeholder="Password" type="password" value={loginForm.password}
                onChange={e => setLoginForm({ ...loginForm, password: e.target.value })} required />
              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                className="btn-primary" type="submit" style={{ padding: '14px', fontSize: '0.95rem', marginTop: 8,
                  background: 'linear-gradient(135deg, #ed8936, #dd6b20)' }}>
                <LogIn size={16} /> Login
              </motion.button>
            </form>
          )}
        </div>
      </motion.div>
    </div>
  )

  // ─── Active Session (Chat) ────────────────────────
  if (activeSession) return (
    <div style={{ maxWidth: 820, margin: '0 auto', padding: '24px 16px' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        className="glass-static" style={{ padding: '14px 24px', marginBottom: 12, borderRadius: 16,
          display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: 'linear-gradient(135deg, #ed8936, #dd6b20)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Gavel size={18} color="white" />
          </div>
          <div>
            <h2 style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '1rem' }}>Arbitration Session</h2>
            <p style={{ fontSize: '0.75rem', color: '#64748b' }}>You are the presiding arbitrator</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: connected ? '#48bb78' : '#fc5c65' }} />
          <span style={{ fontSize: '0.8rem', color: connected ? '#48bb78' : '#fc5c65' }}>{connected ? 'Live' : 'Disconnected'}</span>
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={declareAgreement} style={{ padding: '8px 16px', borderRadius: 10, fontSize: '0.8rem', fontWeight: 700,
              background: 'rgba(72,187,120,0.15)', border: '1px solid rgba(72,187,120,0.3)', color: '#48bb78', cursor: 'pointer' }}>
            <CheckCircle size={14} /> Declare Agreement
          </motion.button>
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={leaveSession} style={{ padding: '8px 16px', borderRadius: 10, fontSize: '0.8rem', fontWeight: 700,
              background: 'rgba(252,92,101,0.1)', border: '1px solid rgba(252,92,101,0.25)', color: '#fc5c65', cursor: 'pointer' }}>
            Leave
          </motion.button>
        </div>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="glass-static" style={{ borderRadius: 20, display: 'flex', flexDirection: 'column', height: '70vh', overflow: 'hidden' }}>
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px 20px 12px' }}>
          {messages.map((msg, i) => {
            const isArb = msg.role === 'arbitrator'
            const isSystem = msg.role === 'system'
            const isMediator = msg.role === 'mediator'
            return (
              <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                style={{ marginBottom: 10, textAlign: isSystem ? 'center' : isArb ? 'right' : 'left' }}>
                {isSystem ? (
                  <span style={{ fontSize: '0.78rem', color: '#94a3b8', fontStyle: 'italic' }}>{msg.content}</span>
                ) : (
                  <div style={{ display: 'inline-block', maxWidth: '75%', padding: '12px 16px', borderRadius: 14,
                    background: isArb ? 'rgba(237,137,54,0.15)' : isMediator ? 'rgba(118,75,162,0.12)' : 'rgba(102,126,234,0.1)',
                    border: `1px solid ${isArb ? 'rgba(237,137,54,0.25)' : isMediator ? 'rgba(118,75,162,0.2)' : 'rgba(102,126,234,0.2)'}` }}>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, marginBottom: 4,
                      color: isArb ? '#ed8936' : isMediator ? '#a78bfa' : '#667eea' }}>
                      {msg.party_name || msg.role}
                    </div>
                    <div style={{ fontSize: '0.88rem', color: '#334155', lineHeight: 1.5 }}>{msg.content}</div>
                  </div>
                )}
              </motion.div>
            )
          })}
          <div ref={chatEndRef} />
        </div>

        <div style={{ padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <input className="input-field" placeholder="Type your message as arbitrator..." value={input}
              onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()}
              style={{ borderRadius: 14 }} />
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={sendMessage} className="btn-primary" disabled={!input.trim()}
              style={{ padding: '12px 18px', borderRadius: 14, background: 'linear-gradient(135deg, #ed8936, #dd6b20)' }}>
              <Send size={18} />
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Sign as Arbitrator */}
      {!arbSigned && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          style={{ marginTop: 12, textAlign: 'center' }}>
          <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
            onClick={initiateArbSign} className="btn-primary"
            style={{ padding: '14px 32px', borderRadius: 14, fontSize: '0.95rem',
              background: 'linear-gradient(135deg, #667eea, #764ba2)',
              boxShadow: '0 6px 20px rgba(102,126,234,0.3)' }}>
            <Pen size={16} /> Sign Agreement as Arbitrator
          </motion.button>
        </motion.div>
      )}
      {arbSigned && (
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
          style={{ marginTop: 12, padding: '14px 20px', borderRadius: 14, textAlign: 'center',
            background: 'rgba(72,187,120,0.08)', border: '1px solid rgba(72,187,120,0.25)' }}>
          <CheckCircle size={18} style={{ color: '#48bb78', verticalAlign: 'middle', marginRight: 8 }} />
          <span style={{ fontWeight: 700, color: '#68d391', fontSize: '0.9rem' }}>You have signed this agreement ✓</span>
        </motion.div>
      )}

      {/* Arbitrator Double Confirmation Modal */}
      <AnimatePresence>
        {arbConfirmStep > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(6px)',
                     display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}
            onClick={() => setArbConfirmStep(0)}>
            <motion.div initial={{ scale: 0.85, y: 30 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.85, y: 30 }}
              onClick={e => e.stopPropagation()}
              className="glass-static" style={{ maxWidth: 480, width: '90%', padding: 32, borderRadius: 24, position: 'relative' }}>

              <button onClick={() => setArbConfirmStep(0)} style={{ position: 'absolute', top: 16, right: 16,
                background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                <X size={20} />
              </button>

              {arbConfirmStep === 1 ? (
                <>
                  <div style={{ textAlign: 'center', marginBottom: 24 }}>
                    <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(237,137,54,0.1)',
                                  border: '2px solid rgba(237,137,54,0.3)', display: 'flex', alignItems: 'center',
                                  justifyContent: 'center', margin: '0 auto 16px' }}>
                      <Gavel size={28} style={{ color: '#ed8936' }} />
                    </div>
                    <h3 style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.3rem', marginBottom: 8 }}>
                      Arbitrator Signature
                    </h3>
                    <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: 1.6 }}>
                      As the presiding arbitrator, your digital signature will make this award
                      <strong style={{ color: '#f6ad55' }}> legally enforceable</strong> under the
                      Arbitration & Conciliation Act, 1996.
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={() => setArbConfirmStep(0)}
                      style={{ flex: 1, padding: '14px', borderRadius: 14, fontSize: '0.9rem', fontWeight: 600,
                        background: 'rgba(0,0,0,0.05)', border: '1px solid var(--border)', color: '#64748b', cursor: 'pointer' }}>
                      Cancel
                    </motion.button>
                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={() => setArbConfirmStep(2)}
                      className="btn-primary" style={{ flex: 1, padding: '14px', borderRadius: 14, fontSize: '0.9rem',
                        background: 'linear-gradient(135deg, #ed8936, #dd6b20)' }}>
                      I Confirm, Proceed →
                    </motion.button>
                  </div>
                </>
              ) : (
                <>
                  <div style={{ textAlign: 'center', marginBottom: 24 }}>
                    <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(252,92,101,0.1)',
                                  border: '2px solid rgba(252,92,101,0.3)', display: 'flex', alignItems: 'center',
                                  justifyContent: 'center', margin: '0 auto 16px' }}>
                      <Pen size={28} style={{ color: '#fc5c65' }} />
                    </div>
                    <h3 style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.3rem', marginBottom: 8 }}>
                      Final Confirmation
                    </h3>
                    <p style={{ color: '#fc5c65', fontSize: '0.9rem', fontWeight: 600 }}>
                      ⚠️ This action is irrevocable. Are you sure?
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={() => setArbConfirmStep(0)}
                      style={{ flex: 1, padding: '14px', borderRadius: 14, fontSize: '0.9rem', fontWeight: 600,
                        background: 'rgba(0,0,0,0.05)', border: '1px solid var(--border)', color: '#64748b', cursor: 'pointer' }}>
                      Go Back
                    </motion.button>
                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={signAsArbitrator}
                      className="btn-primary" style={{ flex: 1, padding: '14px', borderRadius: 14, fontSize: '0.9rem',
                        background: 'linear-gradient(135deg, #fc5c65, #eb3b5a)' }}>
                      ✍️ Sign Now — Final
                    </motion.button>
                  </div>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )

  // ─── Dashboard ────────────────────────────────────
  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '32px 24px' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 32 }}>
        <div>
          <h1 style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.8rem' }}>
            Welcome, <span style={{ color: '#ed8936' }}>{arbInfo?.name}</span>
          </h1>
          <p style={{ color: '#64748b', fontSize: '0.85rem', marginTop: 4 }}>
            <Shield size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />
            {arbInfo?.bar_registration || 'Certified Arbitrator'} • {arbInfo?.email}
          </p>
        </div>
        <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
          onClick={logout} style={{ padding: '10px 20px', borderRadius: 12, fontSize: '0.85rem', fontWeight: 600,
            background: 'rgba(252,92,101,0.1)', border: '1px solid rgba(252,92,101,0.2)', color: '#fc5c65', cursor: 'pointer' }}>
          Logout
        </motion.button>
      </motion.div>

      {/* Pending Cases */}
      <Section title="Pending Requests" icon={Clock} color="#ed8936" count={dashboard?.pending_cases?.length || 0}>
        {dashboard?.pending_cases?.map(c => (
          <CaseCard key={c.case_id} case_={c} onAccept={() => acceptCase(c.dispute_id)} />
        ))}
      </Section>

      {/* Active Cases */}
      <Section title="Active Cases" icon={Users} color="#667eea" count={dashboard?.active_cases?.length || 0}>
        {dashboard?.active_cases?.map(c => (
          <CaseCard key={c.case_id} case_={c} onJoin={() => joinSession(c.dispute_id)} isActive />
        ))}
      </Section>

      {/* Completed */}
      <Section title="Completed" icon={CheckCircle} color="#48bb78" count={dashboard?.completed_cases?.length || 0}>
        {dashboard?.completed_cases?.map(c => (
          <CaseCard key={c.case_id} case_={c} isCompleted />
        ))}
      </Section>
    </div>
  )
}

function Section({ title, icon: Icon, color, count, children }) {
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: 28 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <Icon size={18} style={{ color }} />
        <h3 style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '1.1rem' }}>{title}</h3>
        <span style={{ padding: '2px 10px', borderRadius: 100, background: `${color}15`, color, fontSize: '0.78rem', fontWeight: 700 }}>
          {count}
        </span>
      </div>
      {count === 0 ? (
        <div className="glass-static" style={{ padding: '32px', borderRadius: 16, textAlign: 'center', color: '#94a3b8', fontSize: '0.88rem' }}>
          No cases
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>{children}</div>
      )}
    </motion.div>
  )
}

function CaseCard({ case_, onAccept, onJoin, isActive, isCompleted }) {
  const [showReport, setShowReport] = useState(false)
  let report = null
  try { report = case_.ai_brief ? JSON.parse(case_.ai_brief) : null } catch { report = null }

  return (
    <motion.div className="glass-static" style={{ borderRadius: 16, overflow: 'hidden' }}>
      <div style={{ padding: '18px 24px', display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ width: 44, height: 44, borderRadius: 12,
          background: isCompleted ? 'rgba(72,187,120,0.12)' : isActive ? 'rgba(102,126,234,0.12)' : 'rgba(237,137,54,0.12)',
          border: `1px solid ${isCompleted ? 'rgba(72,187,120,0.2)' : isActive ? 'rgba(102,126,234,0.2)' : 'rgba(237,137,54,0.2)'}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Gavel size={20} style={{ color: isCompleted ? '#48bb78' : isActive ? '#667eea' : '#ed8936' }} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: '0.95rem', fontFamily: 'Outfit' }}>{case_.dispute_title}</div>
          <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: 2 }}>
            {case_.party_a_name} vs {case_.party_b_name} • {case_.dispute_type?.replace(/_/g, ' ')}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {report && (
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={() => setShowReport(!showReport)} style={{ padding: '8px 14px', borderRadius: 10, fontSize: '0.8rem',
                fontWeight: 700, background: 'rgba(118,75,162,0.1)', border: '1px solid rgba(118,75,162,0.2)',
                color: '#a78bfa', cursor: 'pointer' }}>
              {showReport ? 'Hide Report' : '📋 View Report'}
            </motion.button>
          )}
          {onAccept && (
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={onAccept} style={{ padding: '10px 20px', borderRadius: 12, fontSize: '0.85rem', fontWeight: 700,
                background: 'linear-gradient(135deg, #ed8936, #dd6b20)', color: 'white', border: 'none', cursor: 'pointer',
                boxShadow: '0 4px 15px rgba(237,137,54,0.3)' }}>
              Accept & Join
            </motion.button>
          )}
          {onJoin && (
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={onJoin} style={{ padding: '10px 20px', borderRadius: 12, fontSize: '0.85rem', fontWeight: 700,
                background: 'linear-gradient(135deg, #667eea, #764ba2)', color: 'white', border: 'none', cursor: 'pointer',
                boxShadow: '0 4px 15px rgba(102,126,234,0.3)' }}>
              Join Session
            </motion.button>
          )}
        </div>
      </div>

      {/* AI Case Report */}
      <AnimatePresence>
        {showReport && report && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} style={{ overflow: 'hidden' }}>
            <div style={{ padding: '0 24px 24px', borderTop: '1px solid var(--border)' }}>
              <div style={{ padding: '16px 0 8px', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Bot size={16} style={{ color: '#a78bfa' }} />
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#a78bfa', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  AI-Generated Case Report
                </span>
              </div>

              {/* Case Summary */}
              <ReportSection title="Case Summary" color="#667eea">{report.case_summary}</ReportSection>

              {/* Party Analyses - side by side */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 12 }}>
                <ReportSection title={`${case_.party_a_name || 'Party A'} Analysis`} color="#7c8cf0">
                  {report.party_a_analysis}
                </ReportSection>
                <ReportSection title={`${case_.party_b_name || 'Party B'} Analysis`} color="#68d391">
                  {report.party_b_analysis}
                </ReportSection>
              </div>

              {/* Mediation History */}
              <ReportSection title="Mediation History" color="#f093fb">{report.mediation_history}</ReportSection>

              {/* Key Issues */}
              {report.key_issues?.length > 0 && (
                <ReportSection title="Key Issues" color="#fc5c65">
                  <ul style={{ margin: 0, paddingLeft: 18 }}>
                    {report.key_issues.map((issue, i) => (
                      <li key={i} style={{ marginBottom: 4, fontSize: '0.85rem', color: '#475569' }}>{issue}</li>
                    ))}
                  </ul>
                </ReportSection>
              )}

              {/* Applicable Law */}
              {report.applicable_law?.length > 0 && (
                <ReportSection title="Applicable Law" color="#ed8936">
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {report.applicable_law.map((law, i) => (
                      <span key={i} style={{ padding: '4px 12px', borderRadius: 100, fontSize: '0.75rem', fontWeight: 600,
                        background: 'rgba(237,137,54,0.08)', color: '#ed8936', border: '1px solid rgba(237,137,54,0.15)' }}>
                        {law}
                      </span>
                    ))}
                  </div>
                </ReportSection>
              )}

              {/* Recommended Approach */}
              <ReportSection title="Recommended Approach" color="#48bb78" highlight>{report.recommended_approach}</ReportSection>

              {/* Risk Assessment */}
              <ReportSection title="Risk Assessment" color="#fc5c65">{report.risk_assessment}</ReportSection>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

function ReportSection({ title, color, children, highlight }) {
  return (
    <div style={{ marginTop: 12, padding: '14px 16px', borderRadius: 12,
      background: highlight ? `${color}08` : 'rgba(0,0,0,0.015)',
      border: `1px solid ${highlight ? `${color}20` : 'rgba(0,0,0,0.04)'}` }}>
      <div style={{ fontSize: '0.72rem', fontWeight: 700, color, textTransform: 'uppercase',
        letterSpacing: '0.05em', marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: '0.88rem', color: '#334155', lineHeight: 1.6 }}>{children}</div>
    </div>
  )
}

