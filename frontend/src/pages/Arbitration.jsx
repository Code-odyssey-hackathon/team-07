import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAppContext } from '../App'
import { motion, AnimatePresence } from 'framer-motion'
import { Gavel, CheckCircle, Clock, User, AlertCircle, ShieldCheck, Star, Globe, ArrowRight } from 'lucide-react'
import EscalationTracker from '../components/EscalationTracker'

export default function ArbitrationPage() {
  const { disputeId } = useParams()
  const { API_URL, token } = useAppContext()
  const navigate = useNavigate()
  const [arbitrators, setArbitrators] = useState([])
  const [selectedArb, setSelectedArb] = useState(null)
  const [assigned, setAssigned] = useState(false)
  const [loading, setLoading] = useState(true)
  const [assigning, setAssigning] = useState(false)

  useEffect(() => { loadArbitrators() }, [])

  const loadArbitrators = async () => {
    try {
      const res = await fetch(`${API_URL}/arbitrator/available`)
      if (res.ok) setArbitrators(await res.json())
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const assignArbitrator = async () => {
    if (!selectedArb) return
    setAssigning(true)
    try {
      const res = await fetch(`${API_URL}/arbitrator/${disputeId}/assign?arbitrator_id=${selectedArb}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
      })
      if (res.ok) setAssigned(true)
    } catch (e) { console.error(e) }
    finally { setAssigning(false) }
  }

  if (loading) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '100px 0' }}>
      <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3, marginBottom: 16 }} />
      <p style={{ color: '#64748b', fontSize: '0.9rem' }}>Loading arbitrators...</p>
    </div>
  )

  if (assigned) return (
    <div style={{ maxWidth: 520, margin: '0 auto', padding: '100px 24px', textAlign: 'center' }}>
      <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: 'spring' }}>
        <motion.div animate={{ scale: [1, 1.15, 1] }} transition={{ duration: 2, repeat: Infinity }}
          style={{ width: 80, height: 80, borderRadius: '50%', background: 'rgba(72,187,120,0.1)',
                   border: '2px solid rgba(72,187,120,0.3)', display: 'flex', alignItems: 'center',
                   justifyContent: 'center', margin: '0 auto 20px' }}>
          <CheckCircle size={40} style={{ color: '#48bb78' }} />
        </motion.div>
        <h2 style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.6rem', marginBottom: 8 }}>
          Arbitrator Assigned!
        </h2>
        <p style={{ color: '#64748b', marginBottom: 8, lineHeight: 1.7 }}>
          Your request has been sent to the selected arbitrator. Once they accept, you'll be able to join the arbitration session.
        </p>
        <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: 24 }}>
          The arbitrator will review the case brief and join the session as the presiding officer.
        </p>
        <EscalationTracker currentStage="arbitration" />
        <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
          onClick={() => navigate(`/session/${disputeId}`)}
          className="btn-primary" style={{ marginTop: 24, padding: '14px 32px', fontSize: '1rem' }}>
          Go to Session
        </motion.button>
      </motion.div>
    </div>
  )

  return (
    <div style={{ maxWidth: 840, margin: '0 auto', padding: '32px 24px' }}>
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
        style={{ textAlign: 'center', marginBottom: 32 }}>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'Outfit', marginBottom: 6 }}>
          <span className="gradient-text">Select an Arbitrator</span>
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, color: '#64748b', fontSize: '0.85rem' }}>
          <ShieldCheck size={14} style={{ color: '#a78bfa' }} /> Certified under Arbitration & Conciliation Act, 1996
        </div>
      </motion.div>

      <EscalationTracker currentStage="arbitration" />

      {arbitrators.length === 0 ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}
          className="glass-static" style={{ marginTop: 32, padding: 40, borderRadius: 20, textAlign: 'center' }}>
          <AlertCircle size={40} style={{ color: '#ed8936', marginBottom: 16 }} />
          <h3 style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '1.2rem', marginBottom: 8 }}>No Arbitrators Available</h3>
          <p style={{ color: '#64748b' }}>Please check back later or register as an arbitrator.</p>
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={() => navigate('/arbitrator-dashboard')}
            className="btn-primary" style={{ marginTop: 16, padding: '12px 24px', background: 'linear-gradient(135deg, #ed8936, #dd6b20)' }}>
            Register as Arbitrator
          </motion.button>
        </motion.div>
      ) : (
        <div style={{ marginTop: 32, display: 'flex', flexDirection: 'column', gap: 14 }}>
          {arbitrators.map((arb, i) => (
            <motion.div key={arb.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }} whileHover={{ scale: 1.005 }}
              onClick={() => setSelectedArb(arb.id)}
              className="glass-static" style={{
                padding: '20px 24px', borderRadius: 18, cursor: 'pointer', transition: 'all 0.3s',
                border: selectedArb === arb.id ? '2px solid #ed8936' : '1px solid var(--border)',
                boxShadow: selectedArb === arb.id ? '0 0 20px rgba(237,137,54,0.15)' : 'none',
              }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ width: 52, height: 52, borderRadius: 14,
                  background: selectedArb === arb.id ? 'linear-gradient(135deg, #ed8936, #dd6b20)' : 'rgba(237,137,54,0.08)',
                  border: `1px solid ${selectedArb === arb.id ? 'transparent' : 'rgba(237,137,54,0.15)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'all 0.3s' }}>
                  <Gavel size={22} style={{ color: selectedArb === arb.id ? 'white' : '#ed8936' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '1.05rem', fontFamily: 'Outfit' }}>{arb.name}</div>
                  {arb.bar_registration && (
                    <div style={{ fontSize: '0.78rem', color: '#94a3b8', marginTop: 2 }}>
                      Bar: {arb.bar_registration}
                    </div>
                  )}
                  <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                    {arb.specializations?.map(s => (
                      <span key={s} style={{ padding: '3px 10px', borderRadius: 100, fontSize: '0.72rem', fontWeight: 600,
                        background: 'rgba(102,126,234,0.08)', color: '#667eea', border: '1px solid rgba(102,126,234,0.15)' }}>
                        {s}
                      </span>
                    ))}
                    {arb.languages?.map(l => (
                      <span key={l} style={{ padding: '3px 10px', borderRadius: 100, fontSize: '0.72rem', fontWeight: 600,
                        background: 'rgba(118,75,162,0.08)', color: '#a78bfa', border: '1px solid rgba(118,75,162,0.15)' }}>
                        <Globe size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />{l}
                      </span>
                    ))}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{arb.cases_assigned} cases</div>
                  {selectedArb === arb.id && (
                    <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}
                      style={{ width: 24, height: 24, borderRadius: '50%', background: '#ed8936',
                               display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 4, marginLeft: 'auto' }}>
                      <CheckCircle size={14} color="white" />
                    </motion.div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}

          <AnimatePresence>
            {selectedArb && (
              <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 16 }}
                style={{ textAlign: 'center', marginTop: 8 }}>
                <motion.button whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                  onClick={assignArbitrator} disabled={assigning}
                  className="btn-primary" style={{ padding: '16px 40px', fontSize: '1.05rem', borderRadius: 16,
                    background: 'linear-gradient(135deg, #ed8936, #dd6b20)',
                    boxShadow: '0 8px 25px rgba(237,137,54,0.35)' }}>
                  {assigning ? 'Sending Request...' : <>Send Request <ArrowRight size={18} /></>}
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  )
}
