"use client";
import React, { useState } from 'react';
import { UploadCloud, CheckCircle, Loader } from 'lucide-react';

export default function UploadFlow() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      console.error(e);
      alert("Error uploading file");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '3rem 2rem', border: '2px dashed var(--border-color)', background: 'rgba(10, 14, 23, 0.4)' }}>
      {result ? (
        <div style={{ textAlign: 'center' }}>
          <CheckCircle size={48} color="var(--accent-green)" style={{ marginBottom: '1rem' }} />
          <h3>Analysis Complete</h3>
          <p>Extracted insights and categorized {result.docs_ingested || 0} fragments into RAG.</p>
          <div style={{ marginTop: '1.5rem', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '8px', textAlign: 'left', maxHeight: '150px', overflowY: 'auto' }}>
             <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
               AI Agent analysis completed safely. Go to the <strong>Transactions</strong> or <strong>Risk Analysis</strong> tabs to view the newly compiled reports.
             </p>
          </div>
          <button className="btn btn-outline" style={{ marginTop: '1.5rem' }} onClick={() => setResult(null)}>Upload Another</button>
        </div>
      ) : uploading ? (
        <div style={{ textAlign: 'center' }}>
          <Loader size={48} className="lucide-spin" color="var(--accent-blue)" style={{ marginBottom: '1rem', animation: 'spin 2s linear infinite' }} />
          <h3>AI Agents Processing Data...</h3>
          <p>Running LangGraph workflow: Cleaning → Categorizing → Insights</p>
          <style dangerouslySetInnerHTML={{__html: `
            @keyframes spin { 100% { transform: rotate(360deg); } }
          `}} />
        </div>
      ) : (
        <>
          <div style={{ background: 'rgba(0, 240, 255, 0.1)', padding: '1rem', borderRadius: '50%', marginBottom: '1.5rem' }}>
            <UploadCloud size={32} color="var(--accent-blue)" />
          </div>
          <h3 style={{ marginBottom: '0.5rem' }}>Upload Financial Data</h3>
          <p style={{ textAlign: 'center', marginBottom: '2rem', maxWidth: '300px' }}>Upload CSV or PDF expenses for instant multi-agent analysis and categorization.</p>
          
          <input 
            type="file" 
            accept=".csv,.pdf" 
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            style={{ display: 'none' }} 
            id="file-upload" 
          />
          <label htmlFor="file-upload" className="btn btn-primary" style={{ marginBottom: '1rem', width: '100%', maxWidth: '250px' }}>
            {file ? file.name : "Select File"}
          </label>
          {file && (
            <button className="btn btn-outline" style={{ width: '100%', maxWidth: '250px' }} onClick={handleUpload}>
              Start AI Analysis
            </button>
          )}
        </>
      )}
    </div>
  );
}
