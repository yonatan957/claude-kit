#!/usr/bin/env node
"use strict";

/**
 * Fetches and unpacks the platform-specific PyInstaller --onedir build
 * (claude-kit.spec, research.md #8) that matches the current OS/arch, into
 * npm/dist/ so bin/claude-kit.js can exec it directly.
 *
 * The release archives themselves are built and published by CI (one per
 * platform/arch), not built here — this script only downloads and extracts
 * the one matching the current machine.
 */

const https = require("https");
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const PACKAGE_VERSION = require("./package.json").version;

function platformArchTag() {
  const platform = { darwin: "macos", linux: "linux", win32: "windows" }[process.platform];
  const arch = { x64: "x64", arm64: "arm64" }[process.arch];
  if (!platform || !arch) {
    throw new Error(`unsupported platform/arch: ${process.platform}/${process.arch}`);
  }
  return `${platform}-${arch}`;
}

function releaseArchiveUrl() {
  const tag = platformArchTag();
  const ext = process.platform === "win32" ? "zip" : "tar.gz";
  return `${process.env.CLAUDE_KIT_RELEASES_BASE_URL}/v${PACKAGE_VERSION}/claude-kit-${tag}.${ext}`;
}

function download(url, destPath) {
  return new Promise((resolve, reject) => {
    https
      .get(url, (res) => {
        if (res.statusCode !== 200) {
          reject(new Error(`download failed: HTTP ${res.statusCode} for ${url}`));
          return;
        }
        const file = fs.createWriteStream(destPath);
        res.pipe(file);
        file.on("finish", () => file.close(resolve));
      })
      .on("error", reject);
  });
}

async function main() {
  if (!process.env.CLAUDE_KIT_RELEASES_BASE_URL) {
    console.warn(
      "claude-kit: CLAUDE_KIT_RELEASES_BASE_URL is not set; skipping binary fetch. " +
        "Set it to your release host, or build locally with `pyinstaller claude-kit.spec` " +
        "and copy dist/claude-kit/ into npm/dist/."
    );
    return;
  }

  const distDir = path.join(__dirname, "dist");
  fs.mkdirSync(distDir, { recursive: true });

  const url = releaseArchiveUrl();
  const archivePath = path.join(distDir, path.basename(url));
  await download(url, archivePath);

  // `tar` on modern Windows/macOS/Linux all handle both .zip and .tar.gz.
  const tarArgs = archivePath.endsWith(".zip")
    ? ["-xf", archivePath, "-C", distDir]
    : ["-xzf", archivePath, "-C", distDir];
  execFileSync("tar", tarArgs);
  fs.unlinkSync(archivePath);

  if (process.platform !== "win32") {
    fs.chmodSync(path.join(distDir, "claude-kit"), 0o755);
  }
}

main().catch((err) => {
  console.error(`claude-kit: postinstall failed: ${err.message}`);
  process.exit(1);
});
