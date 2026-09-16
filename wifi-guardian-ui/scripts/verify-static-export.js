/**
 * Build contract for the packaged Electron UI.
 *
 * main.js serves `out/` at runtime. This pre-package check stops a build when
 * the static Next.js export is missing, preventing a successfully-installed
 * executable from opening an empty/blank dashboard window.
 */
const fs = require('fs');
const path = require('path');

const outputDir = path.resolve(__dirname, '..', 'out');
const entryPoint = path.join(outputDir, 'index.html');

if (!fs.existsSync(entryPoint)) {
  throw new Error(`Static dashboard export is missing: ${entryPoint}`);
}

const html = fs.readFileSync(entryPoint, 'utf8');
if (!html.includes('<html') || !html.includes('_next/')) {
  throw new Error('Static dashboard export is incomplete: index.html has no valid Next.js document/assets.');
}

const nextAssetsDir = path.join(outputDir, '_next');
if (!fs.existsSync(nextAssetsDir)) {
  throw new Error(`Static dashboard export is incomplete: ${nextAssetsDir} is missing.`);
}

console.log(`[verify:static-ui] Verified dashboard export: ${entryPoint}`);
