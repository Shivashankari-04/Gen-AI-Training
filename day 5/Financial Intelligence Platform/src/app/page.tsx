"use client";
import React, { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import UploadFlow from '@/components/UploadFlow';
import DashboardCharts from '@/components/DashboardCharts';
import ChatAssistant from '@/components/ChatAssistant';
import TransactionsTable from '@/components/TransactionsTable';
import RiskAnalysis from '@/components/RiskAnalysis';
import SettingsPane from '@/components/Settings';
import { Bell, Search } from 'lucide-react';

export default function Home() {
  const [activeView, setActiveView] = useState('dashboard');
  const [showNotifications, setShowNotifications] = useState(false);

  // Interactive Notification State
  const [notifications, setNotifications] = useState([
    { id: 1, text: 'High Risk Flag: Luxury Spa Retreat', time: '10m ago', unread: true },
    { id: 2, text: 'Analyzer categorized 13 transactions successfully.', time: '1h ago', unread: true },
    { id: 3, text: 'System update completed.', time: '2h ago', unread: false }
  ]);

  const markAsRead = (id: number) => {
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, unread: false } : n));
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, unread: false })));
  };

  const [searchQuery, setSearchQuery] = useState("");
  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      alert(`Search queries integrate natively with the RAG ChatAssistant. Head over to the Dashboard and ask the AI Advisor about "${searchQuery}"!`);
      setSearchQuery("");
    }
  };

  const renderView = () => {
    switch (activeView) {
      case 'dashboard':
        return (
          <section style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 350px', gap: '2rem', alignItems: 'stretch' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <DashboardCharts />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
              <UploadFlow />
              <ChatAssistant />
            </div>
          </section>
        );
      case 'transactions':
        return <TransactionsTable />;
      case 'risk':
        return <RiskAnalysis />;
      case 'settings':
        return <SettingsPane />;
      default:
        return <div>View not found</div>;
    }
  };

  const getPageTitle = () => {
    switch(activeView) {
      case 'dashboard': return 'Financial Intelligence Dashboard';
      case 'transactions': return 'Global Transactions Explorer';
      case 'risk': return 'Risk & Policy Evaluation';
      case 'settings': return 'Enterprise Configurations';
      default: return 'Aura Platform';
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeView={activeView} setActiveView={setActiveView} />
      <main className="main-content">
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', position: 'relative' }}>
          <div>
            <h1 style={{ fontSize: '1.875rem' }}>{getPageTitle()}</h1>
            <p className="text-secondary">{activeView === 'dashboard' ? 'Welcome back. Here is the AI analysis of your recent expenses.' : `Manage your ${activeView} natively.`}</p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
            <div style={{ position: 'relative' }}>
              <input 
                type="text" 
                placeholder="Search insights... (Press Enter)" 
                className="input-glass" 
                style={{ paddingLeft: '2.5rem', width: '250px' }} 
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                onKeyDown={handleSearchKeyDown}
              />
              <Search size={18} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            </div>
            <div style={{ position: 'relative', cursor: 'pointer', color: 'var(--text-secondary)' }} onClick={() => setShowNotifications(!showNotifications)}>
              <Bell size={24} />
              {notifications.some(n => n.unread) && (
                <div style={{ position: 'absolute', top: '-4px', right: '-4px', width: '12px', height: '12px', background: 'var(--accent-red)', borderRadius: '50%', border: '2px solid var(--bg-dark)' }} />
              )}
            </div>

            {/* Notifications Dropdown */}
            {showNotifications && (
              <div style={{
                position: 'absolute', top: '100%', right: '0', marginTop: '1rem', width: '300px',
                background: 'var(--bg-card)', border: 'var(--glass-border)', borderRadius: '12px',
                boxShadow: 'var(--glass-shadow)', zIndex: 50, backdropFilter: 'var(--glass-blur)'
              }}>
                <div style={{ padding: '1rem', borderBottom: '1px solid rgba(255,255,255,0.05)', fontWeight: 600 }}>Notifications</div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  {notifications.map(n => (
                    <div key={n.id} onClick={() => markAsRead(n.id)} style={{ padding: '1rem', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: '0.5rem', cursor: 'pointer', transition: 'background 0.2s' }} className="hover:bg-white/5">
                      {n.unread && <div style={{ width: 8, height: 8, background: 'var(--accent-blue)', borderRadius: '50%', marginTop: '6px', flexShrink: 0 }} />}
                      <div>
                        <p style={{ margin: 0, color: 'var(--text-primary)', fontSize: '0.9rem', lineHeight: 1.4, opacity: n.unread ? 1 : 0.6 }}>{n.text}</p>
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{n.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
                <div onClick={markAllAsRead} style={{ padding: '0.75rem', textAlign: 'center', fontSize: '0.85rem', color: 'var(--accent-blue)', cursor: 'pointer' }}>Mark all as read</div>
              </div>
            )}
          </div>
        </header>

        {renderView()}

      </main>
    </div>
  );
}
