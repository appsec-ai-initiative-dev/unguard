'use client';

import { useState } from 'react';
import { triggerSupplyChainExfil } from './actions';

interface ExfilResult {
  success: boolean;
  message: string;
  artifacts?: {
    envMatches: number;
    fileMatches: number;
  };
}

export default function ShaiHuludPage() {
  const [result, setResult] = useState<ExfilResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleTrigger = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await triggerSupplyChainExfil();
      setResult(res);
    } catch (error) {
      setResult({ 
        success: false, 
        message: `Error: ${error instanceof Error ? error.message : String(error)}` 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-4 text-amber-700">
        🪱 Shai-Hulud Supply Chain Attack Demo
      </h1>
      
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
        <h2 className="font-semibold text-amber-800 mb-2">About this demo</h2>
        <p className="text-sm text-amber-700 mb-2">
          This page demonstrates a supply chain attack via the compromised{' '}
          <code className="bg-amber-100 px-1 rounded">@ctrl/tinycolor</code> package.
          The malicious package harvests secrets and exfiltrates them to an attacker-controlled URL.
        </p>
        <p className="text-sm text-amber-700">
          <strong>IoC for Dynatrace:</strong> Outbound HTTP POST with secret data,
          package metadata in headers, environment/file harvesting.
        </p>
      </div>

      <div className="bg-slate-100 border border-slate-200 rounded-lg p-4 mb-6">
        <h3 className="font-medium text-slate-700 mb-2">Setup for demo</h3>
        <ul className="text-sm text-slate-600 space-y-1">
          <li>• Set env vars with <code className="bg-slate-200 px-1 rounded">SAFE_TOKEN_</code> prefix</li>
          <li>• Or create <code className="bg-slate-200 px-1 rounded">fake-secrets/</code> dir with token files</li>
          <li>• Configure <code className="bg-slate-200 px-1 rounded">CTRL_TINYCOLOR_EXFIL_URL</code> to customize target</li>
        </ul>
      </div>

      <button
        onClick={handleTrigger}
        disabled={loading}
        className="bg-amber-600 text-white px-6 py-3 rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
      >
        {loading ? 'Triggering...' : 'Trigger Supply Chain Exfiltration'}
      </button>

      {result && (
        <div className={`mt-6 p-4 rounded-lg border ${
          result.success 
            ? 'bg-green-50 border-green-200 text-green-800' 
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <h3 className="font-semibold mb-2">
            {result.success ? '✓ Exfiltration triggered' : '✗ Error'}
          </h3>
          <p className="text-sm mb-2">{result.message}</p>
          {result.artifacts && (
            <div className="text-sm">
              <p>Environment matches: {result.artifacts.envMatches}</p>
              <p>File matches: {result.artifacts.fileMatches}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
