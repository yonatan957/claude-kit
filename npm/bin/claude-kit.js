#!/usr/bin/env node
"use strict";

/**
 * Thin exec shim (research.md #8): locates the platform PyInstaller
 * --onedir build that npm/postinstall.js fetched into npm/dist/, and execs
 * it with the developer's own argv/stdio. No logic lives here beyond
 * locating and forwarding — the real CLI is the frozen Python binary.
 */

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

function platformBinaryName() {
  return process.platform === "win32" ? "claude-kit.exe" : "claude-kit";
}

function binaryPath() {
  return path.join(__dirname, "..", "dist", platformBinaryName());
}

function main() {
  const bin = binaryPath();
  if (!fs.existsSync(bin)) {
    console.error(
      `claude-kit: platform binary not found at ${bin}. ` +
        "Try reinstalling: npm install -g claude-kit"
    );
    process.exit(1);
  }
  const result = spawnSync(bin, process.argv.slice(2), { stdio: "inherit" });
  process.exit(result.status === null ? 1 : result.status);
}

main();
