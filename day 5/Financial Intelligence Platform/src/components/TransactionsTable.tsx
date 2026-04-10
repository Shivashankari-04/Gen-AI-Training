"use client";
import React, { useEffect, useState } from 'react';
import { FileText, ArrowUpRight, ArrowDownRight } from 'lucide-react';

export default function TransactionsTable() {
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchTransactions = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/transactions');
      if (!res.ok) throw new Error("API not ready");
      const data = await res.json();
      setTransactions(data.transactions || []);
    } catch (e) {
      console.error("Failed to fetch transactions:", e);
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, []);

  return (
    <div className="glass-card" style={{ flex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}><FileText color="var(--accent-blue)" /> Transactions Ledger</h2>
          <p>Review and audit uploaded financial records natively.</p>
        </div>
        <button className="btn btn-outline" onClick={fetchTransactions}>Refresh</button>
      </div>

      <div style={{ overflowX: 'auto' }}>
        {loading ? (
          <p>Loading transactions...</p>
        ) : transactions.length === 0 ? (
          <p>No transactions found. Upload a CSV to get started.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '1rem', fontWeight: 500 }}>Date</th>
                <th style={{ padding: '1rem', fontWeight: 500 }}>Description</th>
                <th style={{ padding: '1rem', fontWeight: 500 }}>Department</th>
                <th style={{ padding: '1rem', fontWeight: 500 }}>Amount</th>
                <th style={{ padding: '1rem', fontWeight: 500 }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map(tx => (
                <tr key={tx.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s' }}>
                  <td style={{ padding: '1rem' }}>{tx.date}</td>
                  <td style={{ padding: '1rem', color: 'var(--text-primary)', fontWeight: 500 }}>{tx.desc}</td>
                  <td style={{ padding: '1rem' }}>{tx.dept}</td>
                  <td style={{ padding: '1rem', color: tx.amount > 5000 ? 'var(--accent-red)' : 'var(--text-primary)' }}>
                    ${parseFloat(tx.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td style={{ padding: '1rem' }}>
                    <span className={`badge ${tx.status === 'Approved' ? 'badge-success' : 'badge-warning'}`}>
                      {tx.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
