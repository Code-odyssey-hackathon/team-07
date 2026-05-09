import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppContext } from '../App'
import { motion, AnimatePresence } from 'framer-motion'
import { Scale, Gavel, Users, ArrowRight, Mail, Lock, User, Shield, Sparkles, AlertTriangle, Eye, EyeOff } from 'lucide-react'

export default function Login() {
  const { API_URL } = useAppContext()
  const navigate = useNavigate()
  const [role, setRole] = useState(null) // null = role selection, 'user' = dispute party, 'arbitrator' = arbitrator
  const [mode, setMode] = useState('login') // login | register (for arbitrator)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPw, setShowPw] = useState(false)

  // Arbitrator form
  const [arbForm, setArbForm] = useState({ email: '', password: '', name: '', bar_registration: '' })

  const handleArbLogin = async () => {
    setLoading(true); setError('')
    try {
      const res = await fetch(`${API_URL}/arbitrator/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: arbForm.email, password: arbForm.password }),
      })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Login failed') }
      const data = await res.json()
      localStorage.setItem('arb_token', data.token)
      navigate('/arbitrator-dashboard')
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  const handleArbRegister = async () => {
    setLoading(true); setError('')
    try {
      const res = await fetch(`${API_URL}/arbitrator/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: arbForm.name, email: arbForm.email, password: arbForm.password,
          bar_registration: arbForm.bar_registration,
          specializations: ['money_loan', 'contract_breach', 'property'],
          languages: ['en', 'hi'],
        }),
      })
      if (!res.ok) { const d = await res.json(); throw new Error(d.detail || 'Registration failed') }
      const data = await res.json()
      localStorage.setItem('arb_token', data.token)
      navigate('/arbitrator-dashboard')
    } catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  // ── Role Selection ──
  if (!role) return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '60px 24px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ textAlign: 'center', marginBottom: 40 }}>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'Outfit', marginBottom: 8 }}>
          Welcome to <span className="gradient-text">Madhyastha</span>
        </h1>
        <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Choose how you'd like to proceed</p>
      </motion.div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* User / Dispute Party */}
        <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }}
          whileHover={{ scale: 1.02, y: -4 }} whileTap={{ scale: 0.98 }}
          onClick={() => { setRole('user'); navigate('/register') }}
          className="glass-static" style={{ padding: 32, borderRadius: 24, cursor: 'pointer', textAlign: 'center',
            border: '2px solid transparent', transition: 'border 0.3s' }}
          onMouseOver={e => e.currentTarget.style.borderColor = 'rgba(102,126,234,0.3)'}
          onMouseOut={e => e.currentTarget.style.borderColor = 'transparent'}>
          <div style={{ width: 72, height: 72, borderRadius: 20, margin: '0 auto 20px',
            background: 'linear-gradient(135deg, rgba(102,126,234,0.12), rgba(118,75,162,0.12))',
            border: '2px solid rgba(102,126,234,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Users size={32} style={{ color: '#667eea' }} />
          </div>
          <h3 style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '1.2rem', marginBottom: 8 }}>
            I Have a Dispute
          </h3>
          <p style={{ color: '#64748b', fontSize: '0.85rem', lineHeight: 1.6, marginBottom: 20 }}>
            Register a new case and resolve it through AI-powered mediation with the other party.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            color: '#667eea', fontWeight: 600, fontSize: '0.9rem' }}>
            Register a Dispute <ArrowRight size={16} />
          </div>
        </motion.div>

        {/* Arbitrator */}
        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }}
          whileHover={{ scale: 1.02, y: -4 }} whileTap={{ scale: 0.98 }}
          onClick={() => setRole('arbitrator')}
          className="glass-static" style={{ padding: 32, borderRadius: 24, cursor: 'pointer', textAlign: 'center',
            border: '2px solid transparent', transition: 'border 0.3s' }}
          onMouseOver={e => e.currentTarget.style.borderColor = 'rgba(237,137,54,0.3)'}
          onMouseOut={e => e.currentTarget.style.borderColor = 'transparent'}>
          <div style={{ width: 72, height: 72, borderRadius: 20, margin: '0 auto 20px',
            background: 'linear-gradient(135deg, rgba(237,137,54,0.12), rgba(221,107,32,0.12))',
            border: '2px solid rgba(237,137,54,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Gavel size={32} style={{ color: '#ed8936' }} />
          </div>
          <h3 style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '1.2rem', marginBottom: 8 }}>
            I'm an Arbitrator
          </h3>
          <p style={{ color: '#64748b', fontSize: '0.85rem', lineHeight: 1.6, marginBottom: 20 }}>
            Certified arbitrator? Login to your dashboard to review and resolve escalated cases.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            color: '#ed8936', fontWeight: 600, fontSize: '0.9rem' }}>
            Arbitrator Portal <ArrowRight size={16} />
          </div>
        </motion.div>
      </div>
    </div>
  )

  // ── Arbitrator Login/Register ──
  return (
    <div style={{ maxWidth: 460, margin: '0 auto', padding: '60px 24px' }}>
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {/* Back button */}
        <motion.button whileHover={{ x: -3 }} whileTap={{ scale: 0.97 }}
          onClick={() => { setRole(null); setError(''); setMode('login') }}
          style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer',
            fontSize: '0.85rem', fontWeight: 500, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 6 }}>
          ← Back to role selection
        </motion.button>

        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{ width: 56, height: 56, borderRadius: 16, margin: '0 auto 16px',
            background: 'linear-gradient(135deg, rgba(237,137,54,0.12), rgba(221,107,32,0.12))',
            border: '2px solid rgba(237,137,54,0.2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Gavel size={28} style={{ color: '#ed8936' }} />
          </div>
          <h2 style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.6rem', marginBottom: 6 }}>
            Arbitrator {mode === 'login' ? 'Login' : 'Registration'}
          </h2>
          <p style={{ color: '#64748b', fontSize: '0.88rem' }}>
            {mode === 'login' ? 'Access your arbitration dashboard' : 'Register as a certified arbitrator'}
          </p>
        </div>

        {/* Toggle login/register */}
        <div style={{ display: 'flex', gap: 4, padding: 4, borderRadius: 14, background: 'rgba(0,0,0,0.03)',
          border: '1px solid var(--border)', marginBottom: 24 }}>
          {['login', 'register'].map(m => (
            <motion.button key={m} whileTap={{ scale: 0.98 }}
              onClick={() => { setMode(m); setError('') }}
              style={{ flex: 1, padding: '10px', borderRadius: 12, border: 'none', cursor: 'pointer',
                fontSize: '0.85rem', fontWeight: 600, transition: 'all 0.3s',
                background: mode === m ? 'white' : 'transparent',
                color: mode === m ? '#0f172a' : '#64748b',
                boxShadow: mode === m ? '0 2px 8px rgba(0,0,0,0.06)' : 'none' }}>
              {m === 'login' ? 'Sign In' : 'Register'}
            </motion.button>
          ))}
        </div>

        {error && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            style={{ padding: '12px 16px', borderRadius: 12, background: 'rgba(252,92,101,0.08)',
              border: '1px solid rgba(252,92,101,0.2)', display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
            <AlertTriangle size={16} style={{ color: '#fc5c65' }} />
            <span style={{ color: '#fc8181', fontSize: '0.85rem' }}>{error}</span>
          </motion.div>
        )}

        <div className="glass-static" style={{ padding: 28, borderRadius: 20 }}>
          <AnimatePresence mode="wait">
            <motion.div key={mode} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
              style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

              {mode === 'register' && (
                <>
                  <div>
                    <label className="form-label"><User size={12} style={{ display: 'inline' }} /> Full Name</label>
                    <input className="input-field" placeholder="Adv. Your Name" value={arbForm.name}
                      onChange={e => setArbForm(p => ({ ...p, name: e.target.value }))} />
                  </div>
                  <div>
                    <label className="form-label"><Shield size={12} style={{ display: 'inline' }} /> Bar Registration No.</label>
                    <input className="input-field" placeholder="e.g. KAR/ADV/2020/1234" value={arbForm.bar_registration}
                      onChange={e => setArbForm(p => ({ ...p, bar_registration: e.target.value }))} />
                  </div>
                </>
              )}

              <div>
                <label className="form-label"><Mail size={12} style={{ display: 'inline' }} /> Email</label>
                <input className="input-field" type="email" placeholder="you@lawfirm.in" value={arbForm.email}
                  onChange={e => setArbForm(p => ({ ...p, email: e.target.value }))} />
              </div>

              <div>
                <label className="form-label"><Lock size={12} style={{ display: 'inline' }} /> Password</label>
                <div style={{ position: 'relative' }}>
                  <input className="input-field" type={showPw ? 'text' : 'password'} placeholder="••••••••"
                    value={arbForm.password} onChange={e => setArbForm(p => ({ ...p, password: e.target.value }))}
                    style={{ paddingRight: 44 }}
                    onKeyDown={e => { if (e.key === 'Enter') { mode === 'login' ? handleArbLogin() : handleArbRegister() } }} />
                  <button onClick={() => setShowPw(!showPw)} style={{ position: 'absolute', right: 12, top: '50%',
                    transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                    {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                onClick={mode === 'login' ? handleArbLogin : handleArbRegister}
                disabled={loading || !arbForm.email || !arbForm.password || (mode === 'register' && !arbForm.name)}
                className="btn-primary" style={{ marginTop: 8, padding: '14px', fontSize: '0.95rem', borderRadius: 14,
                  background: 'linear-gradient(135deg, #ed8936, #dd6b20)',
                  opacity: loading || !arbForm.email || !arbForm.password ? 0.5 : 1,
                  boxShadow: '0 6px 20px rgba(237,137,54,0.3)' }}>
                {loading
                  ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Processing...</>
                  : mode === 'login'
                    ? <><Gavel size={16} /> Sign In to Dashboard</>
                    : <><Sparkles size={16} /> Register as Arbitrator</>}
              </motion.button>
            </motion.div>
          </AnimatePresence>
        </div>

        <p style={{ textAlign: 'center', color: '#94a3b8', fontSize: '0.78rem', marginTop: 16 }}>
          {mode === 'login'
            ? <>Don't have an account? <button onClick={() => setMode('register')} style={{ background: 'none', border: 'none', color: '#ed8936', cursor: 'pointer', fontWeight: 600 }}>Register here</button></>
            : <>Already registered? <button onClick={() => setMode('login')} style={{ background: 'none', border: 'none', color: '#ed8936', cursor: 'pointer', fontWeight: 600 }}>Sign in</button></>
          }
        </p>
      </motion.div>
    </div>
  )
}
