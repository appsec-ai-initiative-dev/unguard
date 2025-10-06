#!/usr/bin/env node

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');

const REGISTRY = process.env.VERDACCIO_REGISTRY || 'http://localhost:4873';
const TARGET_VERSION = process.env.VERDACCIO_TINYCOLOR_VERSION || '4.1.1';
const PACKAGE_NAME = '@ctrl/tinycolor';
const npmCommand = process.platform === 'win32' ? 'npm.cmd' : 'npm';
const REPO_ROOT = path.resolve(__dirname, '..', '..');
const SOURCE_DIR = path.join(
  REPO_ROOT,
  'src',
  'frontend-nextjs',
  'vendor',
  'ctrl-tinycolor-sim'
);

async function main() {
  await ensureExists(SOURCE_DIR, 'vendor package directory');

  const tmpDir = await fsp.mkdtemp(path.join(os.tmpdir(), 'tinycolor-seed-'));

  try {
    await fsp.cp(SOURCE_DIR, tmpDir, { recursive: true });
    const pkgPath = path.join(tmpDir, 'package.json');
    const pkg = JSON.parse(await fsp.readFile(pkgPath, 'utf8'));

    pkg.version = TARGET_VERSION;
    pkg.private = false;
    pkg.scripts = pkg.scripts || {};

    await fsp.writeFile(pkgPath, JSON.stringify(pkg, null, 2));

    const args = [
      'publish',
      '--registry',
      REGISTRY,
      '--access',
      'public',
      '--tag',
      'latest',
    ];

    try {
      await runCapture(npmCommand, args, { cwd: tmpDir });
    } catch (error) {
      if (isConflictError(error)) {
        console.warn(`[verdaccio] ${PACKAGE_NAME}@${TARGET_VERSION} already present, skipping publish`);
        return;
      }
      throw error;
    }
  } finally {
    await fsp.rm(tmpDir, { recursive: true, force: true });
  }
}

function isConflictError(error) {
  if (!error || typeof error !== 'object') {
    return false;
  }

  const haystack = [error.message, error.stderr, error.stdout]
    .filter(Boolean)
    .join('\n');

  return /E409|409 Conflict|already present/i.test(haystack);
}

async function ensureExists(targetPath, description) {
  try {
    await fsp.access(targetPath, fs.constants.F_OK);
  } catch {
    throw new Error(`Unable to locate ${description} at ${targetPath}`);
  }
}

function runCapture(command, args, options) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: process.platform === 'win32',
      ...options,
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
      process.stdout.write(chunk);
    });

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
      process.stderr.write(chunk);
    });

    child.on('exit', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        const error = new Error(`${command} ${args.join(' ')} exited with code ${code}`);
        error.code = code;
        error.stdout = stdout;
        error.stderr = stderr;
        reject(error);
      }
    });

    child.on('error', reject);
  });
}

main().catch((error) => {
  console.error('[verdaccio] failed to publish @ctrl/tinycolor seed package');
  console.error(error instanceof Error ? error.message : error);
  if (error && typeof error.stderr === 'string' && error.stderr.length > 0) {
    console.error(error.stderr);
  }
  process.exit(1);
});
