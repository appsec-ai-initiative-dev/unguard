#!/usr/bin/env node

const fs = require('fs');
const fsp = fs.promises;
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');

const REGISTRY = process.env.VERDACCIO_REGISTRY || 'http://localhost:4873';
const TARGET_VERSION = process.env.VERDACCIO_TINYCOLOR_VERSION || '4.1.1';
const PACKAGE_NAME = '@ctrl/tinycolor';
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

    const versionSpecifier = `${PACKAGE_NAME}@${TARGET_VERSION}`;
    const versionExists = await checkIfPublished(versionSpecifier);

    if (versionExists) {
      console.warn(`[verdaccio] ${versionSpecifier} already present, skipping publish`);
      return;
    }

    await run(process.platform === 'win32' ? 'npm.cmd' : 'npm', [
      'publish',
      '--registry',
      REGISTRY,
      '--access',
      'public',
      '--tag',
      'latest'
    ], { cwd: tmpDir });
  } finally {
    await fsp.rm(tmpDir, { recursive: true, force: true });
  }
}

async function checkIfPublished(specifier) {
  try {
    await runCapture(process.platform === 'win32' ? 'npm.cmd' : 'npm', [
      'view',
      specifier,
      'version',
      '--registry',
      REGISTRY
    ]);
    return true;
  } catch (error) {
    if (error && typeof error.message === 'string' && error.message.includes('404')) {
      return false;
    }

    // npm view exits with code 1 when version not found but does not always include 404
    if (error && typeof error.code === 'number' && error.code === 1) {
      return false;
    }

    throw error;
  }
}

async function ensureExists(targetPath, description) {
  try {
    await fsp.access(targetPath, fs.constants.F_OK);
  } catch {
    throw new Error(`Unable to locate ${description} at ${targetPath}`);
  }
}

function run(command, args, options) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: 'inherit', shell: process.platform === 'win32', ...options });
    child.on('exit', (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`${command} ${args.join(' ')} exited with code ${code}`));
      }
    });
    child.on('error', reject);
  });
}

function runCapture(command, args, options) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: ['ignore', 'pipe', 'pipe'], shell: process.platform === 'win32', ...options });
    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });

    child.on('exit', (code) => {
      if (code === 0) {
        resolve({ stdout, stderr });
      } else {
        const error = new Error(`${command} ${args.join(' ')} exited with code ${code}\n${stderr}`);
        error.code = code;
        reject(error);
      }
    });

    child.on('error', reject);
  });
}

main().catch((error) => {
  console.error('[verdaccio] failed to publish @ctrl/tinycolor seed package');
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});

