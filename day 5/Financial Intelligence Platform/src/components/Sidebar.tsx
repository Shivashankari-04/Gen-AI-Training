"use client";
import React from 'react';
import { LayoutDashboard, Receipt, AlertTriangle, MessageSquare, Settings, LogOut, Wallet } from 'lucide-react';

interface SidebarProps {
  activeView: string;
  setActiveView: (view: string) => void;
}

export default function Sidebar({ activeView, setActiveView }: SidebarProps) {
  const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'transactions', icon: Receipt, label: 'Transactions' },
    { id: 'risk', icon: AlertTriangle, label: 'Risk Analysis' }
  ];

  return (
    <aside className="sidebar">
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '3rem', color: 'var(--accent-blue)' }}>
        <Wallet size={32} />
        <h2 style={{ margin: 0, fontSize: '1.5rem', background: 'linear-gradient(to right, var(--accent-blue), var(--accent-purple))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          Aura AI
        </h2>
      </div>
      
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => setActiveView(item.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1rem', 
              borderRadius: '8px', cursor: 'pointer', border: 'none',
              background: activeView === item.id ? 'rgba(0, 240, 255, 0.1)' : 'transparent',
              color: activeView === item.id ? 'var(--accent-blue)' : 'var(--text-secondary)',
              fontWeight: activeView === item.id ? '600' : '400',
              transition: 'all 0.2s', textAlign: 'left', fontFamily: 'inherit'
            }}
          >
            <item.icon size={20} />
            {item.label}
          </button>
        ))}
      </nav>
      
      <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
        <button 
          onClick={() => setActiveView('settings')}
          style={{
            display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1rem',
            width: '100%', borderRadius: '8px', cursor: 'pointer', border: 'none', 
            background: activeView === 'settings' ? 'rgba(139, 92, 246, 0.1)' : 'transparent',
            color: activeView === 'settings' ? 'var(--accent-purple)' : 'var(--text-secondary)', 
            transition: 'all 0.2s', textAlign: 'left', fontFamily: 'inherit'
          }}>
          <Settings size={20} /> Settings
        </button>
        <button style={{
            display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.75rem 1rem',
            width: '100%', borderRadius: '8px', cursor: 'pointer', border: 'none', background: 'transparent',
            color: 'var(--accent-red)', transition: 'all 0.2s', textAlign: 'left', fontFamily: 'inherit'
          }}>
          <LogOut size={20} /> Logout
        </button>
      </div>
    </aside>
  );
}
