/**
 * Ensures NSIS upgrades/uninstalls close Guardian's hidden backend process
 * before attempting to replace or remove the installed executable resources.
 */
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const packageJson = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const includePath = packageJson.build?.nsis?.include;
if (includePath !== 'nsis/close-guardian-processes.nsh') {
  throw new Error('NSIS must include the Guardian process shutdown macro.');
}

const include = fs.readFileSync(path.join(root, includePath), 'utf8');
for (const required of [
  '!macro customInit',
  '!macro customUnInit',
  'taskkill /F /T /IM "WiFi AC Guardian.exe"',
  'taskkill /F /T /IM "guardian-backend.exe"',
]) {
  if (!include.includes(required)) {
    throw new Error(`Installer shutdown contract is missing: ${required}`);
  }
}

console.log('[verify:installer-shutdown] Verified NSIS upgrade/uninstall backend shutdown contract.');
