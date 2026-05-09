import React, { useState, useEffect } from 'react'
import { useAppContext } from '../App'
import { motion } from 'framer-motion'
import { BarChart3, Users, CheckCircle, Gavel, AlertTriangle, TrendingUp, FileText, Activity, ArrowUpRight, Shield, Zap, Eye, Send, MapPin } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts'

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#48bb78', '#ed8936', '#fc5c65', '#38b2ac', '#ecc94b', '#9f7aea', '#fc8181']

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 25 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: [0.19, 1, 0.22, 1] },
})

function StatCard({ icon: Icon, label, value, color, trend, delay }) {
  return (
    <motion.div {...fadeUp(delay)} className="glass" style={{ padding: 24, borderRadius: 18, position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, right: 0, width: 80, height: 80, borderRadius: '0 0 0 80px',
                    background: `${color}08`, zIndex: 0 }} />
      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: `${color}10`, border: `1px solid ${color}20`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Icon size={18} style={{ color }} />
          </div>
          {trend && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: '0.72rem', fontWeight: 600, color: '#48bb78' }}>
              <ArrowUpRight size={12} /> {trend}
            </div>
          )}
        </div>
        <div style={{ fontSize: '1.8rem', fontWeight: 800, fontFamily: 'Outfit', lineHeight: 1.1 }}>{value}</div>
        <div style={{ fontSize: '0.78rem', color: '#64748b', marginTop: 4, fontWeight: 500 }}>{label}</div>
      </div>
    </motion.div>
  )
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#ffffff', border: '1px solid rgba(102,126,234,0.2)', borderRadius: 12,
                  padding: '10px 14px', boxShadow: '0 8px 30px rgba(0,0,0,0.1)' }}>
      <p style={{ color: '#475569', fontSize: '0.78rem', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || '#667eea', fontWeight: 600, fontSize: '0.88rem' }}>{p.value}</p>
      ))}
    </div>
  )
}

