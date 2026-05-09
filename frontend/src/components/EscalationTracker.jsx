import React from 'react'
import { motion } from 'framer-motion'
import { Shield, Gavel, Scale, CheckCircle, ArrowRight } from 'lucide-react'

const STAGES = [
  { key: 'mediation', label: 'AI Mediation', icon: Shield, color: '#667eea',
    statuses: ['registered', 'awaiting_party_b', 'caucus_a', 'caucus_b', 'caucus',
               'synthesis', 'joint_session', 'agreement_pending', 'resolved'] },
  { key: 'arbitration', label: 'Arbitration', icon: Gavel, color: '#ed8936',
    statuses: ['escalated_arbitration', 'arbitration_hearing', 'award_issued', 'arbitration'] },
  { key: 'court', label: 'Court Filing', icon: Scale, color: '#fc5c65',
    statuses: ['court_filing'] },
]

export default function EscalationTracker({ currentStage }) {
  const currentIdx = STAGES.findIndex(s => s.statuses.includes(currentStage))

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, flexWrap: 'wrap' }}>
      {STAGES.map((stage, i) => {
        const isCompleted = i < currentIdx
        const isActive = i === currentIdx
        const isPending = i > currentIdx

        return (
          <React.Fragment key={stage.key}>
            {i > 0 && (
              <motion.div animate={{ opacity: isCompleted ? 1 : 0.2 }}
                style={{ display: 'flex', alignItems: 'center' }}>
                <div style={{ width: 24, height: 1, background: isCompleted ? '#48bb78' : '#cbd5e1' }} />
                <ArrowRight size={12} style={{ color: isCompleted ? '#48bb78' : '#cbd5e1' }} />
              </motion.div>
            )}
            <motion.div
              animate={isActive ? { boxShadow: `0 0 20px ${stage.color}20` } : {}}
              transition={{ duration: 2, repeat: Infinity, repeatType: 'reverse' }}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '10px 18px', borderRadius: 12,
                fontSize: '0.82rem', fontWeight: 600, letterSpacing: '0.01em',
                background: isActive ? `${stage.color}12` : isCompleted ? 'rgba(72,187,120,0.06)' : 'transparent',
                border: `1px solid ${isActive ? `${stage.color}30` : isCompleted ? 'rgba(72,187,120,0.15)' : 'rgba(0,0,0,0.04)'}`,
                color: isActive ? stage.color : isCompleted ? '#48bb78' : '#94a3b8',
                transition: 'all 0.4s',
              }}>
              {isCompleted ? <CheckCircle size={14} style={{ color: '#48bb78' }} /> : <stage.icon size={14} />}
              <span>{stage.label}</span>
            </motion.div>
          </React.Fragment>
        )
      })}
    </div>
  )
}
