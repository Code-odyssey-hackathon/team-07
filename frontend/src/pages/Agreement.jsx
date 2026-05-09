import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useAppContext } from '../App'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Download, CheckCircle, Pen, AlertCircle, ShieldCheck, Gavel, AlertTriangle, X } from 'lucide-react'
import EscalationTracker from '../components/EscalationTracker'

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: [0.19, 1, 0.22, 1] },
})

export default function AgreementPage() {
  const { disputeId } = useParams()
  const { API_URL, token } = useAppContext()
  const [agreement, setAgreement] = useState(null)
  const [loading, setLoading] = useState(true)
  const [signing, setSigning] = useState(false)
  const [signed, setSigned] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [confirmStep, setConfirmStep] = useState(0) // 0=none, 1=first confirm, 2=final confirm

  useEffect(() => { loadAgreement() }, [disputeId])

  const loadAgreement = async () => {
    try {
      const res = await fetch(`${API_URL}/agreement/${disputeId}`)
      if (res.ok) { setAgreement(await res.json()) }
      else { await generateAgreement() }
    } catch { await generateAgreement() }
    finally { setLoading(false) }
  }

  const generateAgreement = async () => {
    setGenerating(true)
    try {
      const res = await fetch(`${API_URL}/agreement/${disputeId}/generate`, { method: 'POST' })
      if (res.ok) setAgreement(await res.json())
    } catch (e) { console.error(e) }
    finally { setGenerating(false) }
  }

  const initiateSign = () => {
    setConfirmStep(1) // Show first confirmation
  }

  const handleSign = async () => {
    setSigning(true)
    try {
      const res = await fetch(`${API_URL}/agreement/${disputeId}/sign`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ signature_data: 'digital_signature_confirmed' }),
      })
      if (res.ok) { setSigned(true); setConfirmStep(0); loadAgreement() }
    } catch (e) { console.error(e) }
    finally { setSigning(false) }
  }

  if (loading || generating) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '100px 0' }}>
      <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3, marginBottom: 16 }} />
      <p style={{ color: '#64748b', fontSize: '0.9rem' }}>{generating ? 'Drafting legal agreement...' : 'Loading agreement...'}</p>
    </div>
  )

  if (!agreement) return (
    <div style={{ maxWidth: 500, margin: '0 auto', padding: '100px 24px', textAlign: 'center' }}>
      <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
        <AlertCircle size={52} style={{ color: '#ed8936', marginBottom: 16 }} />
        <h2 style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '1.4rem', marginBottom: 8 }}>Agreement Not Ready</h2>
        <p style={{ color: '#64748b' }}>The agreement will be generated once both parties reach consensus.</p>
      </motion.div>
    </div>
  )

  const isArbitration = agreement.agreement_type === 'arbitration_award'
  const isFullySigned = agreement.party_a_signed && agreement.party_b_signed &&
    (isArbitration ? agreement.arbitrator_signed : true)

  return (
    <div style={{ maxWidth: 840, margin: '0 auto', padding: '32px 24px' }}>
      <motion.div {...fadeUp()} style={{ textAlign: 'center', marginBottom: 32 }}>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 800, fontFamily: 'Outfit', marginBottom: 6 }}>
          <span className="gradient-text">{isArbitration ? 'Arbitration Award' : 'Settlement Agreement'}</span>
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, color: '#64748b', fontSize: '0.85rem' }}>
          <ShieldCheck size={14} style={{ color: '#48bb78' }} />
          {isArbitration
            ? 'Binding under Section 36, Arbitration & Conciliation Act 1996'
            : 'Legally binding under Section 22, Mediation Act 2023'}
        </div>
      </motion.div>

      <EscalationTracker currentStage={isFullySigned ? 'resolved' : 'agreement_pending'} />

      {/* Agreement Content */}
      <motion.div {...fadeUp(0.1)} className="glass-static" style={{ marginTop: 32, padding: '40px 48px', borderRadius: 24 }}>
        <div style={{ borderBottom: '1px solid var(--border)', paddingBottom: 24, marginBottom: 32, textAlign: 'center' }}>
          <FileText size={48} style={{ color: '#667eea', margin: '0 auto 16px', opacity: 0.5 }} />
          <h2 style={{ fontFamily: 'Outfit', fontSize: '1.5rem', fontWeight: 700 }}>
            {isArbitration ? 'Arbitral Award' : 'Memorandum of Settlement'}
          </h2>
        </div>

        {agreement.terms?.sections?.map((section, i) => (
          <div key={i} style={{ marginBottom: 32 }}>
            <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem', fontWeight: 700, color: '#a78bfa', marginBottom: 12 }}>
              {section.heading}
            </h3>
            <p style={{ color: '#cbd5e1', fontSize: '0.95rem', lineHeight: 1.8, whiteSpace: 'pre-line' }}>{section.content}</p>
          </div>
        ))}

        {agreement.terms?.enforcement_note && (
          <div style={{ padding: 20, borderRadius: 16, background: 'rgba(102,126,234,0.06)', border: '1px solid rgba(102,126,234,0.15)', marginTop: 40 }}>
            <p style={{ color: '#a78bfa', fontSize: '0.88rem', fontStyle: 'italic', lineHeight: 1.6, textAlign: 'center' }}>
              {agreement.terms.enforcement_note}
            </p>
          </div>
        )}
      </motion.div>

      {/* Signature Status */}
      <motion.div {...fadeUp(0.2)} className="glass-static" style={{ marginTop: 24, padding: 32, borderRadius: 24 }}>
        <h3 style={{ fontFamily: 'Outfit', fontSize: '1.2rem', fontWeight: 700, marginBottom: 20 }}>Digital Signatures</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: isArbitration ? '1fr 1fr 1fr' : '1fr 1fr', gap: 16 }}>
          {[
            { label: 'Party A', signed: agreement.party_a_signed, date: agreement.party_a_signed_at, icon: Pen, color: '#667eea' },
            { label: 'Party B', signed: agreement.party_b_signed, date: agreement.party_b_signed_at, icon: Pen, color: '#48bb78' },
            ...(isArbitration ? [{
              label: agreement.arbitrator_name || 'Arbitrator',
              signed: agreement.arbitrator_signed,
              date: agreement.arbitrator_signed_at,
              icon: Gavel, color: '#ed8936'
            }] : [])
          ].map((party, i) => (
            <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 * i }}
              style={{ padding: 20, borderRadius: 16,
                background: party.signed ? `${party.color}08` : 'var(--bg-base)',
                border: `1px solid ${party.signed ? `${party.color}30` : 'var(--border)'}`,
                textAlign: 'center' }}>
              <div style={{ width: 48, height: 48, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: party.signed ? `${party.color}15` : 'rgba(0,0,0,0.05)', margin: '0 auto 12px',
                            border: `2px solid ${party.signed ? `${party.color}40` : 'transparent'}` }}>
                {party.signed
                  ? <CheckCircle size={22} style={{ color: party.color }} />
                  : <party.icon size={20} style={{ color: '#64748b' }} />}
              </div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: party.signed ? party.color : '#cbd5e1' }}>
                {party.label}
              </div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: 4 }}>
                {party.signed
                  ? `✓ Signed ${new Date(party.date).toLocaleDateString()}`
                  : '⏳ Awaiting signature'}
              </div>
            </motion.div>
          ))}
        </div>

        {/* Finalized Badge */}
        <AnimatePresence>
          {isFullySigned && (
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
              style={{ marginTop: 24, padding: '16px 24px', borderRadius: 16,
                background: 'rgba(72,187,120,0.08)', border: '1px solid rgba(72,187,120,0.25)',
                textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
              <CheckCircle size={20} style={{ color: '#48bb78' }} />
              <span style={{ fontWeight: 700, color: '#68d391', fontSize: '0.95rem' }}>
                Agreement Finalized — {new Date(agreement.finalized_at).toLocaleDateString()}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        <div style={{ display: 'flex', gap: 16, marginTop: 28, justifyContent: 'center' }}>
          {!signed && !isFullySigned && (
            <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
              onClick={initiateSign} className="btn-primary" disabled={signing} style={{ padding: '14px 32px', fontSize: '1rem' }}>
              <Pen size={18}/> Sign Agreement
            </motion.button>
          )}
          <motion.a whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            href={`${API_URL}/agreement/${disputeId}/download`} target="_blank" rel="noreferrer"
            className="btn-secondary" style={{ padding: '14px 32px', fontSize: '1rem' }}>
            <Download size={18} /> Download PDF
          </motion.a>
        </div>
      </motion.div>

      {/* ─── Double Confirmation Modal ─── */}
      <AnimatePresence>
        {confirmStep > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(6px)',
                     display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999 }}
            onClick={() => setConfirmStep(0)}>
            <motion.div initial={{ scale: 0.85, y: 30 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.85, y: 30 }}
              onClick={e => e.stopPropagation()}
              className="glass-static" style={{ maxWidth: 480, width: '90%', padding: 32, borderRadius: 24, position: 'relative' }}>

              {/* Close */}
              <button onClick={() => setConfirmStep(0)} style={{ position: 'absolute', top: 16, right: 16,
                background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                <X size={20} />
              </button>

              {confirmStep === 1 ? (
                <>
                  <div style={{ textAlign: 'center', marginBottom: 24 }}>
                    <div style={{ width: 56, height: 56, borderRadius: '50%', background: 'rgba(237,137,54,0.1)',
                                  border: '2px solid rgba(237,137,54,0.3)', display: 'flex', alignItems: 'center',
                                  justifyContent: 'center', margin: '0 auto 16px' }}>
                      <AlertTriangle size={28} style={{ color: '#ed8936' }} />
                    </div>
                    <h3 style={{ fontFamily: 'Outfit', fontWeight: 800, fontSize: '1.3rem', marginBottom: 8 }}>
                      Confirm Your Signature
                    </h3>
                    <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: 1.6 }}>
                      You are about to digitally sign this {isArbitration ? 'arbitration award' : 'settlement agreement'}.
                      This is a <strong style={{ color: '#f6ad55' }}>legally binding</strong> action.
                    </p>
                  </div>

                  <div style={{ padding: 16, borderRadius: 12, background: 'rgba(102,126,234,0.06)',
                                border: '1px solid rgba(102,126,234,0.15)', marginBottom: 24 }}>
                    <p style={{ fontSize: '0.82rem', color: '#94a3b8', lineHeight: 1.6 }}>
                      By proceeding, you confirm that you have read and understood all terms of this agreement and 
                      consent to be bound by its provisions under the applicable Indian law.
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: 12 }}>
                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={() => setConfirmStep(0)}
                      style={{ flex: 1, padding: '14px', borderRadius: 14, fontSize: '0.9rem', fontWeight: 600,
                        background: 'rgba(0,0,0,0.05)', border: '1px solid var(--border)', color: '#64748b', cursor: 'pointer' }}>
                      Cancel
                    </motion.button>
                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={() => setConfirmStep(2)}
                      className="btn-primary" style={{ flex: 1, padding: '14px', borderRadius: 14, fontSize: '0.9rem',
                        background: 'linear-gradient(135deg, #ed8936, #dd6b20)' }}>
                      I Understand, Continue →
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
                    <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: 1.6 }}>
                      This is your <strong style={{ color: '#fc5c65' }}>final confirmation</strong>.
                      Once signed, this agreement <strong>cannot be revoked</strong>.
                    </p>
                  </div>

                  <div style={{ padding: 16, borderRadius: 12, background: 'rgba(252,92,101,0.06)',
                                border: '1px solid rgba(252,92,101,0.15)', marginBottom: 24, textAlign: 'center' }}>
                    <p style={{ fontSize: '0.9rem', color: '#fc5c65', fontWeight: 700 }}>
                      ⚠️ Are you absolutely sure you want to sign?
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: 12 }}>
                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={() => setConfirmStep(0)}
                      style={{ flex: 1, padding: '14px', borderRadius: 14, fontSize: '0.9rem', fontWeight: 600,
                        background: 'rgba(0,0,0,0.05)', border: '1px solid var(--border)', color: '#64748b', cursor: 'pointer' }}>
                      Go Back
                    </motion.button>
                    <motion.button whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                      onClick={handleSign} disabled={signing}
                      className="btn-primary" style={{ flex: 1, padding: '14px', borderRadius: 14, fontSize: '0.9rem',
                        background: 'linear-gradient(135deg, #fc5c65, #eb3b5a)' }}>
                      {signing ? 'Signing...' : '✍️ Sign Now — Final'}
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
}
