"use client";
import React, { useEffect, useState } from 'react';
import { ShieldAlert, AlertOctagon, TrendingDown } from 'lucide-react';

export default function RiskAnalysis() {
  const [risks, setRisks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    Promise.all([
      fetch('/api/risks').then(async r => {
        if (!r.ok) return { risks: [] };
        return r.json();
      }),
      fetch('/api/dashboard-stats').then(async r => {
        if (!r.ok) return null;
        return r.json();
      })
    ]).then(([riskData, statsData]) => {
      setRisks(riskData?.risks || []);
      setStats(statsData || null);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const totalRisks = risks.length;
  const highRisks = stats?.risk_levels?.High || 0;
  const mediumRisks = stats?.risk_levels?.Medium || 0;
  const compliantCount = stats?.risk_levels?.Low || 0;
  const totalProcessed = highRisks + mediumRisks + compliantCount;
  
  const complianceRate = totalProcessed > 0 
    ? Math.round((compliantCount / totalProcessed) * 100) 
    : 100;

  return (
    <div className="glass-card" style={{ flex: 1 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <ShieldAlert size={32} color="var(--accent-red)" />
        <div>
          <h2 style={{ margin: 0 }}>Compliance & Risk Policy Board</h2>
          <p>Real-time anomaly detection evaluated by the AI Risk Agent.</p>
        </div>
      </div>

      <div className="grid-cols-3" style={{ marginBottom: '2rem' }}>
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '1.5rem', borderRadius: '12px', textAlign: 'center' }}>
          <h1 style={{ color: 'var(--accent-red)', margin: 0, fontSize: '2.5rem' }}>{highRisks}</h1>
          <p style={{ color: 'var(--text-secondary)' }}>High Risk Flag</p>
        </div>
        <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', padding: '1.5rem', borderRadius: '12px', textAlign: 'center' }}>
          <h1 style={{ color: '#f59e0b', margin: 0, fontSize: '2.5rem' }}>{mediumRisks}</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Medium Risk Flags</p>
        </div>
        <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '1.5rem', borderRadius: '12px', textAlign: 'center' }}>
          <h1 style={{ color: 'var(--accent-green)', margin: 0, fontSize: '2.5rem' }}>{complianceRate}%</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Compliance Rate</p>
        </div>
      </div>

      <h3 style={{ marginBottom: '1.5rem' }}>Flagged Records</h3>
      
      {loading ? (
        <p>Analyzing risk parameters...</p>
      ) : risks.length === 0 ? (
        <p>No risks detected. Your expenses are compliant.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {risks.map(r => (
            <div key={r.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.03)', padding: '1rem 1.5rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                {r.severity === 'High' ? <AlertOctagon color="var(--accent-red)" /> : <TrendingDown color="#f59e0b" />}
                <div>
                  <h4 style={{ margin: 0, color: 'var(--text-primary)' }}>{r.title}</h4>
                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{r.category} | {r.reason}</p>
                </div>
              </div>
              <span className={`badge ${r.severity === 'High' ? 'badge-danger' : r.severity === 'Medium' ? 'badge-warning' : 'badge-success'}`}>
                {r.severity} Risk
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
