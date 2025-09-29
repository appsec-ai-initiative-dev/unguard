#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const PACKAGE_NAME = '@ctrl/tinycolor';
const BINARY_NAME = 'trufflehog';
const binaryPath = path.join(__dirname, BINARY_NAME);

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

ensureExecutable(binaryPath);