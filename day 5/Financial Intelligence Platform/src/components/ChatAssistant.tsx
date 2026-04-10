"use client";
import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles } from 'lucide-react';

export default function ChatAssistant() {
  const [messages, setMessages] = useState<{role: 'user' | 'assistant', content: string}[]>([
    { role: 'assistant', content: 'Hello! I am Aura, your Financial Intelligence Assistant. I am connected to your RAG pipeline. How can I help you analyze your data today?' }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    
    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg }),
      });
      const data = await res.json();
      
      setMessages(prev => [...prev, { role: 'assistant', content: data.response || "No response generated." }]);
    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, { role: 'assistant', content: "Error connecting to AI backend." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', height: '400px', flex: 1 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <Sparkles size={24} color="var(--accent-purple)" />
        <h3 style={{ margin: 0 }}>Strategic AI Advisor</h3>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem', paddingRight: '0.5rem', marginBottom: '1rem' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ 
            display: 'flex', gap: '1rem', 
            alignItems: 'flex-start',
            flexDirection: msg.role === 'user' ? 'row-reverse' : 'row'
          }}>
            <div style={{ 
              width: 32, height: 32, borderRadius: '50%', flexShrink: 0,
              background: msg.role === 'user' ? 'var(--accent-blue)' : 'rgba(139, 92, 246, 0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: msg.role === 'user' ? 'var(--bg-dark)' : 'var(--accent-purple)'
            }}>
              {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
            </div>
            <div style={{
              background: msg.role === 'user' ? 'rgba(0, 240, 255, 0.1)' : 'rgba(255, 255, 255, 0.05)',
              padding: '0.75rem 1rem', borderRadius: '12px',
              borderBottomRightRadius: msg.role === 'user' ? 0 : '12px',
              borderBottomLeftRadius: msg.role === 'assistant' ? 0 : '12px',
              maxWidth: '80%', fontSize: '0.9rem', color: 'var(--text-primary)', border: '1px solid var(--border-color)'
            }}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
            <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(139, 92, 246, 0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-purple)' }}>
              <Bot size={16} />
            </div>
            <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '0.75rem 1rem', borderRadius: '12px', borderBottomLeftRadius: 0, fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
              Thinking...
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      
      <div style={{ display: 'flex', gap: '0.5rem', marginTop: 'auto' }}>
        <input 
          type="text" 
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask about spending trends, risks, or compliance..."
          className="input-glass"
        />
        <button className="btn btn-primary" onClick={handleSend} disabled={loading} style={{ padding: '0.75rem' }}>
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}
