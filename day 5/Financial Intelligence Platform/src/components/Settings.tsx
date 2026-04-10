"use client";
import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, Key, Sliders, Shield } from 'lucide-react';

export default function SettingsPane() {
  const [StrictCompliance, setStrictCompliance] = useState(true);
  const [AnomaliesAlerts, setAnomaliesAlerts] = useState(true);

  // Load saved settings
  useEffect(() => {
    const strict = localStorage.getItem('strict_compliance');
    const anomalies = localStorage.getItem('anomalies_alerts');
    if (strict !== null) setStrictCompliance(strict === 'true');
    if (anomalies !== null) setAnomaliesAlerts(anomalies === 'true');
  }, []);

  const handleSave = () => {
    localStorage.setItem('strict_compliance', StrictCompliance.toString());
    localStorage.setItem('anomalies_alerts', AnomaliesAlerts.toString());
    alert('System Configurations successfully saved!');
  };

  return (
    <div className="glass-card" style={{ flex: 1 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
        <SettingsIcon size={32} color="var(--accent-purple)" />
        <div>
          <h2 style={{ margin: 0 }}>System Configuration</h2>
          <p>Manage AI behavior and security policies.</p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
        
        {/* Model Section */}
        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}><Sliders size={20} /> AI Agent Parameters</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ margin: 0 }}>Analyzer Aggressiveness</h4>
                <p style={{ margin: 0, fontSize: '0.85rem' }}>Determine how tightly the LLM restricts categories.</p>
              </div>
              <select className="input-glass" style={{ width: 'auto' }}>
                <option>Conservative</option>
                <option>Balanced</option>
                <option>Aggressive (Creative)</option>
              </select>
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4 style={{ margin: 0 }}>Default RAG Search Depth</h4>
                <p style={{ margin: 0, fontSize: '0.85rem' }}>Top K documents retrieved per Chat Assistant query.</p>
              </div>
              <input type="number" defaultValue={3} className="input-glass" style={{ width: '80px' }} />
            </div>
          </div>
        </div>

        {/* Security Section */}
        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}><Shield size={20} /> Security & Policy Policies</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            
            <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={StrictCompliance} onChange={e => setStrictCompliance(e.target.checked)} style={{ width: 20, height: 20 }} />
              <div>
                <h4 style={{ margin: 0 }}>Strict Compliance Mode</h4>
                <p style={{ margin: 0, fontSize: '0.85rem' }}>Risk Evaluator flags items over $1,000 automatically.</p>
              </div>
            </label>
            
            <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
              <input type="checkbox" checked={AnomaliesAlerts} onChange={e => setAnomaliesAlerts(e.target.checked)} style={{ width: 20, height: 20 }} />
              <div>
                <h4 style={{ margin: 0 }}>Real-Time Anomaly Delivery</h4>
                <p style={{ margin: 0, fontSize: '0.85rem' }}>Receive UI notifications immediately when RAG flags anomalies.</p>
              </div>
            </label>
            
          </div>
        </div>

        <button className="btn btn-primary" style={{ width: 'fit-content' }} onClick={handleSave}>
          <Save size={18} /> Save Configurations
        </button>

      </div>
    </div>
  );
}
