import React, { useState, createContext, useContext } from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Scale, Home, FileText, BarChart3, Menu, X, Sparkles, ChevronDown } from 'lucide-react'
import Register from './pages/Register'
import Login from './pages/Login'
import Caucus from './pages/Caucus'
import JointSession from './pages/JointSession'
import Agreement from './pages/Agreement'
import Arbitration from './pages/Arbitration'
import ArbitratorDashboard from './pages/ArbitratorDashboard'
import CourtFiling from './pages/CourtFiling'
import Admin from './pages/Admin'
import Landing from './pages/Landing'

const API_URL = 'http://localhost:8000'
export const AppContext = createContext()
export function useAppContext() { return useContext(AppContext) }

const pageTransition = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.19, 1, 0.22, 1] } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.3 } },
}

function Navbar() {
  const location = useLocation()
  const [open, setOpen] = useState(false)
  
  const links = ['Home', 'Solutions', 'How It Works', 'Pricing', 'Resources', 'Contact']
  const isActive = (p) => location.pathname === p

  return (
    <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50, padding: '24px 0', background: 'transparent' }}>
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '0 40px' }}>
        <div className="glass-nav" style={{ 
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', 
          height: 72, padding: '0 12px 0 24px', borderRadius: 100, 
          background: 'rgba(255,255,255,0.85)', boxShadow: '0 4px 30px rgba(0,0,0,0.03)' 
        }}>
          
          {/* Logo (Left) */}
          <Link to="/" style={{ 
            display: 'flex', alignItems: 'center', gap: 10, background: '#0f172a',
            padding: '8px 20px 8px 12px', borderRadius: 100
          }}>
            <div style={{ width: 28, height: 28, borderRadius: '50%', background: 'white',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          boxShadow: 'inset 0 0 0 4px #cbd5e1' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#0f172a' }} />
            </div>
            <span style={{ fontSize: '1.05rem', fontWeight: 600, fontFamily: 'Outfit', color: 'white' }}>
              Madhyastha
            </span>
          </Link>

          {/* Links (Center) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 24 }} className="nav-links">
            {links.map((label) => (
              <Link key={label} to={label === 'Home' ? '/' : '#'} style={{
                fontSize: '0.9rem', fontWeight: 500, color: '#475569', transition: 'color 0.3s'
              }} onMouseOver={e => e.target.style.color = '#0f172a'} onMouseOut={e => e.target.style.color = '#475569'}>
                {label}
              </Link>
            ))}
          </div>

          {/* CTA (Right) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }} className="nav-links">
            <Link to="/login" className="btn-primary-dark" style={{ 
              padding: '12px 28px', fontSize: '0.9rem', borderRadius: 100,
              background: 'linear-gradient(135deg, #1e1b4b, #312e81)',
              color: 'white', fontWeight: 600, border: '1px solid rgba(255,255,255,0.1)',
              boxShadow: '0 8px 25px rgba(49, 46, 129, 0.4)'
            }}>
              Get Started
            </Link>
          </div>

          <button onClick={() => setOpen(!open)} className="mobile-toggle"
            style={{ display: 'none', background: 'none', border: 'none', color: '#475569', cursor: 'pointer', paddingRight: 12 }}>
            {open ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }} style={{ overflow: 'hidden', padding: '0 24px', margin: '16px 40px', 
            background: 'rgba(255,255,255,0.95)', borderRadius: 24, boxShadow: '0 20px 40px rgba(0,0,0,0.05)' }}>
            <div style={{ padding: '24px 0', display: 'flex', flexDirection: 'column', gap: 16 }}>
              {links.map((label) => (
                <Link key={label} to={label === 'Home' ? '/' : '#'} onClick={() => setOpen(false)}
                  style={{ fontSize: '1rem', fontWeight: 500, color: '#475569' }}>
                  {label}
                </Link>
              ))}
              <Link to="/login" onClick={() => setOpen(false)}
                style={{ background: '#0f172a', color: 'white', padding: '12px', borderRadius: 12, textAlign: 'center', fontWeight: 600 }}>
                Get Started
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @media (max-width: 900px) {
          .nav-links { display: none !important; }
          .mobile-toggle { display: block !important; }
        }
      `}</style>
    </nav>
  )
}

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <AnimatePresence mode="wait">
      <motion.div key={location.pathname} {...pageTransition}>
        <Routes location={location}>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/caucus" element={<Caucus />} />
          <Route path="/session/:disputeId" element={<JointSession />} />
          <Route path="/agreement/:disputeId" element={<Agreement />} />
          <Route path="/arbitration/:disputeId" element={<Arbitration />} />
          <Route path="/court/:disputeId" element={<CourtFiling />} />
          <Route path="/arbitrator-dashboard" element={<ArbitratorDashboard />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </motion.div>
    </AnimatePresence>
  )
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('party_token') || '')
  const saveToken = (t) => { setToken(t); localStorage.setItem('party_token', t) }

  return (
    <AppContext.Provider value={{ API_URL, token, setToken: saveToken }}>
      <BrowserRouter>
        <div style={{ background: '#e2e8f0', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
          <Navbar />
          <main style={{ paddingTop: 120, flex: 1 }}>
            <AnimatedRoutes />
          </main>
        </div>
      </BrowserRouter>
    </AppContext.Provider>
  )
}
