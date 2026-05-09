import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Phone, Calendar, User, ShieldCheck, Activity } from 'lucide-react'

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.8, delay, ease: [0.19, 1, 0.22, 1] },
})

export default function Landing() {
  return (
    <div style={{ padding: '40px 40px', maxWidth: 1400, margin: '0 auto', overflow: 'hidden' }}>
      
      {/* ═══ HERO SECTION ═══ */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 60, alignItems: 'center' }}>
        
        {/* Left Content */}
        <div>
          {/* Top Badges */}
          <motion.div {...fadeUp(0)} style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 40 }}>
            <div style={{ 
              display: 'inline-flex', alignItems: 'center', gap: 8, padding: '8px 16px', 
              background: 'rgba(255,255,255,0.6)', borderRadius: 100, border: '1px solid rgba(255,255,255,0.8)',
              fontSize: '0.85rem', fontWeight: 600, color: '#1e293b', boxShadow: '0 4px 15px rgba(0,0,0,0.02)'
            }}>
              <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#475569' }} />
              New: Advanced Predictive Arbitration
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ display: 'flex' }}>
                {[1, 2, 3].map((i) => (
                  <div key={i} style={{ 
                    width: 32, height: 32, borderRadius: '50%', background: '#cbd5e1', 
                    marginLeft: i !== 1 ? -12 : 0, border: '2px solid #e2e8f0',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden'
                  }}>
                    <User size={16} color="white" />
                  </div>
                ))}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#64748b', lineHeight: 1.4 }}>
                Rated 5/5 & Trusted<br/>by +5K Citizens
              </div>
            </div>
          </motion.div>

          {/* Main Typography */}
          <motion.h1 {...fadeUp(0.1)} style={{ 
            fontSize: 'clamp(3.5rem, 5vw, 4.5rem)', fontWeight: 600, fontFamily: 'Inter, sans-serif', 
            lineHeight: 1.05, letterSpacing: '-0.03em', color: '#0f172a', marginBottom: 24 
          }}>
            AI-Powered<br/>
            <span style={{ color: '#64748b' }}>Dispute Resolution for</span><br/>
            Better Outcomes
          </motion.h1>

          <motion.p {...fadeUp(0.2)} style={{ 
            fontSize: '1.1rem', color: '#64748b', maxWidth: 480, lineHeight: 1.6, marginBottom: 40 
          }}>
            Analyze case data, predict legal risks, and support resolution decisions with secure, intelligent technology.
          </motion.p>

          {/* Buttons */}
          <motion.div {...fadeUp(0.3)} style={{ display: 'flex', gap: 16 }}>
            <Link to="/login" style={{ 
              display: 'inline-flex', alignItems: 'center', gap: 10, padding: '16px 36px', 
              background: 'linear-gradient(135deg, #1e1b4b, #312e81)', color: 'white', 
              borderRadius: 100, fontSize: '1.05rem', fontWeight: 500,
              boxShadow: '0 15px 35px rgba(49, 46, 129, 0.4)', transition: 'transform 0.3s'
            }} onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'} 
               onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}>
              <Phone size={18} style={{ opacity: 0.8 }} /> Register Case
            </Link>
            
            <Link to="/admin" style={{ 
              display: 'inline-flex', alignItems: 'center', padding: '16px 36px', 
              background: 'rgba(255,255,255,0.6)', color: '#0f172a', 
              borderRadius: 100, fontSize: '1.05rem', fontWeight: 500,
              border: '1px solid rgba(255,255,255,0.8)', transition: 'background 0.3s'
            }} onMouseOver={e => e.currentTarget.style.background = 'white'} 
               onMouseOut={e => e.currentTarget.style.background = 'rgba(255,255,255,0.6)'}>
              Dashboard
            </Link>
          </motion.div>
        </div>

        {/* Right Content (Robot Image) */}
        <motion.div {...fadeUp(0.4)} style={{ position: 'relative', height: '100%', minHeight: 600, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          
          {/* Main 3D Robot Image */}
          <img src="/hero-robot.png" alt="AI Robot Judge" 
               style={{ width: '100%', maxWidth: 650, objectFit: 'contain', position: 'relative', zIndex: 1, filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.1))' }} />

          {/* Floating UI Element 1: Status */}
          <motion.div animate={{ y: [0, -10, 0] }} transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            style={{ 
            position: 'absolute', top: '35%', left: '-10%', zIndex: 2, 
            background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(16px)', 
            padding: '16px 20px', borderRadius: 16, border: '1px solid white',
            boxShadow: '0 10px 30px rgba(0,0,0,0.05)'
          }}>
            <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 600, marginBottom: 4 }}>System Status</div>
            <div style={{ fontSize: '0.95rem', color: '#0f172a', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
              Mediation Complete
            </div>
            <div style={{ marginTop: 8, height: 4, background: '#e2e8f0', borderRadius: 4, overflow: 'hidden' }}>
              <div style={{ width: '100%', height: '100%', background: 'linear-gradient(90deg, #818cf8, #c084fc)' }} />
            </div>
          </motion.div>

          {/* Floating UI Element 2: Experts */}
          <motion.div animate={{ y: [0, 10, 0] }} transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
            style={{ 
            position: 'absolute', bottom: '15%', right: '5%', zIndex: 2, 
            background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(16px)', 
            padding: '12px 20px', borderRadius: 100, border: '1px solid white',
            boxShadow: '0 10px 30px rgba(0,0,0,0.05)', display: 'flex', alignItems: 'center', gap: 16
          }}>
            <div style={{ display: 'flex' }}>
              {[1, 2, 3].map((i) => (
                <div key={i} style={{ 
                  width: 32, height: 32, borderRadius: '50%', background: '#cbd5e1', 
                  marginLeft: i !== 1 ? -12 : 0, border: '2px solid white',
                  display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                  <ShieldCheck size={16} color="white" />
                </div>
              ))}
            </div>
            <div>
              <div style={{ fontSize: '0.95rem', color: '#0f172a', fontWeight: 800 }}>500+</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 500 }}>Certified Arbitrators</div>
            </div>
          </motion.div>

        </motion.div>
      </div>

      {/* ═══ STATS BAR ═══ */}
      <motion.div {...fadeUp(0.5)} style={{ 
        marginTop: 20, display: 'flex', gap: 24, padding: '32px',
        background: 'rgba(255,255,255,0.5)', borderRadius: 24, border: '1px solid rgba(255,255,255,0.8)'
      }}>
        {[
          { value: '98%', label: 'Resolution Accuracy' },
          { value: '24/7', label: 'Case Monitoring' },
          { value: '1M+', label: 'Case Precedents' },
          { value: '40%', label: 'Faster Decisions' }
        ].map((stat, i) => (
          <div key={i} style={{ 
            flex: 1, padding: '0 24px', 
            borderRight: i !== 3 ? '1px solid rgba(0,0,0,0.05)' : 'none' 
          }}>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a', marginBottom: 4 }}>{stat.value}</div>
            <div style={{ fontSize: '0.85rem', color: '#64748b', fontWeight: 500 }}>{stat.label}</div>
          </div>
        ))}
      </motion.div>

    </div>
  )
}
