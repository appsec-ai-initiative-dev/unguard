'use client';

import { useState } from 'react';
import { testAction } from './actions';

interface ActionResult {
  success: boolean;
  message: string;
}

export default function RcePage() {
  const [result, setResult] = useState<ActionResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (formData: FormData) => {
    setLoading(true);
    setResult(null);
    try {
      const res = await testAction(formData);
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
      <h1 className="text-2xl font-bold mb-4 text-red-700">
        ⚠️ React2Shell (CVE-2025-55182) Demo
      </h1>
      
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <h2 className="font-semibold text-red-800 mb-2">About this vulnerability</h2>
        <p className="text-sm text-red-700 mb-2">
          This page demonstrates CVE-2025-55182 - a Remote Code Execution vulnerability
          in React Server Actions. Malicious payloads exploit argument deserialization
          to execute arbitrary code on the server.
        </p>
        <p className="text-sm text-red-700">
          <strong>IoC for Dynatrace:</strong> Node process spawning child processes
          (curl, wget), outbound HTTP POST with exfiltrated data, environment harvesting.
        </p>
      </div>

      <div className="bg-slate-100 border border-slate-200 rounded-lg p-4 mb-6">
        <h3 className="font-medium text-slate-700 mb-2">What happens when triggered</h3>
        <ul className="text-sm text-slate-600 space-y-1">
          <li>• Node spawns <code className="bg-slate-200 px-1 rounded">curl</code> and <code className="bg-slate-200 px-1 rounded">wget</code> child processes</li>
          <li>• Environment variables with TOKEN/SECRET/KEY/PASSWORD are harvested</li>
          <li>• Data is exfiltrated via HTTP POST to webhook endpoint</li>
          <li>• Configure <code className="bg-slate-200 px-1 rounded">REACT2SHELL_EXFIL_URL</code> to customize target</li>
        </ul>
      </div>

      <form action={handleSubmit}>
        <button 
          type="submit"
          disabled={loading}
          className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {loading ? 'Triggering...' : 'Trigger React2Shell Attack'}
        </button>
      </form>

      {result && (
        <div className={`mt-6 p-4 rounded-lg border ${
          result.success 
            ? 'bg-green-50 border-green-200 text-green-800' 
            : 'bg-red-50 border-red-200 text-red-800'
        }`}>
          <h3 className="font-semibold mb-2">
            {result.success ? '✓ Attack simulated' : '✗ Error'}
          </h3>
          <p className="text-sm">{result.message}</p>
        </div>
      )}
    </div>
  );
}
