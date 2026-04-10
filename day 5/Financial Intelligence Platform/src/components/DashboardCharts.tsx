"use client";
import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const mockTrendData = [
  { name: 'Jan', value: 4000 },
  { name: 'Feb', value: 3000 },
  { name: 'Mar', value: 2000 },
  { name: 'Apr', value: 2780 },
  { name: 'May', value: 1890 },
  { name: 'Jun', value: 2390 },
  { name: 'Jul', value: 3490 },
];

const COLORS = ['#00f0ff', '#8b5cf6', '#10b981', '#ef4444', '#f59e0b'];

export default function DashboardCharts() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    fetch('/api/dashboard-stats')
      .then(async res => {
        if (!res.ok) throw new Error("API not ready");
        return res.json();
      })
      .then(data => setStats(data))
      .catch(e => {
        console.error("Dashboard fetch error:", e);
        setStats(null); // Will stay nicely loading till server finishes booting
      });
  }, []);

  if (!stats) return <div className="glass-card">Loading dashboard insights...</div>;

  return (
    <div className="grid-cols-2">
      <div className="glass-card">
        <h3>Expense Trends</h3>
        <p style={{ marginBottom: '1.5rem', fontSize: '0.875rem' }}>6 month spending analysis</p>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <AreaChart data={mockTrendData}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--accent-blue)" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="var(--accent-blue)" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-secondary)" axisLine={false} tickLine={false} />
              <YAxis stroke="var(--text-secondary)" axisLine={false} tickLine={false} />
              <Tooltip 
                contentStyle={{ backgroundColor: 'var(--bg-card)', border: 'var(--glass-border)', borderRadius: '8px' }}
                itemStyle={{ color: 'var(--text-primary)' }}
              />
              <Area type="monotone" dataKey="value" stroke="var(--accent-blue)" strokeWidth={3} fillOpacity={1} fill="url(#colorValue)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card">
        <h3>Category Segmentation</h3>
        <p style={{ marginBottom: '1.5rem', fontSize: '0.875rem' }}>Automated categorization by AI</p>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={stats.top_categories}
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {stats.top_categories.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ backgroundColor: 'var(--bg-card)', border: 'var(--glass-border)', borderRadius: '8px' }}
                itemStyle={{ color: 'var(--text-primary)' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', justifyContent: 'center', marginTop: '1rem' }}>
          {stats.top_categories.map((cat: any, i: number) => (
            <div key={cat.name} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: COLORS[i % COLORS.length] }} />
              {cat.name}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