function RiskScoreBar({ score }) {
  const color = score >= 72 ? '#fc5c65' : score >= 50 ? '#ed8936' : '#48bb78'
  const label = score >= 72 ? 'HIGH' : score >= 50 ? 'MEDIUM' : 'LOW'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{ flex: 1, height: 6, background: '#e2e8f0', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ width: `${score}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 1s ease' }} />
      </div>
      <span style={{ fontSize: '0.75rem', fontWeight: 700, color, minWidth: 50 }}>{score} {label}</span>
    </div>
  )
}

export default function Admin() {
  const { API_URL } = useAppContext()
  const [stats, setStats] = useState(null)
  const [disputes, setDisputes] = useState([])
  const [loading, setLoading] = useState(true)
  const [riskDemo, setRiskDemo] = useState(null)
  const [civicTrail, setCivicTrail] = useState([])
  const [nudgeResult, setNudgeResult] = useState(null)
  const [scoringParty, setScoringParty] = useState('PROP-BLR-2024-78901')

  useEffect(() => { loadData() }, [])

  const loadData = async () => {
    try {
      const [sr, dr] = await Promise.all([
        fetch(`${API_URL}/dispute/stats/summary`), fetch(`${API_URL}/dispute/all`),
      ])
      if (sr.ok) setStats(await sr.json())
      if (dr.ok) setDisputes(await dr.json())
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const runRiskScore = async () => {
    try {
      const res = await fetch(`${API_URL}/risk/score`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ party_identifier: scoringParty })
      })
      if (res.ok) { setRiskDemo(await res.json()) }
    } catch (e) { console.error(e) }
  }

  const loadCivicTrail = async () => {
    try {
      const res = await fetch(`${API_URL}/civic/events/${scoringParty}`)
      if (res.ok) { setCivicTrail(await res.json()) }
    } catch (e) { console.error(e) }
  }

  const sendNudge = async () => {
    try {
      const res = await fetch(`${API_URL}/risk/nudge/${scoringParty}?language=kn`, { method: 'POST' })
      if (res.ok) { setNudgeResult(await res.json()) }
    } catch (e) { console.error(e) }
  }

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: '100px 0' }}><div className="spinner" /></div>

  const statCards = stats ? [
    { label: 'Total Disputes', value: stats.total_disputes, icon: FileText, color: '#667eea', trend: null },
    { label: 'Active', value: stats.active_disputes, icon: Activity, color: '#ed8936', trend: null },
    { label: 'Resolved', value: stats.resolved_disputes, icon: CheckCircle, color: '#48bb78', trend: null },
    { label: 'Arbitration', value: stats.escalated_to_arbitration, icon: Gavel, color: '#764ba2', trend: null },
    { label: 'Court Filings', value: stats.court_filings, icon: AlertTriangle, color: '#fc5c65', trend: null },
    { label: 'Resolution Rate', value: `${stats.resolution_rate}%`, icon: TrendingUp, color: '#38b2ac', trend: null },
  ] : []

  const typeData = stats ? Object.entries(stats.disputes_by_type).map(([k, v]) => ({
    name: k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()), value: v
  })) : []

  const statusData = stats ? Object.entries(stats.disputes_by_status).map(([k, v]) => ({
    name: k.replace(/_/g, ' '), value: v
  })) : []

  const statusBadge = (s) => {
    const m = { registered: 'badge-neutral', awaiting_party_b: 'badge-warning', caucus_a: 'badge-active',
      caucus_b: 'badge-active', synthesis: 'badge-active', joint_session: 'badge-active',
      agreement_pending: 'badge-warning', resolved: 'badge-success', escalated_human: 'badge-warning',
      escalated_arbitration: 'badge-danger', arbitration_hearing: 'badge-warning', award_issued: 'badge-success',
      court_filing: 'badge-danger', closed: 'badge-neutral' }
    return m[s] || 'badge-neutral'
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
      <motion.div {...fadeUp()} style={{ marginBottom: 36 }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'Outfit', marginBottom: 4 }}>
          <span className="gradient-text">Dashboard</span>
        </h1>
        <p style={{ color: '#475569', fontSize: '0.92rem' }}>Madhyastha platform analytics & dispute management</p>
      </motion.div>

      {/* Stats Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 16, marginBottom: 28 }}>
        {statCards.map((c, i) => (
          <StatCard key={i} {...c} delay={i * 0.06} />
        ))}
      </div>

      {/* ═══ PREVENTION ENGINE — Risk Scorer ═══ */}
      <motion.div {...fadeUp(0.25)} className="glass-static" style={{ padding: 28, borderRadius: 20, marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
          <div style={{ width: 40, height: 40, borderRadius: 12, background: 'rgba(252,92,101,0.1)', border: '1px solid rgba(252,92,101,0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Shield size={18} style={{ color: '#fc5c65' }} />
          </div>
          <div>
            <h3 style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '1.1rem', margin: 0 }}>Prevention Engine — LightGBM Risk Scorer</h3>
            <p style={{ fontSize: '0.8rem', color: '#64748b', margin: 0 }}>Predict dispute probability from civic event streams</p>
          </div>
        </div>

        {/* Controls */}
        <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
          <select className="input-field" value={scoringParty} onChange={e => setScoringParty(e.target.value)}
            style={{ maxWidth: 320, padding: '10px 14px', fontSize: '0.88rem' }}>
            <option value="PROP-BLR-2024-78901">🏠 PROP-BLR-2024-78901 (Bengaluru — High Risk)</option>
            <option value="PROP-MUM-2024-34567">🏢 PROP-MUM-2024-34567 (Mumbai — Medium Risk)</option>
            <option value="PROP-CHN-2024-11223">🏡 PROP-CHN-2024-11223 (Chennai — Low Risk)</option>
            <option value="PROP-DEL-2024-55678">🏗️ PROP-DEL-2024-55678 (Delhi)</option>
          </select>

          <button className="btn-primary" onClick={() => { runRiskScore(); loadCivicTrail() }} style={{ borderRadius: 100 }}>
            <Zap size={16} /> Score Risk
          </button>
          <button className="btn-secondary" onClick={loadCivicTrail} style={{ borderRadius: 100 }}>
            <Eye size={16} /> View Trail
          </button>
          <button className="btn-secondary" onClick={sendNudge} style={{ borderRadius: 100 }}>
            <Send size={16} /> Send Nudge
          </button>
        </div>

        {/* Results Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
          
          {/* Risk Score Result */}
          {riskDemo && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
              style={{ padding: 20, borderRadius: 16, background: 'rgba(255,255,255,0.5)', border: '1px solid rgba(0,0,0,0.05)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, margin: 0 }}>🎯 Risk Score Result</h4>
                <span className={`badge ${riskDemo.risk_score >= 72 ? 'badge-danger' : riskDemo.risk_score >= 50 ? 'badge-warning' : 'badge-success'}`}>
                  {riskDemo.risk_score >= 72 ? 'HIGH RISK' : riskDemo.risk_score >= 50 ? 'MEDIUM' : 'LOW RISK'}
                </span>
              </div>

              <div style={{ fontSize: '3rem', fontWeight: 800, fontFamily: 'Outfit', color: riskDemo.risk_score >= 72 ? '#fc5c65' : riskDemo.risk_score >= 50 ? '#ed8936' : '#48bb78',
                            textAlign: 'center', marginBottom: 8 }}>
                {riskDemo.risk_score}
              </div>
              <RiskScoreBar score={riskDemo.risk_score} />

              <div style={{ marginTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: '0.8rem' }}>
                <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.02)', borderRadius: 8 }}>
                  <div style={{ color: '#94a3b8', fontWeight: 500 }}>Predicted Type</div>
                  <div style={{ fontWeight: 700, color: '#1e293b' }}>{riskDemo.predicted_dispute_type.replace(/_/g, ' ')}</div>
                </div>
                <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.02)', borderRadius: 8 }}>
                  <div style={{ color: '#94a3b8', fontWeight: 500 }}>Nudge Recommended</div>
                  <div style={{ fontWeight: 700, color: riskDemo.nudge_recommended ? '#fc5c65' : '#48bb78' }}>
                    {riskDemo.nudge_recommended ? '✅ Yes' : '❌ No'}
                  </div>
                </div>
                <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.02)', borderRadius: 8 }}>
                  <div style={{ color: '#94a3b8', fontWeight: 500 }}>Events Analyzed</div>
                  <div style={{ fontWeight: 700, color: '#1e293b' }}>{riskDemo.feature_breakdown?.event_count || 0}</div>
                </div>
                <div style={{ padding: '8px 12px', background: 'rgba(0,0,0,0.02)', borderRadius: 8 }}>
                  <div style={{ color: '#94a3b8', fontWeight: 500 }}>Model</div>
                  <div style={{ fontWeight: 700, color: '#1e293b' }}>{riskDemo.model_info?.using_mock ? 'Mock' : 'LightGBM'}</div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Civic Event Trail */}
          {civicTrail.length > 0 && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
              style={{ padding: 20, borderRadius: 16, background: 'rgba(255,255,255,0.5)', border: '1px solid rgba(0,0,0,0.05)' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 16 }}>
                📋 Civic Event Trail ({civicTrail.length} events)
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {civicTrail.map((evt, i) => (
                  <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                    <div style={{ minWidth: 10, height: 10, borderRadius: '50%', marginTop: 5,
                                  background: evt.source === 'rera' ? '#fc5c65' : evt.source === 'cpgrams' ? '#ed8936' :
                                  evt.source === 'cersai' ? '#764ba2' : '#667eea' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.82rem', fontWeight: 700, color: '#1e293b' }}>
                        {evt.event_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748b', display: 'flex', gap: 12 }}>
                        <span><MapPin size={10} style={{ display: 'inline', marginRight: 2 }} />{evt.district}, {evt.state}</span>
                        <span>{new Date(evt.event_date).toLocaleDateString()}</span>
                        <span style={{ textTransform: 'uppercase', fontWeight: 600, color: '#94a3b8' }}>{evt.source}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {/* Nudge Result */}
          {nudgeResult && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
              style={{ padding: 20, borderRadius: 16, background: nudgeResult.nudge_sent ? 'rgba(72,187,120,0.05)' : 'rgba(237,137,54,0.05)',
                       border: `1px solid ${nudgeResult.nudge_sent ? 'rgba(72,187,120,0.2)' : 'rgba(237,137,54,0.2)'}`,
                       gridColumn: civicTrail.length > 0 && riskDemo ? '1 / -1' : 'auto' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: 12 }}>
                📱 WhatsApp Nudge {nudgeResult.nudge_sent ? '— Sent ✅' : '— Not Required'}
              </h4>
              <div style={{ fontSize: '0.85rem', color: '#334155', padding: 14, background: 'rgba(255,255,255,0.6)',
                            borderRadius: 12, border: '1px solid rgba(0,0,0,0.05)', lineHeight: 1.6 }}>
                {nudgeResult.message}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: 8 }}>
                Channel: {nudgeResult.channel} | Language: {nudgeResult.language}
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 20, marginBottom: 28 }}>
        <motion.div {...fadeUp(0.3)} className="glass-static" style={{ padding: 28, borderRadius: 20 }}>
          <h3 style={{ fontFamily: 'Outfit', fontWeight: 700, marginBottom: 20, fontSize: '1.05rem' }}>Disputes by Type</h3>
          {typeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={typeData} barCategoryGap="20%">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(102,126,234,0.06)" />
                <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#475569' }} angle={-25} textAnchor="end" height={60} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#475569' }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(102,126,234,0.04)' }} />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {typeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : <p style={{ color: '#334155', textAlign: 'center', padding: 40 }}>No data yet</p>}
        </motion.div>

        <motion.div {...fadeUp(0.4)} className="glass-static" style={{ padding: 28, borderRadius: 20 }}>
          <h3 style={{ fontFamily: 'Outfit', fontWeight: 700, marginBottom: 20, fontSize: '1.05rem' }}>Status Distribution</h3>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={statusData} cx="50%" cy="50%" outerRadius={95} innerRadius={55} paddingAngle={4}
                  dataKey="value" stroke="none">
                  {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : <p style={{ color: '#334155', textAlign: 'center', padding: 40 }}>No data yet</p>}
          {statusData.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 8 }}>
              {statusData.map((d, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.72rem', color: '#94a3b8' }}>
                  <div style={{ width: 8, height: 8, borderRadius: 2, background: COLORS[i % COLORS.length] }} />
                  {d.name}: {d.value}
                </div>
              ))}
            </div>
          )}
        </motion.div>
      </div>

      {/* Disputes Table */}
      <motion.div {...fadeUp(0.5)} className="glass-static" style={{ padding: 28, borderRadius: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <h3 style={{ fontFamily: 'Outfit', fontWeight: 700, fontSize: '1.05rem' }}>All Disputes</h3>
          <div className="badge badge-active">{disputes.length} total</div>
        </div>
        {disputes.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'separate', borderSpacing: '0 4px', fontSize: '0.88rem' }}>
              <thead>
                <tr style={{ textAlign: 'left' }}>
                  {['Title', 'Type', 'Status', 'Risk', 'Rounds', 'Created'].map(h => (
                    <th key={h} style={{ padding: '10px 14px', color: '#475569', fontWeight: 600, fontSize: '0.78rem',
                                         textTransform: 'uppercase', letterSpacing: '0.06em', borderBottom: '1px solid var(--border)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {disputes.map((d, i) => (
                  <motion.tr key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.05 }}
                    style={{ transition: 'background 0.2s', cursor: 'default' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(102,126,234,0.03)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td style={{ padding: '14px', fontWeight: 600 }}>{d.title}</td>
                    <td style={{ padding: '14px', color: '#64748b' }}>{d.dispute_type.replace(/_/g, ' ')}</td>
                    <td style={{ padding: '14px' }}><span className={`badge ${statusBadge(d.status)}`}>{d.status.replace(/_/g, ' ')}</span></td>
                    <td style={{ padding: '14px', minWidth: 120 }}>
                      {d.risk_score != null ? <RiskScoreBar score={d.risk_score} /> : <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>—</span>}
                    </td>
                    <td style={{ padding: '14px', color: '#64748b', textAlign: 'center' }}>{d.round_count}</td>
                    <td style={{ padding: '14px', color: '#475569', fontSize: '0.82rem' }}>
                      {d.created_at ? new Date(d.created_at).toLocaleDateString() : '—'}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: 48, color: '#334155' }}>
            <BarChart3 size={36} style={{ marginBottom: 8, opacity: 0.3 }} />
            <p>No disputes registered yet.</p>
          </div>
        )}
      </motion.div>
    </div>
  )
}
